"""
sysops.config
~~~~~~~~~~~~~

Small persisted config file for user preferences — currently just the
default logo image/width/color, set via ``sysops logo set``.

Stored at:
    Windows: %APPDATA%\\sysops\\config.json
    macOS/Linux: $XDG_CONFIG_HOME/sysops/config.json
    (usually ~/.config/sysops/config.json)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def _config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "sysops"


def config_path() -> Path:
    return _config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_config(data: Dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
