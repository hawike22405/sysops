"""Self-update support for installed sysops environments."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "hawike22405/sysops"
BRANCH = "main"


def _run(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def _git_available() -> bool:
    return shutil.which("git") is not None


def _is_git_install() -> bool:
    return (Path(__file__).resolve().parents[3] / ".git").exists()


def _source_checkout() -> Path | None:
    candidate = Path(__file__).resolve().parents[3]
    return candidate if (candidate / ".git").is_dir() else None


def _venv_python() -> str:
    return str(Path(sys.prefix) / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))


def _pip_install(python: str, source: Path) -> bool:
    code, output = _run([python, "-m", "pip", "install", "--upgrade", "."], cwd=source)
    if output:
        print(output)
    return code == 0


def update() -> int:
    print("Checking for SysOps updates...")

    checkout = _source_checkout()
    if checkout is not None and _git_available():
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
            print("Update failed. Your existing installation was not replaced.")
            return 1

        print("Installing updated files and dependencies...")
        if not _pip_install(_venv_python(), checkout):
            print("The source was updated, but dependency/package installation failed.")
            return 1
        print("SysOps update complete.")
        return 0

    if not _git_available():
        print("Git is required for updating this installation.")
        return 1

    print("This installation is not a Git checkout.")
    print("Use the official installer again to upgrade this installation automatically.")
    return 1
