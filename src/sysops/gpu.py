"""GPU detection helpers
Try nvidia-smi, then parse lspci for VGA/3D controllers.
"""
import subprocess
from typing import Dict, Any

def _run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return None

def detect_gpu() -> Dict[str, Any]:
    # Try nvidia-smi first
    nvm = _run_cmd(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"]) 
    if nvm:
        parts = [p.strip() for p in nvm.split(",")]
        return {"vendor": "NVIDIA", "name": parts[0] if parts else None, "driver": parts[1] if len(parts) > 1 else None}

    # Fallback to lspci
    lsp = _run_cmd(["lspci"]) or ""
    lines = [l for l in lsp.splitlines() if "VGA compatible controller" in l or "3D controller" in l]
    if not lines:
        return {}
    line = lines[0]
    try:
        desc = line.split(':', 2)[-1].strip()
    except Exception:
        desc = line
    vendor = None
    if "NVIDIA" in desc.upper():
        vendor = "NVIDIA"
    elif "INTEL" in desc.upper():
        vendor = "Intel"
    elif "AMD" in desc.upper() or "RADEON" in desc.upper():
        vendor = "AMD"
    return {"vendor": vendor, "description": desc}
