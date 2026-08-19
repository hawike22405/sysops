import json
from typing import Optional

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _format_bytes(value) -> str:
    if not value:
        return "0 B"
    return f"{value / (1024 ** 3):.2f} GiB"


def _format_uptime(seconds) -> str:
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


def _build_panels(data: dict, detail: str) -> list:
    panels = []

    os_info = data.get("os", {})
    host = data.get("host", {})
    distro = os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform") or "Unknown"
    kernel = host.get("kernel") or "Unknown"
    kernel_version = host.get("kernel_version") or "Unknown"
    node = host.get("node") or "localhost"
    desktop = data.get("desktop", {})
    os_table = Table(show_header=False, box=box.MINIMAL, expand=True)
    os_table.add_column("Key", style="bold cyan", width=10)
    os_table.add_column("Value")
    os_table.add_row("OS", distro)
    os_table.add_row("Kernel", f"{kernel} ({kernel_version})")
    uptime = _format_uptime(data.get("uptime", {}).get("uptime_seconds"))
    os_table.add_row("Uptime", uptime)
    if desktop.get("de"):
        os_table.add_row("DE", desktop["de"])
    if desktop.get("wm"):
        os_table.add_row("WM", desktop["wm"])
    if desktop.get("terminal"):
        os_table.add_row("Terminal", desktop["terminal"])
    if desktop.get("shell"):
        os_table.add_row("Shell", desktop["shell"])

    panels.append(Panel(os_table, title=f"[bold green]{node}[/]", border_style="green"))

    cpu = data.get("cpu", {})
    cpu_table = Table(show_header=False, box=box.MINIMAL, expand=True)
    cpu_table.add_column("Key", style="bold yellow", width=10)
    cpu_table.add_column("Value")
    cpu_table.add_row("Model", cpu.get("model") or "Unknown")
    cores = f"{cpu.get('physical_cores', '?')} phys / {cpu.get('logical_cores', '?')} log"
    if cpu.get("freq_mhz"):
        cores += f" @ {cpu['freq_mhz']} MHz"
    cpu_table.add_row("Cores", cores)
    panels.append(Panel(cpu_table, title="[bold yellow]⚡ CPU Specs[/]", border_style="yellow"))

    mem = data.get("memory", {})
    mem_table = Table(show_header=False, box=box.MINIMAL, expand=True)
    mem_table.add_column("Key", style="bold magenta", width=10)
    mem_table.add_column("Value")
    total = mem.get("total_bytes")
    if total:
        used = mem.get("used_bytes") or 0
        swap_total = mem.get("swap_total") or 0
        swap_used = mem.get("swap_used") or 0
        mem_table.add_row("Total RAM", _format_bytes(total))
        mem_table.add_row("Used RAM", f"{_format_bytes(used)} ({mem.get('percent', 0)}%)")
        mem_table.add_row(
            "Swap",
            f"{_format_bytes(swap_used)} / {_format_bytes(swap_total)} ({mem.get('swap_percent', 0)}%)",
        )
    else:
        mem_table.add_row("Memory", "N/A")
    panels.append(Panel(mem_table, title="[bold magenta]🧠 Memory Usage[/]", border_style="magenta"))

    disks = data.get("disks", {}).get("partitions", [])
    disk_table = Table("Device", "Mount", "FS", "Size", "Used", box=box.SIMPLE, expand=True)
    for part in disks:
        total = part.get("total")
        size = f"{total / (1024 ** 3):.1f}G" if total else "?"
        used = f"{part.get('percent')}%" if part.get("percent") is not None else "?"
        disk_table.add_row(
            part.get("device") or "?",
            part.get("mountpoint") or "?",
            part.get("fstype") or "?",
            size,
            used,
        )
    panels.append(Panel(disk_table, title="[bold red]💾 Storage & Disks[/]", border_style="red"))

    net = data.get("network", {}).get("interfaces", {})
    net_table = Table("Interface", "Address", "Status", box=box.SIMPLE, expand=True)
    for name, info in list(net.items())[:8]:
        addresses = [a.get("address") for a in info.get("addresses", []) if a.get("address")]
        address = addresses[0] if addresses else "-"
        if len(addresses) > 1:
            address += f" (+{len(addresses) - 1})"
        status = "[green]UP[/]" if info.get("is_up") else "[red]DOWN[/]"
        net_table.add_row(name, address, status)
    panels.append(Panel(net_table, title="[bold green]🌐 Network Interfaces[/]", border_style="green"))

    gpu = data.get("gpu")
    if isinstance(gpu, dict) and gpu:
        gpu_table = Table(show_header=False, box=box.MINIMAL, expand=True)
        gpu_table.add_column("Key", style="bold blue", width=10)
        gpu_table.add_column("Value")
        for key, value in gpu.items():
            if value:
                gpu_table.add_row(str(key).capitalize(), str(value))
        panels.append(Panel(gpu_table, title="[bold blue]🎮 GPU Information[/]", border_style="blue"))

    sensors = data.get("sensors")
    if isinstance(sensors, dict) and sensors.get("raw"):
        raw_lines = [line.strip() for line in sensors["raw"].splitlines() if line.strip()]
        filtered = [
            line for line in raw_lines
            if any(word in line.lower() for word in ("temp", "fan", "package", "core", "composite"))
        ]
        panels.append(
            Panel(
                "\n".join(filtered[:8] or raw_lines[:6]),
                title="[bold cyan]🌡️ Hardware Sensors[/]",
                border_style="cyan",
            )
        )

    if detail == "full":
        extras = data.get("extras")
        if extras:
            panels.append(
                Panel(
                    json.dumps(extras, indent=2),
                    title="[bold white]Extras[/]",
                    border_style="white",
                )
            )

    return panels


def render_pretty(data: dict, detail: str = "brief", logo: Optional[str] = None):
    console.rule("[bold cyan]System Summary")

    if logo:
        logo_renderable = Text.from_ansi(logo)
        grid = Table.grid(padding=(0, 2, 0, 0), expand=True)
        grid.add_column(no_wrap=True, vertical="top")
        grid.add_column(vertical="top", ratio=1)
        panels = _build_panels(data, detail)
        grid.add_row(logo_renderable, Group(*panels))
        console.print(grid)
    else:
        for panel in _build_panels(data, detail):
            console.print(panel)


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)

