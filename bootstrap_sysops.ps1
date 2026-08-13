# Save this file as bootstrap_sysops.ps1 and run it from the repo root in PowerShell.
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$branch = "init/sysops"
$commitMsg = "chore: initial project scaffold — sysops prototype"

if (-not (Test-Path ".git")) {
    Write-Error "This script must be run from the root of a cloned git repository (no .git directory found)."
    exit 1
}

# create and switch to branch
Write-Host "Creating and switching to branch $branch..."
git checkout -b $branch

function Write-File([string]$path, [string]$content) {
    $dir = Split-Path $path -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $content | Out-File -FilePath $path -Encoding utf8 -Force
    Write-Host "Wrote $path"
}

# Files
Write-File README.md @'
# sysops

A modern, terminal-first system information reporter (prototype).

Features:
- Pretty terminal output (Rich)
- JSON output for automation
- Modular probes: OS, CPU, memory, disks, network, GPU, sensors
- No privileged operations by default

See docs/DESIGN.md for design notes and roadmap.
'@

Write-File LICENSE @'
MIT License

Copyright (c) 2026 hawike22405

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'@

Write-File .gitignore @'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtualenv
.venv/
env/
venv/

# Distribution / packaging
build/
dist/
*.egg-info/

# PyInstaller
*.spec

# VSCode
.vscode/

# macOS
.DS_Store

# logs
*.log

# pytest cache
.pytest_cache/

# coverage
htmlcov/
.coverage
'@

Write-File requirements.txt @'
psutil>=5.9
rich>=13.0
distro>=1.8
pytest>=7.0
'@

Write-File pyproject.toml @'
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sysops"
version = "0.1.0"
description = "Terminal-first system information reporter (prototype)"
authors = [
  {name = "hawike22405"}
]
license = {text = "MIT"}

[tool.black]
line-length = 88
'@

Write-File Makefile @'
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv install run test

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

run: install
	$(PY) -m sysops

test: install
	$(PY) -m pytest -q
'@

Write-File .github/workflows/ci.yml @'
name: CI

