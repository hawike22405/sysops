"""Polished terminal rendering for SysOps system reports."""

from __future__ import annotations

import json
import re
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")


def _strip_ansi(text: str) -> str:
    text = _OSC_RE.sub("", text)
    return _ANSI_RE.sub("", text)


def _format_bytes(value: Any) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if value <= 0:
        return "0 B"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    return f"{value:.2f} {units[index]}"


def _format_uptime(seconds: Any) -> str:
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "N/A"
    if total <= 0:
        return "N/A"
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _system_info(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("system"), dict):
        return data["system"]
    os_info = data.get("os") if isinstance(data.get("os"), dict) else {}
    host = data.get("host") if isinstance(data.get("host"), dict) else {}
    desktop = data.get("desktop") if isinstance(data.get("desktop"), dict) else {}
    uptime = data.get("uptime") if isinstance(data.get("uptime"), dict) else {}
    return {
        "hostname": host.get("node") or "localhost",
        "os": os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform") or "Unknown",
        "kernel": host.get("kernel") or "Unknown",
        "uptime": _format_uptime(uptime.get("uptime_seconds")),
        "de": desktop.get("de"),
        "wm": desktop.get("wm"),
        "terminal": desktop.get("terminal"),
        "shell": desktop.get("shell"),
    }


def _kv_table(rows: list[tuple[str, str]], key_style: str = "bold cyan") -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(style=key_style, no_wrap=True)
    table.add_column(overflow="fold")
    for label, value in rows:
        table.add_row(label, value)
    return table


def _system_panel(data: dict[str, Any]) -> Panel:
    info = _system_info(data)
    rows = [("OS", str(info.get("os", "N/A"))), ("Kernel", str(info.get("kernel", "N/A"))), ("Uptime", str(info.get("uptime", "N/A")))]
    for key in ("de", "wm", "terminal", "shell"):
        if info.get(key):
            rows.append((key.upper(), str(info[key])))
    return Panel(_kv_table(rows), title=f"SYSTEM  •  {info.get('hostname', 'localhost')}", border_style="green", box=box.ROUNDED)


def _cpu_panel(data: dict[str, Any]) -> Panel:
    cpu = data.get("cpu") if isinstance(data.get("cpu"), dict) else {}
    physical = cpu.get("physical") or cpu.get("physical_cores") or "?"
    logical = cpu.get("logical") or cpu.get("logical_cores") or "?"
    freq = cpu.get("mhz") or cpu.get("freq_mhz")
    cores = f"{physical} physical / {logical} logical"
    if freq:
        cores += f" @ {freq} MHz"
    return Panel(_kv_table([("Model", str(cpu.get("model") or "N/A")), ("CPU", cores)]), title="CPU", border_style="yellow", box=box.ROUNDED)


def _memory_panel(data: dict[str, Any]) -> Panel:
    mem = data.get("memory") if isinstance(data.get("memory"), dict) else {}
    total = mem.get("total_bytes", mem.get("total"))
    used = mem.get("used_bytes", mem.get("used"))
    total_display = _format_bytes(total) if isinstance(total, (int, float)) else str(total or "N/A")
    used_display = _format_bytes(used) if isinstance(used, (int, float)) else str(used or "N/A")
    pct = mem.get("percent", mem.get("used_pct", "?"))
    swap_total = mem.get("swap_total")
    swap_used = mem.get("swap_used")
    if isinstance(swap_total, (int, float)):
        swap = f"{_format_bytes(swap_used)} / {_format_bytes(swap_total)} ({mem.get('swap_percent', '?')}%)"
    else:
        swap = f"{swap_used or 'N/A'} / {swap_total or 'N/A'}"
    return Panel(_kv_table([("RAM", f"{used_display} / {total_display} ({pct}%)"), ("Swap", swap)], key_style="bold magenta"), title="MEMORY", border_style="magenta", box=box.ROUNDED)


def _disks(data: dict[str, Any]) -> list[dict[str, Any]]:
    disks = data.get("disks", [])
    return disks.get("partitions", []) if isinstance(disks, dict) else disks


def _disks_panel(data: dict[str, Any]) -> Panel:
    table = Table("Device", "Mount", "FS", "Size", "Used", box=box.SIMPLE, expand=True)
    for disk in _disks(data):
        total = disk.get("total", disk.get("size"))
        size = _format_bytes(total) if isinstance(total, (int, float)) else str(total or "?")
        percent = disk.get("percent")
        used = f"{percent}%" if percent is not None else str(disk.get("used") or "?")
        table.add_row(str(disk.get("device") or "?"), str(disk.get("mountpoint", disk.get("mount", "?"))), str(disk.get("fstype", disk.get("fs", "?"))), size, used)
    if not _disks(data):
        table.add_row("—", "—", "—", "N/A", "N/A")
    return Panel(table, title="STORAGE", border_style="red", box=box.ROUNDED)


