import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

SYSOPS_ASCII = r"""
 [bold cyan]  ███████╗██╗██╗   ██╗██████╗ ███████╗[/bold cyan]
 [bold cyan]  ██╔════╝╚██╗██║   ██║██╔══██╗██╔════╝[/bold cyan]
 [bold cyan]  ███████╗ ╚████║   ██║██████╔╝███████╗[/bold cyan]
 [bold cyan]  ╚════██║  ╚███║   ██║██╔═══╝ ╚════██║[/bold cyan]
 [bold cyan]  ███████║   ██║╚█████╔╝██║     ███████║[/bold cyan]
 [bold cyan]  ╚══════╝   ╚═╝ ╚════╝ ╚═╝     ╚══════╝[/bold cyan]
"""


def _format_bytes(b: float) -> str:
    if not b:
        return "0 B"
    gb = b / (1024 ** 3)
    return f"{gb:.2f} GiB"


def _format_uptime(seconds) -> str:
    if not seconds:
        return "N/A"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def render_pretty(data: dict, detail="brief"):
    # 1. Large ASCII Banner
    console.print(SYSOPS_ASCII)

    # 2. System Overview Banner
    os_info = data.get("os", {})
    host = data.get("host", {})
    uptime = data.get("uptime", {}).get("uptime_seconds")

    distro = os_info.get("name") or os_info.get("pretty_name") or os_info.get("platform", "Linux")
    hostname = host.get("node", "localhost")
    kernel = host.get("kernel", "")
    machine = host.get("machine", "")
    uptime_str = _format_uptime(uptime)

    header_text = f"[bold green]Host:[/] {hostname}   [bold green]OS:[/] {distro}   [bold green]Kernel:[/] {kernel} ({machine})   [bold green]Uptime:[/] {uptime_str}"
    console.print(Panel(header_text, style="cyan", expand=True))

    # Grid for Side-by-Side Panels (CPU & Memory)
    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)

    # CPU Panel
    cpu = data.get("cpu", {})
    cpu_t = Table(show_header=False, box=box.SIMPLE, expand=True)
    cpu_t.add_column("Key", style="bold yellow", width=10)
    cpu_t.add_column("Value", style="white")
    cpu_t.add_row("Model", cpu.get("model") or "Unknown")
    cores = f"{cpu.get('physical_cores', '?')} phys / {cpu.get('logical_cores', '?')} log"
    if cpu.get("freq_mhz"):
        cores += f" @ {cpu.get('freq_mhz')} MHz"
    cpu_t.add_row("Cores", cores)
    cpu_panel = Panel(cpu_t, title="[bold yellow]⚡ CPU Specs[/]", border_style="yellow")

    # Memory Panel
    mem = data.get("memory", {})
    mem_t = Table(show_header=False, box=box.SIMPLE, expand=True)
    mem_t.add_column("Key", style="bold magenta", width=10)
    mem_t.add_column("Value", style="white")
    total = mem.get("total_bytes")
    if total:
        mem_t.add_row("Total RAM", _format_bytes(total))
        used = mem.get("used_bytes", 0)
        pct = mem.get("percent", 0)
        mem_t.add_row("Used RAM", f"{_format_bytes(used)} ({pct}%)")
        swap_t = mem.get("swap_total", 0)
        swap_u = mem.get("swap_used", 0)
        swap_p = mem.get("swap_percent", 0)
        mem_t.add_row("Swap", f"{_format_bytes(swap_u)} / {_format_bytes(swap_t)} ({swap_p}%)")
    else:
        mem_t.add_row("Memory", "N/A")
    mem_panel = Panel(mem_t, title="[bold magenta]🧠 Memory Usage[/]", border_style="magenta")

    grid.add_row(cpu_panel, mem_panel)
    console.print(grid)

    # Grid for GPU & Network Panels
    grid2 = Table.grid(expand=True)
    grid2.add_column(ratio=1)
    grid2.add_column(ratio=1)

    # GPU Panel
    gpu_data = data.get("gpu")
    if gpu_data and isinstance(gpu_data, dict):
        gpu_t = Table(show_header=False, box=box.SIMPLE, expand=True)
        gpu_t.add_column("Key", style="bold blue", width=10)
        gpu_t.add_column("Value", style="white")
        for k, v in gpu_data.items():
            if v:
                gpu_t.add_row(k.capitalize(), str(v))
        gpu_panel = Panel(gpu_t, title="[bold blue]🎮 GPU Information[/]", border_style="blue")
    else:
        gpu_panel = Panel("No GPU info detected", title="[bold blue]🎮 GPU Information[/]", border_style="blue")

    # Network Panel
    net = data.get("network", {}).get("interfaces", {})
    net_t = Table("Interface", "Addresses", "Status", box=box.SIMPLE, expand=True)
    net_t.columns[0].header_style = "bold green"
    net_t.columns[1].header_style = "bold green"
    net_t.columns[2].header_style = "bold green"
    for name, info in list(net.items())[:4]:
        addrs_list = [a.get("address") for a in info.get("addresses", []) if a.get("address")]
        addrs = addrs_list[0] if addrs_list else "-"
        if len(addrs_list) > 1:
            addrs += f" (+{len(addrs_list)-1})"
        up = "[green]UP[/]" if info.get("is_up") else "[red]DOWN[/]"
        net_t.add_row(name, addrs, up)
    net_panel = Panel(net_t, title="[bold green]🌐 Network Interfaces[/]", border_style="green")

    grid2.add_row(gpu_panel, net_panel)
    console.print(grid2)

    # Disks Panel
    disks = data.get("disks", {}).get("partitions", [])
    dt = Table("Device", "Mount Point", "FS Type", "Total Size", "Used %", box=box.SIMPLE, expand=True)
    dt.columns[0].header_style = "bold red"
    dt.columns[1].header_style = "bold red"
    dt.columns[2].header_style = "bold red"
    dt.columns[3].header_style = "bold red"
    dt.columns[4].header_style = "bold red"
    for p in disks:
        tot = p.get("total")
        size = f"{tot / (1024**3):.1f}G" if tot else "?"
        used = f"{p.get('percent')}%" if p.get("percent") is not None else "?"
        dt.add_row(p.get("device") or "?", p.get("mountpoint") or "?", p.get("fstype") or "?", size, used)
    console.print(Panel(dt, title="[bold red]💾 Storage & Disks[/]", border_style="red"))

    # Sensors Panel (if present)
    sensors_data = data.get("sensors")
    if sensors_data and sensors_data.get("raw"):
        raw_lines = [line.strip() for line in sensors_data["raw"].splitlines() if line.strip()]
        clean_lines = []
        for line in raw_lines:
            if any(k in line.lower() for k in ("temp", "fan", "package", "core", "composite")):
                clean_lines.append(line)
        sens_text = "\n".join(clean_lines[:8]) if clean_lines else "\n".join(raw_lines[:6])
        console.print(Panel(sens_text, title="[bold cyan]🌡️ Hardware Sensors[/]", border_style="cyan"))

    if detail == "full":
        extras = data.get("extras")
        if extras:
            console.print(Panel(json.dumps(extras, indent=2), title="[bold white]Extras[/]", border_style="white"))


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)