on:
  push:
    branches: [ main, init/sysops ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest -q
'@

# package files
Write-File src/sysops/__init__.py @'
"""sysops package entry"""

__all__ = ["cli", "probes", "output", "gpu", "sensors"]
'@

Write-File src/sysops/__main__.py @'
#!/usr/bin/env python3
"""
Entry point for running as a module: python -m sysops
"""
from .cli import main

if __name__ == "__main__":
    main()
'@

Write-File src/sysops/cli.py @'
import argparse
import json
from pathlib import Path
from .probes import collect_all
from .output import render_pretty, render_json


def build_parser():
    p = argparse.ArgumentParser(prog="sysops", description="System spec reporter (prototype)")
    p.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty", help="output format")
    p.add_argument("--detail", choices=["brief", "full"], default="brief", help="detail level")
    p.add_argument("--output", "-o", help="write output to file (path)")
    p.add_argument("--modules", help="comma-separated modules to run (default: all)")
    p.add_argument("--watch", type=int, help="repeat every N seconds")
    p.add_argument("--no-root", action="store_true", help="do not attempt privileged probes")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    modules = None
    if args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    data = collect_all(detail=args.detail, modules=modules, no_root=args.no_root)

    out_text = None
    if args.format == "pretty":
        render_pretty(data, detail=args.detail)
    elif args.format == "compact":
        render_pretty(data, detail="brief")
    else:
        out_text = render_json(data)
        print(out_text)

    if args.output:
        path = Path(args.output)
        if out_text is None:
            out_text = json.dumps(data, indent=2)
        path.write_text(out_text, encoding="utf-8")
        print(f"Wrote output to {path}")
'@

Write-File src/sysops/probes.py @'
import platform
import socket
import time
import os
from typing import Dict, Any, List

try:
    import psutil
except Exception:
    psutil = None

try:
    import distro as _distro
except Exception:
    _distro = None

from . import gpu, sensors

def _safe(fun, default=None):
    try:
        return fun()
    except Exception:
        return default

def get_os_info() -> Dict[str, Any]:
    info = {}
    if _distro:
        info["name"] = _distro.name(pretty=True)
        info["id"] = _distro.id()
        info["version"] = _distro.version(best=True)
    else:
        if os.path.exists("/etc/os-release"):
            try:
                data = {}
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            data[k] = v.strip().strip('"')
                info["pretty_name"] = data.get("PRETTY_NAME")
                info["id"] = data.get("ID")
                info["version"] = data.get("VERSION")
            except Exception:
                pass
        info.setdefault("platform", platform.system())
        info.setdefault("platform_release", platform.release())
    return info

def get_kernel_and_host() -> Dict[str, Any]:
    u = platform.uname()
    return {
        "kernel": u.release,
        "kernel_version": u.version,
        "machine": u.machine,
        "processor": u.processor or platform.machine(),
        "node": socket.gethostname(),
    }

def get_uptime() -> Dict[str, Any]:
    try:
        if os.path.exists("/proc/uptime"):
            with open("/proc/uptime", "r", encoding="utf-8") as f:
                s = float(f.readline().split()[0])
            return {"uptime_seconds": int(s)}
    except Exception:
        pass
    try:
        return {"uptime_seconds": int(time.time() - psutil.boot_time())}
    except Exception:
        return {"uptime_seconds": None}

def get_cpu_info() -> Dict[str, Any]:
    info = {}
    if os.path.exists("/proc/cpuinfo"):
        try:
            model = None
            flags = None
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line and model is None:
                        model = line.split(":",1)[1].strip()
                    if "flags" in line:
                        flags = line.split(":",1)[1].strip()
            info["model"] = model
            info["flags"] = flags.split() if flags else None
        except Exception:
            pass
    if psutil:
        info["logical_cores"] = psutil.cpu_count(logical=True)
        info["physical_cores"] = psutil.cpu_count(logical=False)
        try:
            freq = psutil.cpu_freq()
            if freq:
                info["freq_mhz"] = round(freq.current, 2)
        except Exception:
            pass
    return info

def get_memory_info() -> Dict[str, Any]:
    if not psutil:
        return {}
    v = psutil.virtual_memory()
    s = psutil.swap_memory()
    return {
        "total_bytes": v.total,
        "available_bytes": v.available,
        "used_bytes": v.used,
        "percent": v.percent,
        "swap_total": s.total,
        "swap_used": s.used,
        "swap_percent": s.percent,
    }

def get_disks_info() -> Dict[str, Any]:
    if not psutil:
        return {}
    parts = []
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            parts.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "opts": p.opts,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except Exception:
            parts.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "opts": p.opts,
            })
    return {"partitions": parts}

def get_network_info() -> Dict[str, Any]:
    if not psutil:
        return {}
    interfaces = {}
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for name, addrl in addrs.items():
        items = []
        for a in addrl:
            items.append({"family": str(a.family), "address": a.address, "netmask": a.netmask, "broadcast": a.broadcast})
        st = stats.get(name)
        interfaces[name] = {
            "addresses": items,
            "is_up": st.isup if st else None,
            "speed_mbps": st.speed if st else None,
            "mtu": st.mtu if st else None,
        }
    return {"interfaces": interfaces}

def collect_all(detail: str = "brief", modules: List[str] = None, no_root: bool = True) -> Dict[str, Any]:
    data = {}
    data["os"] = get_os_info()
    data["host"] = get_kernel_and_host()
    data["uptime"] = get_uptime()
    if modules is None or "cpu" in modules:
        data["cpu"] = get_cpu_info()
    if modules is None or "memory" in modules:
        data["memory"] = get_memory_info()
    if modules is None or "disks" in modules:
        data["disks"] = get_disks_info()
    if modules is None or "network" in modules:
        data["network"] = get_network_info()

    # GPU and sensors are optional and non-privileged
    if modules is None or "gpu" in modules:
        data["gpu"] = gpu.detect_gpu()
    if modules is None or "sensors" in modules:
        data["sensors"] = sensors.read_sensors()

    if detail == "full":
        data.setdefault("extras", {})
        data["extras"]["note"] = "Full detail probes that require root (dmidecode, smartctl) are intentionally not run by default."
    return data
'@

