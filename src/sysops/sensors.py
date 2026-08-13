"""Sensors helper (wraps `sensors` output if lm-sensors is installed).
Returns dict with raw output under 'raw' key or empty dict if not available.
"""
import subprocess
from typing import Dict, Any

def read_sensors() -> Dict[str, Any]:
    try:
        out = subprocess.check_output(["sensors"], stderr=subprocess.DEVNULL, text=True)
        return {"raw": out}
    except Exception:
        return {}
