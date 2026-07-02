import sys
import os
import shutil
import subprocess
import threading
import uuid
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Make sibling and .engine modules importable
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / ".engine"))

# Standard directories
UPLOAD_DIR = BASE_DIR / "uploads"
SANITIZED_DIR = BASE_DIR / "sanitized"
OUTPUT_DIR = BASE_DIR / "output"
QUARANTINE_DIR = BASE_DIR / "quarantine"
REVIEW_DIR = BASE_DIR / "review"

for d in (UPLOAD_DIR, SANITIZED_DIR, OUTPUT_DIR, QUARANTINE_DIR, REVIEW_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Try imports
try:
    from combined_scanner import CombinedScanner
    from pipeline_integration import malware_gate
    from deep_analyzer import deep_analyze
except ImportError as e:
    logging.error(f"Failed to import security modules: {e}")
    CombinedScanner = None

app = FastAPI(title="Sentinel AI Local Dashboard")

# Global tasks status mapping
# task_id -> task_details
TASKS: Dict[str, dict] = {}

class ProcessRequest(BaseModel):
    file_path: str
    dry_run: bool = False
    no_vision: bool = False

def run_pipeline_subprocess(task_id: str, file_path: str, dry_run: bool, no_vision: bool):
    task = TASKS[task_id]
    
    # 1. Run Security Gate
    task["status"] = "scanning"
    task["stage"] = "security_gate"
    task["progress"] = 10
    task["logs"].append("[+] Initiating YARA security scan...")
    
    try:
        rules_path = BASE_DIR / ".engine" / "rules"
        scanner = CombinedScanner(
            rules_dir=rules_path,
            quarantine_dir=QUARANTINE_DIR,
            review_dir=REVIEW_DIR,
            sanitized_dir=SANITIZED_DIR,
            require_clamav=False,
            move_files=False  # Do not move uploaded file during scan to preserve path
        )
        scan_result = scanner.scan(file_path)
        task["scan_result"] = scan_result
        task["verdict"] = scan_result["final_verdict"]
        task["logs"].append(f"[+] Security Scan complete. Verdict: {scan_result['final_verdict']}")
        
        # If malicious, block immediately
        if scan_result["final_verdict"] == "MALICIOUS":
            task["status"] = "failed"
            task["progress"] = 100
            task["logs"].append("[-] BLOCKED: File was flagged as MALICIOUS. Aborting pipeline.")
            return
            
        # If sanitized, update the file_path to the sanitized one
        if scan_result["final_verdict"] == "CLEAN_SANITIZED" and scan_result.get("deep_analysis", {}).get("sanitized_path"):
            file_path = scan_result["deep_analysis"]["sanitized_path"]
            task["logs"].append(f"[+] Sanitized version of file will be used: {file_path}")
            
    except Exception as e:
        task["logs"].append(f"[!] Security scan error: {e}. Attempting to proceed with warning...")
        task["verdict"] = "ERROR"

    # 2. Run Main Document Standardization Pipeline
    task["status"] = "processing"
    task["progress"] = 20
    task["stage"] = "table_extraction"
    task["logs"].append("[+] Launching document standardization pipeline...")
    
    # Prepare output path
    output_filename = Path(file_path).with_suffix(".json").name
    output_path = OUTPUT_DIR / output_filename
    
    # Construct subprocess command
    cmd = [
        sys.executable,
        "-m", "src.pipeline",
        "--input", file_path,
        "--output", str(output_path)
    ]
    if dry_run:
        cmd.append("--dry-run")
        cmd.append("--no-vision")  # Bypasses VLM download and GPU requirements for dry run
    elif no_vision:
        cmd.append("--no-vision")
        
    task["logs"].append(f"[+] Executing: {' '.join(cmd)}")
    
    start_time = datetime.now()
    
    try:
        # Run subprocess and stream stdout
        # The working directory is set to .engine/ since src/ is inside it
        process = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR / ".engine"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Monitor stdout and update task state
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            clean_line = line.strip()
            if not clean_line:
                continue
                
            task["logs"].append(clean_line)
            
            # Map stdout keywords to stepper progress
            if "[Route 1] Extracting tables" in clean_line:
                task["stage"] = "table_extraction"
                task["progress"] = 30
            elif "[Route 1] Rendering cleaned pages" in clean_line:
                task["stage"] = "page_cleaning"
                task["progress"] = 50
            elif "[Route 2] Extracting document" in clean_line:
                task["stage"] = "vlm_analysis"
                task["progress"] = 70
            elif "[Stage 3] Structuring" in clean_line:
                task["stage"] = "llm_structuring"
                task["progress"] = 90
            elif "[Output] Saving results" in clean_line:
                task["progress"] = 95
                
        process.wait()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        task["elapsed"] = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        
        if process.returncode != 0:
            task["status"] = "failed"
            task["logs"].append(f"[-] Subprocess failed with return code {process.returncode}")
            return
            
        # Try loading output JSON
        if dry_run:
            if output_path.exists():
                text_content = output_path.read_text(encoding="utf-8")
                task["output"] = {
                    "document_id": task_id[:8].upper(),
                    "status": "DRY_RUN_COMPLETED",
                    "text_preview": text_content[:5000],
                    "raw_markdown": text_content
                }
                task["status"] = "completed"
                task["progress"] = 100
                task["logs"].append("[+] Dry run complete. Saved raw extraction markdown.")
            else:
                task["status"] = "failed"
                task["logs"].append("[-] Error: Output markdown not found.")
        else:
            if output_path.exists():
                try:
                    with open(output_path, "r", encoding="utf-8") as f:
                        extracted_json = json.load(f)
                    task["output"] = extracted_json
                    task["status"] = "completed"
                    task["progress"] = 100
                    task["logs"].append("[+] Pipeline completed successfully. Output JSON loaded.")
                except Exception as e:
                    task["status"] = "failed"
                    task["logs"].append(f"[-] Failed to load output JSON: {e}")
            else:
                task["status"] = "failed"
                task["logs"].append("[-] Error: Output JSON file was not generated.")
                
    except Exception as e:
        task["status"] = "failed"
        task["logs"].append(f"[!] Pipeline runtime error: {e}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan-and-process")
async def scan_and_process(req: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "id": task_id,
        "filename": Path(req.file_path).name,
        "status": "pending",
        "progress": 0,
        "stage": "security_gate",
        "logs": [],
        "verdict": "UNKNOWN",
        "scan_result": None,
        "output": None,
        "elapsed": "0s"
    }
    
    background_tasks.add_task(
        run_pipeline_subprocess,
        task_id=task_id,
        file_path=req.file_path,
        dry_run=req.dry_run,
        no_vision=req.no_vision
    )
    
    return {"task_id": task_id}

@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]

