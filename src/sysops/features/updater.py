"""Self-update support for installed sysops environments.

Windows cannot overwrite the running sysops.exe, so updates are performed by
an independent helper that starts before the current process exits, waits for
its PID to disappear, and then runs pip against the managed source checkout.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from sysops import config

BRANCH = "main"
HELPER_TIMEOUT = 15


def _repo_root() -> Path:
    home = getattr(config, "SYSOPS_HOME", None)
    if home:
        return Path(home) / "src"
    candidates = [
        Path.home() / ".local" / "share" / "sysops" / "src-checkout",
        Path(sys.prefix).resolve().parent / "src-checkout",
    ]
    for candidate in candidates:
        if (candidate / ".git").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("Could not locate the managed SysOps source checkout")


def _venv_python() -> Path:
    home = getattr(config, "SYSOPS_HOME", None)
    if home:
        return Path(home) / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    candidate = Path(sys.prefix) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def check_for_update() -> tuple[bool, str]:
    try:
        repo = _repo_root()
    except RuntimeError as exc:
        return False, str(exc)
    result = subprocess.run(["git", "fetch", "origin", BRANCH], cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"Could not check for updates: {result.stderr.strip()}"
    local_result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True)
    remote_result = subprocess.run(["git", "rev-parse", f"origin/{BRANCH}"], cwd=repo, capture_output=True, text=True)
    if local_result.returncode != 0 or remote_result.returncode != 0:
        return False, "Could not determine the installed or remote version."
    local = local_result.stdout.strip()
    remote = remote_result.stdout.strip()
    if local == remote:
        return False, "SysOps is already up to date. No further actions needed."
    return True, f"Update available ({local[:7]} -> {remote[:7]})."


def _write_windows_helper(pid: int, repo: Path, python_exe: Path) -> Path:
    fd, path = tempfile.mkstemp(suffix=".bat", prefix="sysops_update_")
    os.close(fd)
    script = f'''@echo off
setlocal
:wait
tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >NUL
    goto wait
)
cd /d "{repo}"
git pull origin {BRANCH}
"{python_exe}" -m pip install --upgrade --force-reinstall --no-deps .
if errorlevel 1 (
    echo SysOps update failed.
) else (
    echo SysOps updated. Run "sysops" to use the new version.
)
del "%~f0"
'''
    Path(path).write_text(script, encoding="utf-8")
    return Path(path)


def _write_posix_helper(pid: int, repo: Path, python_exe: Path) -> Path:
    fd, path = tempfile.mkstemp(suffix=".sh", prefix="sysops_update_")
    os.close(fd)
    script = f'''#!/bin/sh
end=$(( $(date +%s) + {HELPER_TIMEOUT} ))
while kill -0 {pid} 2>/dev/null; do
    [ "$(date +%s)" -ge "$end" ] && exit 1
    sleep 1
done
cd "{repo}" || exit 1
git pull origin {BRANCH}
"{python_exe}" -m pip install --upgrade --force-reinstall --no-deps .
rm -- "$0"
'''
    helper = Path(path)
    helper.write_text(script, encoding="utf-8")
    helper.chmod(0o755)
    return helper


def _spawn_detached(helper_path: Path) -> None:
    if os.name == "nt":
        subprocess.Popen(["cmd.exe", "/c", str(helper_path)], creationflags=0x00000008 | 0x00000200, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["/bin/sh", str(helper_path)], start_new_session=True, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_update() -> None:
    print("Checking for SysOps updates...")
    available, message = check_for_update()
    print(message)
    if not available:
        return
    repo = _repo_root()
    python_exe = _venv_python()
    pid = os.getpid()
    print("Preparing update (the install will finish after this process exits)...")
    helper = _write_windows_helper(pid, repo, python_exe) if os.name == "nt" else _write_posix_helper(pid, repo, python_exe)
    _spawn_detached(helper)
    print("Update scheduled. The detached updater will finish automatically.")
    print("Run 'sysops' again after a few seconds.")
    time.sleep(0.5)
    sys.exit(0)

update = run_update
