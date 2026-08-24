"""sysops.output (summary rendering)
----------------------------------

Renders the ``sysops`` system summary in one bordered layout, optionally
placing a generated terminal logo above the panels.
"""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def render(data: dict[str, Any], logo: str | None = None) -> None:
    """Render the system summary as bordered panels, with an optional logo."""
    if logo:
        console.print(Panel(Text.from_ansi(logo), border_style="cyan", padding=(0, 1)))
    for panel in _build_panels(data):
        console.print(panel)


def _system_info(data: dict[str, Any]) -> dict[str, Any]:
    if "system" in data:
        return data.get("system", {})
    os_info = data.get("os", {})
    host = data.get("host", {})
    desktop = data.get("desktop", {})
    uptime = data.get("uptime", {}).get("uptime_seconds")
    return {
        "hostname": host.get("node", "localhost"),
        "os": os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform") or "Unknown",
        "kernel": host.get("kernel") or "Unknown",
        "uptime": _format_uptime(uptime),
        "de": desktop.get("de"),
        "wm": desktop.get("wm"),
        "terminal": desktop.get("terminal"),
        "shell": desktop.get("shell"),
    }


def _format_uptime(seconds: Any) -> str:
    if not seconds:
        return "N/A"
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _kv_table(rows: list[tuple[str, str]], key_style: str = "bold cyan") -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(style=key_style, no_wrap=True)
    table.add_column()
    for label, value in rows:
        table.add_row(label, value)
    return table


def _system_panel(data: dict[str, Any]) -> Panel:
    info = _system_info(data)
    rows = [
        ("OS", str(info.get("os", "N/A"))),
        ("Kernel", str(info.get("kernel", "N/A"))),
        ("Uptime", str(info.get("uptime", "N/A"))),
    ]
    for key in ("de", "wm", "terminal", "shell"):
        if info.get(key):
            rows.append((key.upper(), str(info[key])))
    return Panel(_kv_table(rows), title=f"System Summary — {info.get('hostname', '')}", border_style="green")


def _cpu_panel(data: dict[str, Any]) -> Panel:
    cpu = data.get("cpu", {})
    physical = cpu.get("physical", cpu.get("physical_cores", "?"))
    logical = cpu.get("logical", cpu.get("logical_cores", "?"))
    mhz = cpu.get("mhz", cpu.get("freq_mhz"))
    cores = f"{physical} phys / {logical} log"
    if mhz:
        cores += f" @ {mhz} MHz"
    rows = [("Model", str(cpu.get("model", "N/A"))), ("Cores", cores)]
    return Panel(_kv_table(rows, key_style="bold yellow"), title="CPU Specs", border_style="yellow")


def _memory_panel(data: dict[str, Any]) -> Panel:
    mem = data.get("memory", {})
    if "total" in mem:
        total, used = mem.get("total", "N/A"), mem.get("used", "N/A")
        used_pct = mem.get("used_pct", mem.get("percent", "?"))
        swap_total, swap_used = mem.get("swap_total", "N/A"), mem.get("swap_used", "N/A")
        swap_pct = mem.get("swap_pct", mem.get("swap_percent", "?"))
    else:
        total_bytes = mem.get("total_bytes") or 0
        used_bytes = mem.get("used_bytes") or 0
        swap_total_bytes = mem.get("swap_total") or 0
        swap_used_bytes = mem.get("swap_used") or 0
        total = _format_bytes(total_bytes)
        used = _format_bytes(used_bytes)
        used_pct = mem.get("percent", "?")
        swap_total = _format_bytes(swap_total_bytes)
        swap_used = _format_bytes(swap_used_bytes)
        swap_pct = mem.get("swap_percent", "?")
    rows = [
        ("Total RAM", str(total)),
        ("Used RAM", f"{used} ({used_pct}%)"),
        ("Swap", f"{swap_used} / {swap_total} ({swap_pct}%)"),
    ]
    return Panel(_kv_table(rows, key_style="bold magenta"), title="Memory Usage", border_style="magenta")


def _format_bytes(value: Any) -> str:
    if not value:
        return "0 B"
    return f"{float(value) / (1024 ** 3):.2f} GiB"


def _disks(data: dict[str, Any]) -> list[dict[str, Any]]:
    disks = data.get("disks", [])
    return disks.get("partitions", []) if isinstance(disks, dict) else disks


def _disks_panel(data: dict[str, Any]) -> Panel:
    table = Table("Device", "Mount", "FS", "Size", "Used", box=box.SIMPLE, expand=True)
    for disk in _disks(data):
        total = disk.get("total", disk.get("size"))
        size = f"{float(total) / (1024 ** 3):.1f}G" if isinstance(total, (int, float)) and total else str(total or "?")
        used = disk.get("percent")
        used_text = f"{used}%" if used is not None else str(disk.get("used", "?"))
        table.add_row(
            str(disk.get("device", "?")),
            str(disk.get("mountpoint", disk.get("mount", "?"))),
            str(disk.get("fstype", disk.get("fs", "?"))),
            size,
            used_text,
        )
    return Panel(table, title="Storage & Disks", border_style="red")


def _network(data: dict[str, Any]) -> list[dict[str, Any]]:
    network = data.get("network", [])
    if isinstance(network, dict):
        result = []
        for name, info in network.get("interfaces", {}).items():
            addresses = info.get("addresses", [])
            address = addresses[0].get("address") if addresses else "-"
            result.append({"name": name, "address": address or "-", "status": "UP" if info.get("is_up") else "DOWN"})
        return result
    return network


def _network_panel(data: dict[str, Any]) -> Panel:
    table = Table("Interface", "Address", "Status", box=box.SIMPLE, expand=True)
    for iface in _network(data)[:8]:
        status = iface.get("status", "")
        table.add_row(str(iface.get("name", "")), str(iface.get("address", "-")), Text(status, style="green" if status == "UP" else "red"))
    return Panel(table, title="Network Interfaces", border_style="blue")


def _gpu_panel(data: dict[str, Any]) -> Panel:
    gpu = data.get("gpu", {})
    if isinstance(gpu, list):
        gpu = gpu[0] if gpu else {}
    rows = [(str(k).capitalize(), str(v)) for k, v in gpu.items() if v]
    return Panel(_kv_table(rows, key_style="bold blue"), title="GPU Information", border_style="cyan")


def _build_panels(data: dict[str, Any]) -> list[Panel]:
    panels = [
        _system_panel(data),
        _cpu_panel(data),
        _memory_panel(data),
        _disks_panel(data),
        _network_panel(data),
    ]
    if data.get("gpu"):
        panels.append(_gpu_panel(data))
    return panels


def render_json(data: dict[str, Any]) -> str:
    import json
    return json.dumps(data, indent=2, ensure_ascii=False)