@app.get("/api/history")
async def get_history():
    history_items = []
    # Read files from OUTPUT_DIR
    for file_path in OUTPUT_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("_meta", {})
            history_items.append({
                "filename": meta.get("source_file", file_path.name.replace(".json", ".pdf")),
                "timestamp": meta.get("extraction_timestamp", datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()),
                "status": "completed",
                "verdict": "CLEAN",
                "output_file": file_path.name,
                "tables_extracted": meta.get("tables_extracted", 0),
                "images_extracted": meta.get("images_extracted", 0)
            })
        except Exception:
            pass
            
    # Also add current tasks that are running/completed/failed
    for task in TASKS.values():
        if task["status"] == "completed" and any(h["filename"] == task["filename"] for h in history_items):
            continue
        history_items.append({
            "filename": task["filename"],
            "timestamp": datetime.now().isoformat(),
            "status": task["status"],
            "verdict": task.get("verdict", "UNKNOWN"),
            "task_id": task["id"],
            "tables_extracted": task["output"].get("_meta", {}).get("tables_extracted", 0) if task["output"] else 0,
            "images_extracted": task["output"].get("_meta", {}).get("images_extracted", 0) if task["output"] else 0
        })
        
    return sorted(history_items, key=lambda x: x["timestamp"], reverse=True)

@app.get("/api/history/load")
async def load_historical_item(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() and not filename.endswith(".json"):
        file_path = OUTPUT_DIR / f"{filename}.json"
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Historical report not found")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "status": "completed",
            "filename": filename.replace(".json", ""),
            "output": data,
            "verdict": "CLEAN"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-status")
async def get_system_status():
    import psutil
    
    # Disk usage
    disk = shutil.disk_usage(str(BASE_DIR))
    
    # Check GPU VRAM
    gpu_available = False
    gpu_name = "N/A"
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
        elif torch.backends.mps.is_available():
            gpu_available = True
            gpu_name = "Apple Silicon MPS"
    except Exception:
        pass
        
    # Check scanner modules
    yara_installed = False
    try:
        import yara
        yara_installed = True
    except ImportError:
        pass

    clamav_installed = shutil.which("clamscan") is not None
    ghostscript_installed = shutil.which("gs") is not None
    
    return {
        "cpu_usage": psutil.cpu_percent(),
        "ram_usage": psutil.virtual_memory().percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "yara_scanner": "Active" if yara_installed else "Inactive",
        "clamav_scanner": "Active" if clamav_installed else "Inactive (YARA Fallback)",
        "ghostscript": "Active" if ghostscript_installed else "Inactive (PDF Sanitization Disabled)",
        "python_version": sys.version.split(" ")[0]
    }

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