def _network(data: dict[str, Any]) -> list[dict[str, Any]]:
    network = data.get("network", [])
    if isinstance(network, dict):
        result = []
        for name, info in network.get("interfaces", {}).items():
            addresses = info.get("addresses", [])
            address = next((a.get("address") for a in addresses if a.get("address")), "-")
            result.append({"name": name, "address": address, "status": "UP" if info.get("is_up") else "DOWN"})
        return result
    return network


def _network_panel(data: dict[str, Any]) -> Panel:
    table = Table("Interface", "Address", "Status", box=box.SIMPLE, expand=True)
    interfaces = _network(data)
    for iface in interfaces[:10]:
        status = str(iface.get("status") or "UNKNOWN")
        table.add_row(str(iface.get("name") or ""), str(iface.get("address") or "-"), Text(status, style="green" if status == "UP" else "red"))
    if not interfaces:
        table.add_row("—", "—", Text("N/A", style="dim"))
    return Panel(table, title="NETWORK", border_style="blue", box=box.ROUNDED)


def _gpu_panel(data: dict[str, Any]) -> Panel:
    gpu = data.get("gpu") or {}
    if isinstance(gpu, list):
        gpu = gpu[0] if gpu else {}
    rows = [(str(key).replace("_", " ").title(), str(value)) for key, value in gpu.items() if value]
    if not rows:
        rows = [("Device", "N/A")]
    return Panel(_kv_table(rows, key_style="bold blue"), title="GPU", border_style="cyan", box=box.ROUNDED)


def _build_panels(data: dict[str, Any]) -> list[Panel]:
    panels = [_system_panel(data), _cpu_panel(data), _memory_panel(data), _disks_panel(data), _network_panel(data)]
    if data.get("gpu"):
        panels.append(_gpu_panel(data))
    return panels


def _render_side_by_side(data: dict[str, Any], logo: str) -> None:
    info = _system_info(data)
    logo_lines = logo.splitlines() or [""]
    info_lines = [
        f"[bold cyan]{info.get('hostname', 'localhost')}[/bold cyan]",
        f"[cyan]{'─' * max(8, min(len(str(info.get('hostname', 'localhost'))), 28))}[/cyan]",
        f"[bold cyan]OS[/bold cyan]       {info.get('os', 'N/A')}",
        f"[bold cyan]Kernel[/bold cyan]   {info.get('kernel', 'N/A')}",
        f"[bold cyan]Uptime[/bold cyan]   {info.get('uptime', 'N/A')}",
    ]
    for key in ("de", "wm", "terminal", "shell"):
        if info.get(key):
            info_lines.append(f"[bold cyan]{key.upper():<10}[/bold cyan] {info[key]}")

    cpu = data.get("cpu") or {}
    if cpu.get("model"):
        info_lines.append(f"[bold cyan]CPU[/bold cyan]      {cpu['model']}")
    mem = data.get("memory") or {}
    if "total_bytes" in mem:
        info_lines.append(f"[bold cyan]Memory[/bold cyan]  {_format_bytes(mem.get('used_bytes'))} / {_format_bytes(mem.get('total_bytes'))} ({mem.get('percent', '?')}%)")
    gpu = data.get("gpu") or {}
    if isinstance(gpu, list) and gpu:
        if gpu[0].get("name"):
            info_lines.append(f"[bold cyan]GPU[/bold cyan]      {gpu[0]['name']}")
    elif isinstance(gpu, dict) and gpu.get("name"):
        info_lines.append(f"[bold cyan]GPU[/bold cyan]      {gpu['name']}")

    logo_width = max(len(_strip_ansi(line)) for line in logo_lines)
    gap = "   "
    max_lines = max(len(logo_lines), len(info_lines))
    for index in range(max_lines):
        left = logo_lines[index] if index < len(logo_lines) else ""
        right = info_lines[index] if index < len(info_lines) else ""
        padded = left + (" " * max(0, logo_width - len(_strip_ansi(left))))
        console.print(Text.from_ansi(padded) + Text(gap) + Text.from_markup(right))
    console.print()


def render(data: dict[str, Any], logo: str | None = None) -> None:
    """Render a structured, terminal-native system report."""
    title = Text(" SYSOPS ", style="bold white on blue")
    subtitle = Text("  SYSTEM OPERATIONS REPORT  ", style="bold cyan")
    console.print()
    console.rule(title)
    console.print(subtitle)
    console.print()
    if logo:
        _render_side_by_side(data, logo)
    for panel in _build_panels(data):
        console.print(panel)
    console.print("[dim]Tip:[/dim] use [bold]sysops --help[/bold] to explore monitor, dashboard, benchmark, ASCII and 3D tools.")
    console.print()


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
