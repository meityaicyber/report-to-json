import re

# APIs that are never legitimate — always malicious intent
MALICIOUS_JS_APIS = {
    "exportDataObject",     # silently execute embedded files
    "launchURL",            # open external URLs / exfiltrate data
    "app.exec",             # execute system commands
    "util.stringToStream",  # encode data for exfiltration
    "Net.HTTP",             # raw network request
    "nLaunch",              # silent execution flag
    "this.submitForm",      # send data to external server
    "app.openDoc",          # open external document
    "app.launchURL",        # variant of launchURL
}

# APIs used exclusively in legitimate form PDFs
BENIGN_JS_APIS = {
    "getField",
    "setField",
    "app.alert",
    "event.value",
    "AFNumber_Format",
    "AFDate_Format",
    "AFRange_Validate",
    "AFPercent_Format",
    "util.printd",
    "this.getField",
    "event.rc",
}


def classify_javascript(js_code):
    """
    Classify JavaScript found inside a PDF.

    Returns:
        verdict : "MALICIOUS" | "BENIGN" | "UNKNOWN"
        apis    : list of matched API names / flags
        score   : obfuscation/complexity score (0-100+)
    """
    malicious_found = [api for api in MALICIOUS_JS_APIS if api in js_code]
    benign_found    = [api for api in BENIGN_JS_APIS if api in js_code]

    obfusc_score = 0
    obfusc_flags = []

    if re.search(r"%u[0-9a-fA-F]{4}", js_code):
        obfusc_score += 50
        obfusc_flags.append("unicode escape sequences (shellcode pattern)")

    if "eval(" in js_code:
        obfusc_score += 40
        obfusc_flags.append("eval() — dynamic code execution")

    if "unescape(" in js_code:
        obfusc_score += 40
        obfusc_flags.append("unescape() — runtime payload decoding")

    for line in js_code.split("\n"):
        if len(line) > 500:
            obfusc_score += 30
            obfusc_flags.append("extremely long line (>500 chars) — obfuscation")
            break

    if re.search(r"new Array\(\)", js_code) and re.search(r"for.*\d{3,}", js_code):
        obfusc_score += 60
        obfusc_flags.append("heap spray pattern detected")

    if malicious_found or obfusc_score >= 50:
        return "MALICIOUS", malicious_found + obfusc_flags, obfusc_score

    if benign_found and not obfusc_flags:
        return "BENIGN", benign_found, obfusc_score

    return "UNKNOWN", obfusc_flags, obfusc_score