Write-File src/sysops/output.py @'
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def render_pretty(data: dict, detail="brief"):
    console.rule("[bold cyan]System Summary")
    os_info = data.get("os", {})
    host = data.get("host", {})
    distro = os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform")
    top = f"{distro} — {host.get('kernel')} ({host.get('kernel_version')})"
    console.print(Panel(top, title=f"[green]{host.get('node')}", expand=False))

    # CPU
    cpu = data.get("cpu", {})
    t = Table(show_header=False, box=box.MINIMAL)
    t.add_column("k")
    t.add_column("v")
    t.add_row("CPU", cpu.get("model") or "Unknown")
    cores = f"{cpu.get('physical_cores', '?')} phys / {cpu.get('logical_cores', '?')} log"
    if cpu.get("freq_mhz"):
        cores += f" @ {cpu.get('freq_mhz')} MHz"
    t.add_row("Cores", cores)
    console.print(Panel(t, title="CPU", expand=False))

    # Memory
    mem = data.get("memory", {})
    t = Table(show_header=False, box=box.MINIMAL)
    t.add_column("k")
    t.add_column("v")
    total = mem.get("total_bytes")
    if total:
        gb = total / (1024**3)
        t.add_row("Total", f"{gb:.2f} GiB")
        t.add_row("Used", f"{mem.get('used_bytes') / (1024**3):.2f} GiB ({mem.get('percent')}%)")
        swap_total = mem.get('swap_total') or 0
        t.add_row("Swap", f"{swap_total / (1024**3):.2f} GiB ({mem.get('swap_percent')}%)")
    else:
        t.add_row("Memory", "Unknown")
    console.print(Panel(t, title="Memory", expand=False))

    # Disks
    disks = data.get("disks", {}).get("partitions", [])
    dt = Table("Device", "Mount", "FS", "Size", "Used", box=box.SIMPLE)
    for p in disks:
        total = p.get("total")
        if total:
            size = f"{total / (1024**3):.2f}G"
            used = f"{p.get('percent')}%"
        else:
            size = "?"
            used = "?"
        dt.add_row(p.get("device") or "?", p.get("mountpoint") or "?", p.get("fstype") or "?", size, used)
    console.print(Panel(dt, title="Disks", expand=False))

    # Network (brief)
    net = data.get("network", {}).get("interfaces", {})
    nt = Table("Interface", "Addresses", "Up/Speed", box=box.SIMPLE)
    for name, info in net.items():
        addrs = ", ".join(a.get("address") for a in info.get("addresses", []) if a.get("address"))
        up = ("up" if info.get("is_up") else "down")
        speed = f"{info.get('speed_mbps')}Mbps" if info.get("speed_mbps") else ""
        nt.add_row(name, addrs or "-", f"{up} {speed}")
    console.print(Panel(nt, title="Network", expand=False))

    # GPU
    gpu = data.get("gpu")
    if gpu:
        gtxt = "\n".join(f"{k}: {v}" for k, v in gpu.items() if v)
        console.print(Panel(gtxt or "No GPU info", title="GPU", expand=False))

    # Sensors
    sensors = data.get("sensors")
    if sensors:
        console.print(Panel(sensors.get("raw", ""), title="Sensors (raw)", expand=False))

    if detail == "full":
        extras = data.get("extras")
        console.print(Panel(json.dumps(extras, indent=2), title="Extras", expand=False))

def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
'@

Write-File src/sysops/gpu.py @'
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
'@

Write-File src/sysops/sensors.py @'
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
'@

# tests and helpers
Write-File tests/test_basic.py @'
import json
from src.sysops import probes

def test_collect_all_keys():
    data = probes.collect_all()
    assert isinstance(data, dict)
    assert "os" in data
    assert "host" in data
    assert "cpu" in data
    assert "memory" in data
'@

Write-File scripts/release-wrapup.sh @'
#!/usr/bin/env bash
set -euo pipefail

# Helper used during release: update changelog / tag and show next steps.
echo "Release helper placeholder: build artifacts, create GitHub release, upload binaries."
'@

# docs
Write-File docs/DESIGN.md @'
# Design notes and short roadmap

This document outlines key design choices and a short roadmap for the sysops prototype.

Goals:
- Terminal-first, modern display
- Modular probes and JSON output
- No privileged operations by default

Roadmap:
- Prototype: Python + Rich (this branch)
- Add more probes: smartctl, dmidecode (opt-in)
- Add TUI & theming with Textual or port to Rust for single-binary release
'@

# git add/commit/push
git add --all
git commit -m $commitMsg
Write-Host "Pushing branch $branch to origin..."
git push -u origin $branch

Write-Host "Done. Branch $branch pushed. Create a PR from $branch -> main (draft recommended)."