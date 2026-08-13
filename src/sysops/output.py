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
