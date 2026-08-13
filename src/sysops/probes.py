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
