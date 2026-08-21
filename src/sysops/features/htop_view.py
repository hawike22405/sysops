"""Interactive htop-style system view for SysOps."""

from __future__ import annotations

import contextlib
import os
import select
import sys
import time
from dataclasses import dataclass

import psutil
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

REFRESH_SECONDS = 1.5
SAMPLE_INTERVAL = 0.5
TOP_N_PROCESSES = 15

console = Console()


@dataclass
class SortMode:
    key: str = "cpu"
    label: str = "CPU%"


def _bar(percent: float, width: int = 30) -> ProgressBar:
    return ProgressBar(total=100, completed=max(0, min(percent, 100)), width=width)


def _color_for(percent: float) -> str:
    if percent >= 85:
        return "red"
    if percent >= 60:
        return "yellow"
    return "green"


def _build_cpu_panel() -> Panel:
    per_core = psutil.cpu_percent(percpu=True)
    table = Table.grid(padding=(0, 1))
    table.add_column(width=6)
    table.add_column()
    table.add_column(width=8, justify="right")
    for i, pct in enumerate(per_core):
        table.add_row(
            f"CPU{i}",
            _bar(pct, width=28),
            Text(f"{pct:5.1f}%", style=_color_for(pct)),
        )
    return Panel(table, title=f"CPU ({len(per_core)} cores)", border_style="cyan")


def _build_mem_panel() -> Panel:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    table = Table.grid(padding=(0, 1))
    table.add_column(width=6)
    table.add_column()
    table.add_column(justify="right")
    used_gb = vm.used / (1024 ** 3)
    total_gb = vm.total / (1024 ** 3)
    table.add_row(
        "Mem",
        _bar(vm.percent, width=28),
        Text(f"{used_gb:.1f}/{total_gb:.1f} GB ({vm.percent:.0f}%)", style=_color_for(vm.percent)),
    )
    if swap.total > 0:
        used_gb = swap.used / (1024 ** 3)
        total_gb = swap.total / (1024 ** 3)
        table.add_row(
            "Swap",
            _bar(swap.percent, width=28),
            Text(f"{used_gb:.1f}/{total_gb:.1f} GB ({swap.percent:.0f}%)", style=_color_for(swap.percent)),
        )
    else:
        table.add_row("Swap", Text("—", style="dim"), Text("N/A on this platform", style="dim"))
    return Panel(table, title="Memory", border_style="magenta")


_PSEUDO_PROCESS_NAMES = {"system idle process", "system"}
_CPU_COUNT = psutil.cpu_count(logical=True) or 1


def _build_process_table(sort: SortMode) -> Panel:
    procs = []
    for process in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent", "username"]):
        try:
            info = process.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        name = (info.get("name") or "").strip().lower()
        if name in _PSEUDO_PROCESS_NAMES:
            continue

        raw_cpu = info.get("cpu_percent") or 0.0
        info["cpu_percent"] = min(raw_cpu / _CPU_COUNT, 100.0)
        procs.append(info)

    key_fn = {
        "cpu": lambda info: info.get("cpu_percent") or 0,
        "mem": lambda info: info.get("memory_percent") or 0,
        "pid": lambda info: info.get("pid") or 0,
        "name": lambda info: (info.get("name") or "").lower(),
    }[sort.key]
    procs.sort(key=key_fn, reverse=sort.key in ("cpu", "mem"))

    table = Table(expand=True, border_style="dim")
    table.add_column("PID", justify="right", width=7)
    table.add_column("User", width=14, overflow="ellipsis")
    table.add_column("CPU%", justify="right", width=7)
    table.add_column("MEM%", justify="right", width=7)
    table.add_column("Name", overflow="ellipsis")
    for info in procs[:TOP_N_PROCESSES]:
        cpu = info.get("cpu_percent") or 0.0
        mem = info.get("memory_percent") or 0.0
        table.add_row(
            str(info.get("pid", "")),
            (info.get("username") or "")[:14],
            Text(f"{cpu:.1f}", style=_color_for(cpu)),
            Text(f"{mem:.1f}", style=_color_for(mem * 4)),
            info.get("name") or "",
        )
    return Panel(table, title=f"Processes (sorted by {sort.label}, top {TOP_N_PROCESSES})", border_style="blue")


def _build_frame(sort: SortMode) -> Layout:
    layout = Layout()
    layout.split_column(Layout(name="top", size=12), Layout(name="procs"))
    layout["top"].split_row(
        Layout(_build_cpu_panel(), name="cpu"),
        Layout(_build_mem_panel(), name="mem"),
    )
    layout["procs"].update(_build_process_table(sort))
    return layout


class _KeyReader:
    """Cross-platform non-blocking single-key reader for the live view."""

    def __enter__(self):
        self._fd = None
        self._old = None
        if os.name != "nt" and sys.stdin.isatty():
            import termios
            import tty
            self._fd = sys.stdin.fileno()
            self._old = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._fd is not None and self._old is not None:
            import termios
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)
        return False

    def read(self, timeout: float = 0.1) -> str | None:
        if os.name == "nt":
            import msvcrt
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                if msvcrt.kbhit():
                    key = msvcrt.getwch()
                    if key in ("\x00", "\xe0") and msvcrt.kbhit():
                        msvcrt.getwch()
                        return None
                    return key
                time.sleep(0.02)
            return None
        if self._fd is None:
            time.sleep(timeout)
            return None
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        return sys.stdin.read(1) if ready else None


def _prime_cpu_counters() -> None:
    psutil.cpu_percent(percpu=True)
    for process in psutil.process_iter():
        try:
            process.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def run_htop_view(refresh_seconds: float = REFRESH_SECONDS, sort_key: str = "cpu") -> None:
    """Run the flicker-free htop-style live system view."""
    if refresh_seconds <= 0:
        raise ValueError("refresh_seconds must be greater than 0")
    labels = {"cpu": "CPU%", "mem": "MEM%", "pid": "PID", "name": "Name"}
    if sort_key not in labels:
        raise ValueError(f"invalid sort key: {sort_key}")

    sort = SortMode(key=sort_key, label=labels[sort_key])
    _prime_cpu_counters()
    time.sleep(SAMPLE_INTERVAL)

    with _KeyReader() as keys, Live(console=console, screen=True, refresh_per_second=4) as live:
        last_draw = 0.0
        live.update(_build_frame(sort))
        while True:
            now = time.monotonic()
            if now - last_draw >= refresh_seconds:
                live.update(_build_frame(sort))
                last_draw = now
            key = keys.read(0.1)
            if key:
                key = key.lower()
                if key == "q":
                    return
                if key == "c":
                    sort.key, sort.label = "cpu", "CPU%"
                elif key == "m":
                    sort.key, sort.label = "mem", "MEM%"
                elif key == "p":
                    sort.key, sort.label = "pid", "PID"
                elif key == "n":
                    sort.key, sort.label = "name", "Name"


if __name__ == "__main__":
    run_htop_view()
