import json
from typing import Optional

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _build_panels(data: dict, detail: str) -> list:
    """Build system-information panels without printing them."""
    panels = []

    os_info = data.get("os", {})
    host = data.get("host", {})
    distro = os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform")
    top = f"{distro} — {host.get('kernel')} ({host.get('kernel_version')})"
    panels.append(Panel(top, title=f"[green]{host.get('node')}", expand=False))

    cpu = data.get("cpu", {})
    t = Table(show_header=False, box=box.MINIMAL)
    t.add_column("k")
    t.add_column("v")
    t.add_row("CPU", cpu.get("model") or "Unknown")
    cores = f"{cpu.get('physical_cores', '?')} phys / {cpu.get('logical_cores', '?')} log"
    if cpu.get("freq_mhz"):
        cores += f" @ {cpu.get('freq_mhz')} MHz"
    t.add_row("Cores", cores)
    panels.append(Panel(t, title="CPU", expand=False))

    mem = data.get("memory", {})
    t = Table(show_header=False, box=box.MINIMAL)
    t.add_column("k")
    t.add_column("v")
    total = mem.get("total_bytes")
    if total:
        gb = total / (1024**3)
        t.add_row("Total", f"{gb:.2f} GiB")
        used = mem.get("used_bytes")
        percent = mem.get("percent")
        if used is not None:
            t.add_row("Used", f"{used / (1024**3):.2f} GiB ({percent}%)")
        swap_total = mem.get("swap_total") or 0
        t.add_row("Swap", f"{swap_total / (1024**3):.2f} GiB ({mem.get('swap_percent')}%)")
    else:
        t.add_row("Memory", "Unknown")
    panels.append(Panel(t, title="Memory", expand=False))

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
    panels.append(Panel(dt, title="Disks", expand=False))

    net = data.get("network", {}).get("interfaces", {})
    nt = Table("Interface", "Addresses", "Up/Speed", box=box.SIMPLE)
    for name, info in net.items():
        addrs = ", ".join(a.get("address") for a in info.get("addresses", []) if a.get("address"))
        up = "up" if info.get("is_up") else "down"
        speed = f"{info.get('speed_mbps')}Mbps" if info.get("speed_mbps") else ""
        nt.add_row(name, addrs or "-", f"{up} {speed}")
    panels.append(Panel(nt, title="Network", expand=False))

    gpu = data.get("gpu")
    if gpu:
        gtxt = "\n".join(f"{k}: {v}" for k, v in gpu.items() if v)
        panels.append(Panel(gtxt or "No GPU info", title="GPU", expand=False))

    sensors = data.get("sensors")
    if sensors:
        panels.append(Panel(sensors.get("raw", ""), title="Sensors (raw)", expand=False))

    if detail == "full":
        extras = data.get("extras")
        panels.append(Panel(json.dumps(extras, indent=2), title="Extras", expand=False))

    return panels


def render_pretty(data: dict, detail: str = "brief", logo: Optional[str] = None):
    """Print system information, optionally with a logo beside the panels."""
    console.rule("[bold cyan]System Summary")
    panels = _build_panels(data, detail)

    if not logo:
        for panel in panels:
            console.print(panel)
        return

    logo_renderable = Text.from_ansi(logo)
    grid = Table.grid(padding=(0, 2, 0, 0))
    grid.add_column(no_wrap=True, vertical="top")
    grid.add_column(vertical="top")
    grid.add_row(logo_renderable, Group(*panels))
    console.print(grid)


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
