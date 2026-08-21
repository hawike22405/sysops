"""
sysops.output (summary rendering)
----------------------------------

Provides two genuinely different layouts for the system summary:

* ``full`` — bordered panels and tables for a normal-width terminal.
* ``compact`` — dense, borderless label/value lines for narrow panes.

Compact mode intentionally avoids fixed-width table columns, so values are
not silently truncated when the terminal is narrow.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _format_bytes(value: Any) -> str:
    if not value:
        return "0 B"
    return f"{float(value) / (1024 ** 3):.2f} GiB"


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


def _system_info(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize system fields for both the current probes and flat render data."""
    if "system" in data:
        return data.get("system", {})
    os_info = data.get("os", {})
    host = data.get("host", {})
    desktop = data.get("desktop", {})
    return {
        "hostname": host.get("node", "localhost"),
        "os": os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform") or "Unknown",
        "kernel": host.get("kernel") or "Unknown",
        "kernel_version": host.get("kernel_version") or "Unknown",
        "uptime": _format_uptime(data.get("uptime", {}).get("uptime_seconds")),
        "de": desktop.get("de"),
        "wm": desktop.get("wm"),
        "terminal": desktop.get("terminal"),
        "shell": desktop.get("shell"),
    }


def _cpu_info(data: dict[str, Any]) -> dict[str, Any]:
    cpu = data.get("cpu", {})
    if "physical" in cpu or "logical" in cpu:
        return cpu
    return {
        "model": cpu.get("model") or "Unknown",
        "physical": cpu.get("physical_cores", "?"),
        "logical": cpu.get("logical_cores", "?"),
        "mhz": cpu.get("freq_mhz"),
    }


def _memory_info(data: dict[str, Any]) -> dict[str, Any]:
    mem = data.get("memory", {})
    if "total" in mem or "used" in mem:
        return mem
    total = mem.get("total_bytes")
    used = mem.get("used_bytes")
    swap_total = mem.get("swap_total") or 0
    swap_used = mem.get("swap_used") or 0
    return {
        "total": _format_bytes(total),
        "used": _format_bytes(used),
        "used_pct": mem.get("percent", 0),
        "swap_total": _format_bytes(swap_total),
        "swap_used": _format_bytes(swap_used),
        "swap_pct": mem.get("swap_percent", 0),
    }


def _disks(data: dict[str, Any]) -> list[dict[str, Any]]:
    disks = data.get("disks", [])
    if isinstance(disks, dict):
        return disks.get("partitions", [])
    return disks


def _network(data: dict[str, Any]) -> list[dict[str, Any]]:
    network = data.get("network", [])
    if isinstance(network, dict):
        result = []
        for name, info in network.get("interfaces", {}).items():
            addresses = info.get("addresses", [])
            address = addresses[0].get("address") if addresses else "-"
            result.append({
                "name": name,
                "address": address or "-",
                "status": "UP" if info.get("is_up") else "DOWN",
            })
        return result
    return network


# ---------------------------------------------------------------------------
# FULL FORMAT
# ---------------------------------------------------------------------------


def render_full(data: dict[str, Any]) -> None:
    """Render the full bordered summary."""
    panels = _build_panels(data, "brief")
    for panel in panels:
        console.print(panel)


def _kv_table(rows: list[tuple[str, str]], key_style: str = "bold cyan") -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(style=key_style, no_wrap=True)
    table.add_column()
    for label, value in rows:
        table.add_row(label, value)
    return table


def _full_system_panel(data: dict[str, Any]) -> Panel:
    info = _system_info(data)
    rows = [
        ("OS", str(info.get("os", "N/A"))),
        ("Kernel", f"{info.get('kernel', 'N/A')} ({info.get('kernel_version', 'N/A')})"),
        ("Uptime", str(info.get("uptime", "N/A"))),
    ]
    for key in ("de", "wm", "terminal", "shell"):
        if info.get(key):
            rows.append((key.upper(), str(info[key])))
    return Panel(_kv_table(rows), title=f"System Summary — {info.get('hostname', '')}", border_style="green")


def _full_cpu_panel(data: dict[str, Any]) -> Panel:
    cpu = _cpu_info(data)
    cores = f"{cpu.get('physical', '?')} phys / {cpu.get('logical', '?')} log"
    if cpu.get("mhz"):
        cores += f" @ {cpu['mhz']} MHz"
    return Panel(
        _kv_table([
            ("Model", str(cpu.get("model", "Unknown"))),
            ("Cores", cores),
        ], key_style="bold yellow"),
        title="⚡ CPU Specs",
        border_style="yellow",
    )


def _full_memory_panel(data: dict[str, Any]) -> Panel:
    mem = _memory_info(data)
    return Panel(
        _kv_table([
            ("Total RAM", str(mem.get("total", "N/A"))),
            ("Used RAM", f"{mem.get('used', 'N/A')} ({mem.get('used_pct', 0)}%)"),
            ("Swap", f"{mem.get('swap_used', 'N/A')} / {mem.get('swap_total', 'N/A')} ({mem.get('swap_pct', 0)}%)"),
        ], key_style="bold magenta"),
        title="🧠 Memory Usage",
        border_style="magenta",
    )


