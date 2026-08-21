"""Self-update support for installed sysops environments."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BRANCH = "main"


def _run(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def _source_checkout() -> Path | None:
    """Find the source directory recorded by pip's direct_url metadata."""
    try:
        from importlib.metadata import distribution
        from urllib.parse import unquote, urlparse

        metadata = distribution("sysops").read_text("direct_url.json")
        if not metadata:
            return None
        url = json.loads(metadata).get("url", "")
        if not url.startswith("file://"):
            return None
        path = Path(unquote(urlparse(url).path))
        if os.name == "nt" and path.as_posix().startswith("/"):
            path = Path(path.as_posix().lstrip("/"))
        return path if (path / ".git").is_dir() else None
    except Exception:
        return None


def _venv_python() -> str:
    candidate = Path(sys.prefix) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(candidate if candidate.exists() else Path(sys.executable))


def update() -> int:
    print("Checking for SysOps updates...")

    if shutil.which("git") is None:
        print("Git is required for updating this installation.")
        return 1

    checkout = _source_checkout()
    if checkout is None:
        print("Could not locate the managed SysOps source checkout.")
        print("Run the official installer again to repair the installation and enable self-updates.")
        return 1

    code, output = _run(["git", "fetch", "origin", BRANCH], cwd=checkout)
    if code != 0:
        print(f"Update check failed: {output or 'git fetch failed'}")
        return 1

    code, local = _run(["git", "rev-parse", "HEAD"], cwd=checkout)
    code2, remote = _run(["git", "rev-parse", f"origin/{BRANCH}"], cwd=checkout)
    if code != 0 or code2 != 0:
        print("Could not determine the installed or remote version.")
        return 1

    if local == remote:
        print("SysOps is already up to date. No further actions needed.")
        return 0

    print("Update available. Downloading the latest version...")
    code, output = _run(["git", "pull", "--ff-only", "origin", BRANCH], cwd=checkout)
    if output:
        print(output)
    if code != 0:
        print("Update failed. Your existing source was not replaced.")
        return 1

    print("Installing updated files and dependencies...")
    code, output = _run([_venv_python(), "-m", "pip", "install", "--upgrade", "."], cwd=checkout)
    if output:
        print(output)
    if code != 0:
        print("The source was updated, but dependency/package installation failed.")
        return 1

    print("SysOps update complete. All required package changes have been applied.")
    return 0
