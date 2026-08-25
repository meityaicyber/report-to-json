#!/usr/bin/env python3
"""
gui_app.py
==========
Tkinter GUI for the Qwen 3.6 VL Report-to-JSON document standardization pipeline.

Features
--------
- Visual-Language Model (Qwen 3.6 VL) 2-pass unified extraction
- Direct Vision-to-JSON and fast layout parser modes
- Multi-stage processing with animated progress bar and live log
- Dark, modern VS Code-inspired UI
- JSON viewer with syntax highlighting and artifact inspection
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import re
import os
import datetime
import time
from pathlib import Path
import sys

# Ensure vlm_repo/src and repo root are in python path
SRC_DIR = Path(__file__).resolve().parent / "vlm_repo" / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from image_offloader import ImageOffloader
from lossless_transcriber import LosslessTranscriber
from schema_structurer import SchemaStructurer

try:
    from unified_vlm_engine import UnifiedVLMEngine
except ImportError:
    UnifiedVLMEngine = None

try:
    from vl_extractor import VLExtractor
except ImportError:
    VLExtractor = None

try:
    from pipeline_integration import malware_gate, MalwareDetectedError
except ImportError:
    malware_gate = None
    MalwareDetectedError = Exception

# ─────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────
BG_DARK      = "#0f1117"
BG_CARD      = "#1a1d27"
BG_PANEL     = "#141720"
ACCENT       = "#7c6af7"
ACCENT2      = "#56cfb2"
TEXT_PRIMARY = "#e8e9f0"
TEXT_MUTED   = "#6b7280"
TEXT_SUCCESS = "#4ade80"
TEXT_ERROR   = "#f87171"
TEXT_WARN    = "#fbbf24"
BORDER       = "#252836"
BAR_BG       = "#252836"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUB   = ("Segoe UI", 11)
FONT_BODY  = ("Segoe UI", 10)
FONT_MONO  = ("Consolas", 9)
FONT_LABEL = ("Segoe UI", 9, "bold")
FONT_STEP  = ("Segoe UI", 9)

# ─────────────────────────────────────────────
# Pipeline stages  (label, pct-threshold)
# ─────────────────────────────────────────────
STAGES = [
    ("Security Pre-Gate",        10),
    ("Offloading Images",        25),
    ("Qwen 3.6 VL Vision Pass",  65),
    ("Schema Structuring",       85),
    ("Saving Artifacts",         95),
    ("Done",                    100),
]

DEFAULT_VLM_MODEL = os.environ.get("VLM_MODEL", "Qwen/Qwen3.6-VL")


# ─────────────────────────────────────────────
# Extraction helpers
# ─────────────────────────────────────────────

def extract_text_pdfplumber(pdf_path: str):
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber not installed.\nRun: pip install pdfplumber")

    full_text, tables = [], []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            full_text.append(f"--- Page {page_num} ---\n{text}")
            for tbl in page.extract_tables():
                if tbl:
                    tables.append({"page": page_num, "data": tbl})

    return "\n\n".join(full_text), tables


def detect_doc_type(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["vulnerability", "cve", "vapt", "penetration test", "pentest"]):
        return "vapt_report"
    if any(k in t for k in ["audit", "compliance", "finding", "observation", "risk rating"]):
        return "audit_report"
    return "general_report"


# ─────────────────────────────────────────────
# Pipeline (runs in background thread)
# ─────────────────────────────────────────────

def run_pipeline(
    pdf_path: str,
    output_dir: str,
    engine_mode: str,
    vlm_model: str,
    load_in_4bit: bool,
    schema_path: str,
    progress_cb,
    log_cb,
    done_cb,
    error_cb
):
    try:
        def step(idx):
            label, pct = STAGES[idx]
            progress_cb(pct, label)

        # 0 - Security Pre-Gate
        step(0)
        log_cb(f"Document: {pdf_path}")
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")
        size_mb = os.path.getsize(pdf_path) / 1_048_576
        log_cb(f"  File size: {size_mb:.2f} MB")

        if malware_gate:
            try:
                log_cb("  Running security pre-gate scan...")
                gate_res = malware_gate(pdf_path)
                log_cb(f"  Security verdict: {gate_res.get('verdict', 'CLEAN')}")
            except MalwareDetectedError as mde:
                raise RuntimeError(f"Security Alert: Blocked by malware pre-gate: {mde}")
        time.sleep(0.1)

        stem = Path(pdf_path).stem
        os.makedirs(output_dir, exist_ok=True)
        img_storage_dir = os.path.join(output_dir, f"images_{stem}")
        intermediate_md_path = os.path.join(output_dir, f"{stem}_intermediate.md")
        out_json_path = os.path.join(output_dir, f"{stem}.json")

        # 1 - Stage 1: Offloading images
        step(1)
        log_cb(f"[Stage 1] Offloading embedded images & figures to deep storage...")
        offloader = ImageOffloader()
        if pdf_path.lower().endswith(".pdf"):
            image_map = offloader.extract_from_pdf(pdf_path, img_storage_dir)
        else:
            docx_images = offloader.extract_from_docx(pdf_path, img_storage_dir)
            image_map = {0: docx_images}
        img_count = sum(len(v) for v in image_map.values()) if isinstance(image_map, dict) else len(image_map)
        log_cb(f"  Offloaded {img_count} image(s) to: {img_storage_dir}")
        time.sleep(0.1)

        result = {}

        if engine_mode == "vlm_direct" and VLExtractor is not None:
            # Direct single-pass vision extraction
            step(2)
            log_cb(f"[Direct VLM] Extracting schema directly from page images via {vlm_model}...")
            extractor = VLExtractor(
                model_id=vlm_model,
                schema_path=schema_path,
                load_in_4bit=load_in_4bit
            )
            result = extractor.extract_from_pdf(pdf_path)
            step(4)
            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            step(5)
            log_cb(f"Direct VLM extraction complete. Saved to: {out_json_path}")
            done_cb(out_json_path, result, None, img_storage_dir)
            return

        elif engine_mode == "python_fallback":
            # Fast python layout parser mode
            step(2)
            log_cb("[Stage 2] Parsing document layout & tables to Markdown via pdfplumber...")
            transcriber = LosslessTranscriber()
            if pdf_path.lower().endswith(".pdf"):
                trans_res = transcriber.transcribe_pdf(pdf_path, image_map=image_map, output_md_path=intermediate_md_path)
            else:
                trans_res = transcriber.transcribe_docx(pdf_path, image_list=image_map.get(0, []), output_md_path=intermediate_md_path)
            md_text = trans_res.get("markdown_content", "")
            log_cb(f"  Generated transcript: {len(md_text):,} chars")

            step(3)
            log_cb("[Stage 3] Structuring markdown via deterministic schema structurer...")
            structurer = SchemaStructurer(schema_path=schema_path, backend="rule_based")
            result = structurer.structure_transcript(
                markdown_text=md_text,
                output_json_path=out_json_path,
                source_file_name=Path(pdf_path).name
            )

        else:
            # Default: Qwen 3.6 VL Unified 2-Pass Vision Engine
            step(2)
            log_cb(f"[Pass 1/2] Executing Qwen 3.6 VL Multimodal Visual Transcription ({vlm_model})...")
            unified_engine = UnifiedVLMEngine(
                model_id=vlm_model,
                schema_path=schema_path,
                load_in_4bit=load_in_4bit
            )
            md_text = unified_engine.pass1_visual_transcribe(
                pdf_path=pdf_path,
                image_map=image_map,
                output_md_path=intermediate_md_path
            )
            log_cb(f"  ✓ Pass 1 completed. Transcript ({len(md_text):,} chars) saved: {intermediate_md_path}")

            step(3)
            log_cb(f"[Pass 2/2] Executing Qwen 3.6 VL Schema Structuring...")
            result = unified_engine.pass2_structure_json(
                markdown_text=md_text,
                output_json_path=out_json_path,
                source_file_name=Path(pdf_path).name
            )
            log_cb(f"  ✓ Pass 2 completed. Findings extracted: {len(result.get('detailed_observations', []))}")

        # 4 - Saving
        step(4)
        log_cb(f"Artifacts ready:")
        log_cb(f"  JSON: {out_json_path}")
        if os.path.exists(intermediate_md_path):
            log_cb(f"  Markdown: {intermediate_md_path}")
        log_cb(f"  Images: {img_storage_dir}")
        time.sleep(0.1)

        # 5 - Done
        step(5)
        log_cb("Pipeline processing finished successfully.")
        done_cb(out_json_path, result, intermediate_md_path, img_storage_dir)

    except Exception as exc:
        import traceback
        error_cb(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")


# ─────────────────────────────────────────────
# Animated progress bar
# ─────────────────────────────────────────────

class AnimatedBar(tk.Canvas):
    """Gradient progress bar that resizes with its container."""

    def __init__(self, parent, bar_height=24, **kwargs):
        self._h = bar_height
        super().__init__(parent, height=self._h,
                         bg=BG_PANEL, highlightthickness=0, **kwargs)
        self._target  = 0.0
        self._current = 0.0
        self._anim    = False
        self.bind("<Configure>", lambda e: self._draw(self._current))

    def _draw(self, pct):
        self.delete("all")
        w = self.winfo_width()
        h = self._h
        if w <= 1:
            return

        self.create_rectangle(0, 0, w, h, fill=BAR_BG, outline="", width=0)

        fill_w = max(0, int(w * pct / 100))
        if fill_w > 0:
            for i in range(fill_w):
                t = i / max(fill_w - 1, 1)
                r = int(0x56 + t * (0x7c - 0x56))
                g = int(0xcf + t * (0x6a - 0xcf))
                b = int(0xb2 + t * (0xf7 - 0xb2))
                self.create_line(i, 0, i, h, fill=f"#{r:02x}{g:02x}{b:02x}")

            cx = min(fill_w + 8, w)
            self.create_oval(fill_w - 8, 1, cx, h - 1, fill=ACCENT, outline="")

        self.create_text(w // 2, h // 2,
                         text=f"{pct:.0f}%",
                         fill=TEXT_PRIMARY,
                         font=("Segoe UI", 8, "bold"),
                         anchor="center")

    def set_value(self, pct):
        self._target = max(0.0, min(100.0, pct))
        if not self._anim:
            self._tick()

    def _tick(self):
        self._anim = True
        diff = self._target - self._current
        if abs(diff) < 0.4:
            self._current = self._target
            self._draw(self._current)
            self._anim = False
            return
        self._current += diff * 0.18
        self._draw(self._current)
        self.after(16, self._tick)


# ─────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Report-to-JSON | Qwen 3.6 VL Document Pipeline")
        self.configure(bg=BG_DARK)
        self.geometry("1140x880")
        self.minsize(940, 720)

        self._pdf_path       = tk.StringVar()
        self._output_dir     = tk.StringVar(
            value=str(Path.home() / "Documents" / "report-json-output"))
        self._engine_mode    = tk.StringVar(value="vlm_unified")
        self._vlm_model      = tk.StringVar(value=DEFAULT_VLM_MODEL)
        self._load_in_4bit   = tk.BooleanVar(value=True)

        _default_schema = Path(__file__).resolve().parent / "vlm_repo" / "master_schema.json"
        self._schema_path    = tk.StringVar(
            value=str(_default_schema) if _default_schema.exists() else "")

        self._processing     = False
        self._output_path    = None

        self._build()
        self._pulse()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_CARD, height=66)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        self._title_lbl = tk.Label(hdr, text="Report-to-JSON Engine",
                                   font=FONT_TITLE, bg=BG_CARD, fg=TEXT_PRIMARY)
        self._title_lbl.pack(side="left", padx=(18, 4))
        tk.Label(hdr, text="  Powered by Qwen 3.6 VL (Multimodal Document Intelligence)",
                 font=FONT_SUB, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")

        # Body
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG_DARK, width=430)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG_PANEL)
        right.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, p):
        # ── Upload card
        uc = self._card(p, "1. Input Document (PDF / DOCX)")
        uc.pack(fill="x", pady=(0, 10))

        drop = tk.Frame(uc, bg="#1e2130",
                        highlightthickness=2, highlightbackground=BORDER)
        drop.pack(fill="x", padx=12, pady=(0, 8))
        self._drop_lbl = tk.Label(
            drop, text="Click to Select Audit Report PDF",
            font=("Segoe UI", 11), bg="#1e2130", fg=TEXT_MUTED,
            pady=18, cursor="hand2")
        self._drop_lbl.pack(fill="x")
        self._drop_lbl.bind("<Button-1>", lambda e: self._browse_pdf())
        drop.bind("<Button-1>", lambda e: self._browse_pdf())

        self._file_lbl = tk.Label(uc, text="No file selected",
                                  font=FONT_MONO, bg=BG_CARD, fg=TEXT_MUTED,
                                  wraplength=390, justify="left")
        self._file_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # ── Engine Mode card
        ec = self._card(p, "2. Processing Engine (Qwen 3.6 VL)")
        ec.pack(fill="x", pady=(0, 10))

        modes = [
            ("Qwen 3.6 VL Unified (2-Pass Vision + JSON)", "vlm_unified"),
            ("Qwen 3.6 VL Direct Vision-to-JSON", "vlm_direct"),
            ("Fast Python Layout Parsers (pdfplumber)", "python_fallback")
        ]
        for text, val in modes:
            tk.Radiobutton(
                ec, text=text, value=val, variable=self._engine_mode,
                bg=BG_CARD, fg=TEXT_PRIMARY, selectcolor=BG_DARK,
                activebackground=BG_CARD, activeforeground=ACCENT,
                font=FONT_BODY
            ).pack(anchor="w", padx=12, pady=2)

        frow = tk.Frame(ec, bg=BG_CARD)
        frow.pack(fill="x", padx=12, pady=(6, 8))
        tk.Label(frow, text="Model:", font=FONT_BODY, bg=BG_CARD, fg=TEXT_MUTED, width=6, anchor="w").pack(side="left")
        tk.Entry(frow, textvariable=self._vlm_model,
                 bg="#1e2130", fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                 relief="flat", font=FONT_MONO, bd=4).pack(side="left", fill="x", expand=True)

        tk.Checkbutton(
            ec, text="4-bit NF4 Quantization (Optimized for 8GB GPU VRAM)",
            variable=self._load_in_4bit,
            bg=BG_CARD, fg=TEXT_PRIMARY, selectcolor=BG_DARK,
            activebackground=BG_CARD, activeforeground=ACCENT,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # ── Output dir card
        oc = self._card(p, "3. Output Directory & Schema")
        oc.pack(fill="x", pady=(0, 10))
        row = tk.Frame(oc, bg=BG_CARD)
        row.pack(fill="x", padx=12, pady=(0, 6))
        tk.Entry(row, textvariable=self._output_dir,
                 bg="#1e2130", fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                 relief="flat", font=FONT_MONO, bd=4
                 ).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="…", command=self._browse_output,
                  bg=ACCENT, fg="white", font=FONT_LABEL,
                  relief="flat", bd=0, padx=10, cursor="hand2"
                  ).pack(side="left", padx=(6, 0))

        srow = tk.Frame(oc, bg=BG_CARD)
        srow.pack(fill="x", padx=12, pady=(0, 8))
        tk.Entry(srow, textvariable=self._schema_path,
                 bg="#1e2130", fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                 relief="flat", font=FONT_MONO, bd=4
                 ).pack(side="left", fill="x", expand=True)
        tk.Button(srow, text="Schema…", command=self._browse_schema,
                  bg=BORDER, fg=TEXT_PRIMARY, font=("Segoe UI", 8),
                  relief="flat", bd=0, padx=8, cursor="hand2"
                  ).pack(side="left", padx=(6, 0))

        # ── Run button
        self._run_btn = tk.Button(
            p, text="Process Document with Qwen 3.6 VL",
            command=self._start,
            bg=ACCENT, fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat", bd=0, pady=12,
            cursor="hand2", activebackground="#5e52c4")
        self._run_btn.pack(fill="x", pady=(4, 0))

        self._open_btn = tk.Button(
            p, text="Open Standardized JSON",
            command=self._open_output,
            bg=BORDER, fg=TEXT_MUTED,
            font=FONT_BODY, relief="flat", bd=0,
            pady=7, cursor="hand2", state="disabled")
        self._open_btn.pack(fill="x", pady=(6, 0))

        self._open_md_btn = tk.Button(
            p, text="Open Intermediate Markdown Transcript",
            command=self._open_md,
            bg=BORDER, fg=TEXT_MUTED,
            font=FONT_BODY, relief="flat", bd=0,
            pady=7, cursor="hand2", state="disabled")
        self._open_md_btn.pack(fill="x", pady=(4, 0))

        self._open_img_btn = tk.Button(
            p, text="Open Offloaded Figures & Diagrams",
            command=self._open_images,
            bg=BORDER, fg=TEXT_MUTED,
            font=FONT_BODY, relief="flat", bd=0,
            pady=7, cursor="hand2", state="disabled")
        self._open_img_btn.pack(fill="x", pady=(4, 0))

    def _build_right(self, p):
        # ── Progress bar
        pg = tk.Frame(p, bg=BG_PANEL)
        pg.pack(fill="x", padx=14, pady=(14, 4))

        top_row = tk.Frame(pg, bg=BG_PANEL)
        top_row.pack(fill="x", pady=(0, 4))
        tk.Label(top_row, text="Execution Status", font=FONT_LABEL,
                 bg=BG_PANEL, fg=TEXT_MUTED).pack(side="left")
        self._stage_lbl = tk.Label(top_row, text="Ready",
                                   font=FONT_STEP, bg=BG_PANEL, fg=TEXT_MUTED)
        self._stage_lbl.pack(side="right")

        self._bar = AnimatedBar(pg, bar_height=24)
        self._bar.pack(fill="x")

        # ── Stage pills
        pills = tk.Frame(p, bg=BG_PANEL)
        pills.pack(fill="x", padx=14, pady=(6, 8))
        self._step_lbls = []
        cols = 6
        for idx, (label, _) in enumerate(STAGES):
            cell = tk.Frame(pills, bg=BG_PANEL)
            cell.grid(row=idx // cols, column=idx % cols,
                      sticky="w", padx=3, pady=2)
            lbl = tk.Label(cell, text=label,
                           font=("Segoe UI", 8), bg=BG_PANEL, fg=TEXT_MUTED)
            lbl.pack(side="left")
            self._step_lbls.append(lbl)

        # ── Log
        lhdr = tk.Frame(p, bg=BG_PANEL)
        lhdr.pack(fill="x", padx=14)
        tk.Label(lhdr, text="Processing & VLM Log", font=FONT_LABEL,
                 bg=BG_PANEL, fg=TEXT_MUTED).pack(side="left")
        tk.Button(lhdr, text="Clear Log", command=self._clear_log,
                  bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8),
                  relief="flat", bd=0, cursor="hand2").pack(side="right")

        log_frame = tk.Frame(p, bg=BG_DARK)
        log_frame.pack(fill="both", expand=True, padx=14, pady=(2, 8))
        self._log = tk.Text(log_frame, bg=BG_DARK, fg=TEXT_PRIMARY,
                            font=FONT_MONO, relief="flat", bd=0,
                            state="disabled", wrap="word")
        ls = ttk.Scrollbar(log_frame, command=self._log.yview)
        self._log.configure(yscrollcommand=ls.set)
        ls.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True, padx=6, pady=6)
        self._log.tag_configure("success", foreground=TEXT_SUCCESS)
        self._log.tag_configure("error",   foreground=TEXT_ERROR)
        self._log.tag_configure("warn",    foreground=TEXT_WARN)
        self._log.tag_configure("accent",  foreground=ACCENT)

        # ── JSON viewer
        jhdr = tk.Frame(p, bg=BG_PANEL)
        jhdr.pack(fill="x", padx=14)
        tk.Label(jhdr, text="Master Schema JSON Output Preview", font=FONT_LABEL,
                 bg=BG_PANEL, fg=TEXT_MUTED).pack(side="left")
        tk.Button(jhdr, text="Copy Output JSON", command=self._copy_json,
                  bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8),
                  relief="flat", bd=0, cursor="hand2").pack(side="right")

        jframe = tk.Frame(p, bg="#0a0c11")
        jframe.pack(fill="both", expand=True, padx=14, pady=(2, 14))
        self._jview = tk.Text(jframe, bg="#0a0c11", fg="#c9d1d9",
                              font=FONT_MONO, relief="flat", bd=0,
                              state="disabled", wrap="none")
        jvs = ttk.Scrollbar(jframe, command=self._jview.yview)
        jhs = ttk.Scrollbar(jframe, orient="horizontal", command=self._jview.xview)
        self._jview.configure(yscrollcommand=jvs.set, xscrollcommand=jhs.set)
        jvs.pack(side="right", fill="y")
        jhs.pack(side="bottom", fill="x")
        self._jview.pack(fill="both", expand=True, padx=6, pady=6)
        self._jview.tag_configure("key",    foreground="#79c0ff")
        self._jview.tag_configure("str",    foreground="#a5d6ff")
        self._jview.tag_configure("num",    foreground="#ffa657")
        self._jview.tag_configure("bool",   foreground="#ff7b72")

    def _card(self, parent, title):
        outer = tk.Frame(parent, bg=BG_CARD,
                         highlightthickness=1, highlightbackground=BORDER)
        tk.Label(outer, text=title, font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_MUTED, pady=6).pack(anchor="w", padx=12)
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")
        tk.Frame(outer, bg=BG_CARD, height=6).pack()
        return outer

    def _browse_pdf(self):
        p = filedialog.askopenfilename(
            title="Select Audit Report PDF",
            filetypes=[("PDF files", "*.pdf"), ("DOCX files", "*.docx"), ("All files", "*.*")])
        if p:
            self._pdf_path.set(p)
            name = Path(p).name
            self._file_lbl.configure(text=name, fg=ACCENT2)
            self._drop_lbl.configure(text=name, fg=TEXT_SUCCESS)
            self._log_write(f"Loaded document: {p}", "success")

    def _browse_output(self):
        p = filedialog.askdirectory(title="Select output directory")
        if p:
            self._output_dir.set(p)

    def _browse_schema(self):
        p = filedialog.askopenfilename(
            title="Select Master Schema JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if p:
            self._schema_path.set(p)
            self._log_write(f"Master schema selected: {p}")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _copy_json(self):
        txt = self._jview.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(txt)

    def _open_output(self):
        if hasattr(self, "_output_path") and self._output_path and os.path.isfile(self._output_path):
            os.startfile(self._output_path)

    def _open_md(self):
        if hasattr(self, "_md_path") and self._md_path and os.path.isfile(self._md_path):
            os.startfile(self._md_path)

    def _open_images(self):
        if hasattr(self, "_img_dir") and self._img_dir and os.path.isdir(self._img_dir):
            os.startfile(self._img_dir)

    def _log_write(self, msg: str, tag: str = ""):
        def _do():
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self._log.configure(state="normal")
            line = f"[{ts}] {msg}\n"
            if tag:
                self._log.insert("end", line, tag)
            else:
                self._log.insert("end", line)
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, _do)

    def _start(self):
        if self._processing:
            return
        pdf = self._pdf_path.get()
        if not pdf:
            messagebox.showwarning("No document selected", "Please select a PDF or DOCX report first.")
            return

        self._processing = True
        self._run_btn.configure(state="disabled", text="Running Qwen 3.6 VL...")
        self._open_btn.configure(state="disabled", bg=BORDER, fg=TEXT_MUTED)
        self._open_md_btn.configure(state="disabled", bg=BORDER, fg=TEXT_MUTED)
        self._open_img_btn.configure(state="disabled", bg=BORDER, fg=TEXT_MUTED)
        self._bar.set_value(0)
        self._stage_lbl.configure(text="Initializing...", fg=ACCENT)
        for lbl in self._step_lbls:
            lbl.configure(fg=TEXT_MUTED)

        self._jview.configure(state="normal")
        self._jview.delete("1.0", "end")
        self._jview.configure(state="disabled")

        self._log_write("-" * 52)
        self._log_write(f"Initiating pipeline for: {Path(pdf).name}", "accent")

        threading.Thread(
            target=run_pipeline,
            args=(
                pdf,
                self._output_dir.get(),
                self._engine_mode.get(),
                self._vlm_model.get(),
                self._load_in_4bit.get(),
                self._schema_path.get(),
                self._on_progress,
                self._log_write,
                self._on_done,
                self._on_error
            ),
            daemon=True,
        ).start()

    def _on_progress(self, pct, label):
        def _do():
            self._bar.set_value(pct)
            self._stage_lbl.configure(
                text=label, fg=TEXT_SUCCESS if pct >= 100 else ACCENT2)
            for i, (_, thresh) in enumerate(STAGES):
                if pct >= thresh:
                    self._step_lbls[i].configure(fg=TEXT_SUCCESS)
        self.after(0, _do)

    def _on_done(self, out_path, result, md_path=None, img_dir=None):
        def _do():
            self._processing = False
            self._output_path = out_path
            self._md_path = md_path
            self._img_dir = img_dir

            self._run_btn.configure(state="normal", text="Process Document with Qwen 3.6 VL")
            self._open_btn.configure(state="normal", bg=ACCENT2, fg="white")
            if md_path and os.path.exists(md_path):
                self._open_md_btn.configure(state="normal", bg="#3a3f58", fg="white")
            if img_dir and os.path.exists(img_dir):
                self._open_img_btn.configure(state="normal", bg="#3a3f58", fg="white")

            pretty = json.dumps(result, indent=2, ensure_ascii=False)
            self._jview.configure(state="normal")
            self._jview.delete("1.0", "end")
            self._jview.insert("end", pretty)
            self._highlight_json(pretty)
            self._jview.configure(state="disabled")

            self._log_write(f"Saved Standardized JSON: {out_path}", "success")
            if md_path:
                self._log_write(f"Saved Intermediate Transcript: {md_path}", "success")
            if img_dir:
                self._log_write(f"Saved Figures: {img_dir}", "success")
        self.after(0, _do)

    def _on_error(self, msg):
        def _do():
            self._processing = False
            self._run_btn.configure(state="normal", text="Process Document with Qwen 3.6 VL")
            self._log_write(f"ERROR: {msg}", "error")
            self._bar.set_value(0)
            self._stage_lbl.configure(text="Failed", fg=TEXT_ERROR)
        self.after(0, _do)

    def _highlight_json(self, content: str):
        for tag in ("key", "str", "num", "bool"):
            self._jview.tag_remove(tag, "1.0", "end")

        patterns = [
            ("key",  r'"([^"]+)"\s*:'),
            ("str",  r':\s*"([^"]*)"'),
            ("num",  r':\s*(-?\d+\.?\d*)'),
            ("bool", r':\s*(true|false|null)'),
        ]
        for tag, pat in patterns:
            for m in re.finditer(pat, content):
                s = f"1.0+{m.start(1)}c"
                e = f"1.0+{m.end(1)}c"
                self._jview.tag_add(tag, s, e)

    def _pulse(self):
        seq = [ACCENT, "#a093ff", "#8f82ff", ACCENT, "#6358d4"]
        self._pi = 0

        def _step():
            self._title_lbl.configure(fg=seq[self._pi % len(seq)])
            self._pi += 1
            self.after(1100, _step)

        self.after(1100, _step)


if __name__ == "__main__":
    style_root = tk.Tk()
    style_root.withdraw()
    s = ttk.Style(style_root)
    s.theme_use("clam")
    style_root.destroy()

    app = App()
    style = ttk.Style(app)
    style.theme_use("clam")
    style.configure("Vertical.TScrollbar",
                    background=BG_CARD, troughcolor=BG_DARK,
                    bordercolor=BORDER, arrowcolor=TEXT_MUTED)
    style.configure("Horizontal.TScrollbar",
                    background=BG_CARD, troughcolor=BG_DARK,
                    bordercolor=BORDER, arrowcolor=TEXT_MUTED)
    app.mainloop()