def _full_disks_panel(data: dict[str, Any]) -> Panel:
    table = Table("Device", "Mount", "FS", "Size", "Used", box=box.SIMPLE, expand=True)
    for part in _disks(data):
        total = part.get("total") or part.get("size")
        size = f"{float(total) / (1024 ** 3):.1f}G" if isinstance(total, (int, float)) and total else str(total or "?")
        used = part.get("percent")
        used_text = f"{used}%" if used is not None else str(part.get("used", "?"))
        table.add_row(
            str(part.get("device") or "?"),
            str(part.get("mountpoint", part.get("mount", "?"))),
            str(part.get("fstype", part.get("fs", "?"))),
            size,
            used_text,
        )
    return Panel(table, title="💾 Storage & Disks", border_style="red")


def _full_network_panel(data: dict[str, Any]) -> Panel:
    table = Table("Interface", "Address", "Status", box=box.SIMPLE, expand=True)
    for iface in _network(data)[:8]:
        status = iface.get("status", "")
        styled = Text(status, style="green" if status == "UP" else "red")
        table.add_row(str(iface.get("name", "")), str(iface.get("address", "-")), styled)
    return Panel(table, title="🌐 Network Interfaces", border_style="green")


def _full_gpu_panel(data: dict[str, Any]) -> Panel:
    gpu = data.get("gpu")
    if isinstance(gpu, list):
        gpu = gpu[0] if gpu else {}
    gpu = gpu or {}
    rows = [(str(k).capitalize(), str(v)) for k, v in gpu.items() if v]
    return Panel(_kv_table(rows, key_style="bold blue"), title="🎮 GPU Information", border_style="blue")


def _build_panels(data: dict[str, Any], detail: str = "brief") -> list[Panel]:
    panels = [
        _full_system_panel(data),
        _full_cpu_panel(data),
        _full_memory_panel(data),
        _full_disks_panel(data),
        _full_network_panel(data),
    ]
    if data.get("gpu"):
        panels.append(_full_gpu_panel(data))
    sensors = data.get("sensors")
    if isinstance(sensors, dict) and sensors.get("raw"):
        raw_lines = [line.strip() for line in sensors["raw"].splitlines() if line.strip()]
        filtered = [line for line in raw_lines if any(word in line.lower() for word in ("temp", "fan", "package", "core", "composite"))]
        panels.append(Panel("\n".join(filtered[:8] or raw_lines[:6]), title="🌡️ Hardware Sensors", border_style="cyan"))
    if detail == "full" and data.get("extras"):
        panels.append(Panel(json.dumps(data["extras"], indent=2), title="Extras", border_style="white"))
    return panels


# ---------------------------------------------------------------------------
# COMPACT FORMAT
# ---------------------------------------------------------------------------


def render_compact(data: dict[str, Any]) -> None:
    """Render a dense borderless layout that does not truncate by columns."""
    lines: list[Text] = []
    info = _system_info(data)
    lines.append(Text(str(info.get("hostname", "")), style="bold green"))
    lines.append(_line("os", info.get("os")))
    lines.append(_line("kernel", info.get("kernel")))
    lines.append(_line("uptime", info.get("uptime")))
    lines.append(_line("shell", f"{info.get('shell', '')} ({info.get('terminal', '')})"))

    cpu = _cpu_info(data)
    lines.append(_line("cpu", f"{cpu.get('model', 'Unknown')} — {cpu.get('physical', '?')}c/{cpu.get('logical', '?')}t"))

    mem = _memory_info(data)
    lines.append(_line("mem", f"{mem.get('used', '?')}/{mem.get('total', '?')} ({mem.get('used_pct', '?')}%)"))
    lines.append(_line("swap", f"{mem.get('swap_used', '?')}/{mem.get('swap_total', '?')} ({mem.get('swap_pct', '?')}%)"))

    for disk in _disks(data):
        mount = disk.get("mountpoint", disk.get("mount", ""))
        fs = disk.get("fstype", disk.get("fs", ""))
        used = disk.get("used", "")
        if not used and disk.get("percent") is not None:
            used = f"{disk.get('percent')}%"
        size = disk.get("size", disk.get("total", ""))
        if isinstance(size, (int, float)):
            size = f"{size / (1024 ** 3):.1f}G"
        lines.append(_line(f"disk {mount}", f"{fs} {used}/{size}"))

    for iface in _network(data):
        status = iface.get("status", "")
        line = Text(f"  net {iface.get('name', '')} {iface.get('address', '')} ", style="cyan")
        line.append(str(status), style="green" if status == "UP" else "dim red")
        lines.append(line)

    if data.get("gpu"):
        gpu = data["gpu"]
        if isinstance(gpu, list):
            gpu = gpu[0] if gpu else {}
        lines.append(_line("gpu", f"{gpu.get('name', 'N/A')} (driver {gpu.get('driver', '?')})"))

    console.print(Group(*lines))


def _line(label: str, value: Any) -> Text:
    text = Text(f"  {label:<10}", style="cyan")
    text.append(str(value if value is not None else "N/A"))
    return text


def render(data: dict[str, Any], fmt: str = "full") -> None:
    """Single entry point for choosing a summary layout."""
    if fmt == "compact":
        render_compact(data)
    else:
        render_full(data)


def render_pretty(data: dict, detail: str = "brief", logo: Optional[str] = None):
    """Backward-compatible entry point used by the CLI."""
    console.rule("[bold cyan]System Summary")
    panels = _build_panels(data, detail)
    if logo:
        logo_renderable = Text.from_ansi(logo)
        grid = Table.grid(padding=(0, 2, 0, 0), expand=True)
        grid.add_column(no_wrap=True, vertical="top")
        grid.add_column(vertical="top", ratio=1)
        grid.add_row(logo_renderable, Group(*panels))
        console.print(grid)
    else:
        for panel in panels:
            console.print(panel)


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
