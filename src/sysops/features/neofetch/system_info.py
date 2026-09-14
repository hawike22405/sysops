"""Fast system-information gathering for the neofetch display.

Prefers reading directly from ``/proc`` and ``/sys`` over spawning
subprocesses wherever possible, and wraps every probe in a try/except
so that missing data never crashes the display.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None  # type: ignore[assignment]

try:
    import distro as _distro
except Exception:  # pragma: no cover
    _distro = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------

def _safe(fn, default: Any = "N/A") -> Any:
    """Run *fn* and return its result, or *default* on any error."""
    try:
        result = fn()
        return result if result is not None else default
    except Exception:
        return default


def _read_file(path: str) -> str | None:
    """Read first line of *path* (stripped), or ``None``."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.readline().strip()
    except Exception:
        return None


def _read_file_full(path: str) -> str | None:
    """Read entire file content (stripped), or ``None``."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().strip()
    except Exception:
        return None


def _run_cmd(cmd: list[str], timeout: float = 2.0) -> str | None:
    """Run *cmd* and return its stdout, or ``None``."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# OS / Distro
# ---------------------------------------------------------------------------

def _detect_distro_id() -> str:
    """Return a short lowercase distro identifier (e.g. 'arch', 'ubuntu')."""
    if platform.system() == "Windows":
        return "windows"
    if platform.system() == "Darwin":
        return "macos"
    if _distro:
        return _distro.id() or "linux"
    data = _read_file_full("/etc/os-release")
    if data:
        for line in data.splitlines():
            if line.startswith("ID="):
                return line.split("=", 1)[1].strip().strip('"').lower()
    return "linux"


def _get_os_name() -> str:
    """Full pretty name of the OS."""
    if platform.system() == "Windows":
        return f"Windows {platform.release()} {platform.version()}"
    if platform.system() == "Darwin":
        ver = platform.mac_ver()[0]
        return f"macOS {ver}" if ver else "macOS"
    if _distro:
        return _distro.name(pretty=True) or "Linux"
    data = _read_file_full("/etc/os-release")
    if data:
        for line in data.splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    return "Linux"


def _get_architecture() -> str:
    return platform.machine() or "unknown"


# ---------------------------------------------------------------------------
# Host / Machine
# ---------------------------------------------------------------------------

_DMI_PATHS = [
    ("/sys/devices/virtual/dmi/id/product_name", "product_name"),
    ("/sys/devices/virtual/dmi/id/product_version", "product_version"),
    ("/sys/devices/virtual/dmi/id/board_vendor", "board_vendor"),
    ("/sys/devices/virtual/dmi/id/board_name", "board_name"),
]


def _get_host() -> str:
    """Machine / motherboard model."""
    if platform.system() == "Darwin":
        model = _run_cmd(["sysctl", "-n", "hw.model"])
        return model or "Apple Mac"
    if platform.system() == "Windows":
        out = _run_cmd(["wmic", "computersystem", "get", "model"])
        if out:
            lines = [l.strip() for l in out.splitlines() if l.strip() and l.strip().lower() != "model"]
            if lines:
                return lines[0]
        return platform.node()
    # Linux: read from sysfs (no subprocess needed)
    product = _read_file("/sys/devices/virtual/dmi/id/product_name")
    version = _read_file("/sys/devices/virtual/dmi/id/product_version")

    _IGNORE = {"", "to be filled by o.e.m.", "system product name", "default string", "not applicable", "none"}

    def _is_serial(val: str) -> bool:
        """Heuristic: long alphanumeric strings with no spaces are serial numbers."""
        return len(val) > 12 and " " not in val and val.isalnum()

    if product and product.lower() not in _IGNORE:
        parts = [product]
        if version and version.lower() not in _IGNORE and not _is_serial(version):
            parts.append(version)
        return " ".join(parts)
    vendor = _read_file("/sys/devices/virtual/dmi/id/board_vendor")
    board = _read_file("/sys/devices/virtual/dmi/id/board_name")
    if board:
        parts = []
        if vendor:
            parts.append(vendor)
        parts.append(board)
        return " ".join(parts)
    return "N/A"


# ---------------------------------------------------------------------------
# Kernel
# ---------------------------------------------------------------------------

def _get_kernel() -> str:
    return platform.release()


# ---------------------------------------------------------------------------
# Uptime
# ---------------------------------------------------------------------------

def _get_uptime() -> str:
    """Formatted as 'Xd Yh Zm'."""
    seconds: int | None = None
    raw = _read_file("/proc/uptime")
    if raw:
        try:
            seconds = int(float(raw.split()[0]))
        except (ValueError, IndexError):
            pass
    if seconds is None and psutil:
        try:
            import time
            seconds = int(time.time() - psutil.boot_time())
        except Exception:
            pass
    if seconds is None:
        return "N/A"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts: list[str] = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

_PKG_MANAGERS: list[tuple[str, list[str]]] = [
    ("pacman",  ["pacman", "-Qq"]),
    ("dpkg",    ["dpkg-query", "-f", "${binary:Package}\\n", "-W"]),
    ("rpm",     ["rpm", "-qa"]),
    ("flatpak", ["flatpak", "list"]),
    ("snap",    ["snap", "list"]),
    ("brew",    ["brew", "list", "--formula"]),
    ("nix",     ["nix-env", "-q"]),
    ("apk",     ["apk", "list", "--installed"]),
    ("xbps",    ["xbps-query", "-l"]),
    ("eopkg",   ["eopkg", "li"]),
    ("emerge",  ["qlist", "-I"]),
]


def _count_packages() -> str:
    """Count installed packages for every detected package manager."""
    results: list[str] = []
    for name, cmd in _PKG_MANAGERS:
        if not shutil.which(cmd[0]):
            continue
        out = _run_cmd(cmd, timeout=5.0)
        if out is not None:
            count = len([l for l in out.splitlines() if l.strip()])
            results.append(f"{count} ({name})")
    return ", ".join(results) if results else "N/A"


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

def _get_shell() -> str:
    """Detect the active shell and its version."""
    if platform.system() == "Windows":
        if "PSModulePath" in os.environ:
            ver = _run_cmd(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"])
            return f"PowerShell {ver}" if ver else "PowerShell"
        return os.environ.get("ComSpec", "cmd.exe").rsplit("\\", 1)[-1]
    shell_path = os.environ.get("SHELL", "")
    if not shell_path:
        return "N/A"
    shell_name = Path(shell_path).name
    # Try to get the version
    ver_cmd: list[str] | None = None
    if shell_name in ("bash", "zsh", "fish", "dash", "ksh"):
        ver_cmd = [shell_path, "--version"]
    elif shell_name == "tcsh":
        ver_cmd = [shell_path, "--version"]
    if ver_cmd:
        raw = _run_cmd(ver_cmd, timeout=2.0) or ""
        # Extract version number from the first line
        first_line = raw.splitlines()[0] if raw else ""
        match = re.search(r"(\d+\.\d+[\.\d]*)", first_line)
        if match:
            return f"{shell_name} {match.group(1)}"
    return shell_name


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def _get_resolution() -> str:
    """Detect screen resolution(s)."""
    # Try xrandr first (X11)
    if shutil.which("xrandr"):
        out = _run_cmd(["xrandr", "--current"])
        if out:
            resolutions: list[str] = []
            for line in out.splitlines():
                match = re.search(r"(\d+x\d+)\+\d+\+\d+", line)
                if match:
                    resolutions.append(match.group(1))
            if resolutions:
                return ", ".join(resolutions)
    # Try xdpyinfo
    if shutil.which("xdpyinfo"):
        out = _run_cmd(["xdpyinfo"])
        if out:
            match = re.search(r"dimensions:\s+(\d+x\d+)", out)
            if match:
                return match.group(1)
    # Wayland: try wlr-randr or swaymsg
    if shutil.which("wlr-randr"):
        out = _run_cmd(["wlr-randr"])
        if out:
            resolutions = re.findall(r"(\d+x\d+)\s+px", out)
            if resolutions:
                return ", ".join(resolutions)
    if shutil.which("swaymsg"):
        out = _run_cmd(["swaymsg", "-t", "get_outputs"])
        if out:
            matches = re.findall(r'"current_mode":\s*\{[^}]*"width":\s*(\d+)[^}]*"height":\s*(\d+)', out)
            if matches:
                return ", ".join(f"{w}x{h}" for w, h in matches)
    # macOS
    if platform.system() == "Darwin" and shutil.which("system_profiler"):
        out = _run_cmd(["system_profiler", "SPDisplaysDataType"])
        if out:
            match = re.search(r"Resolution:\s*(.+)", out)
            if match:
                return match.group(1).strip()
    return "N/A"


# ---------------------------------------------------------------------------
# DE / WM
# ---------------------------------------------------------------------------

def _get_de() -> str:
    """Detect the Desktop Environment."""
    if platform.system() == "Windows":
        return "Windows Desktop"
    if platform.system() == "Darwin":
        return "Aqua"
    de = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION")
    return de if de else "N/A"


def _get_wm() -> str:
    """Detect the Window Manager (X11 or Wayland)."""
    if platform.system() == "Windows":
        return "DWM"
    if platform.system() == "Darwin":
        return "Quartz Compositor"
    # Check Wayland compositors
    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    if wayland_display:
        # Hyprland
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return "Hyprland"
        # Sway
        if os.environ.get("SWAYSOCK"):
            return "Sway"
        # Generic Wayland
        xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in xdg:
            return "Mutter (Wayland)"
        if "kde" in xdg or "plasma" in xdg:
            return "KWin (Wayland)"
        return "Wayland Compositor"
    # X11: try wmctrl
    if shutil.which("wmctrl"):
        out = _run_cmd(["wmctrl", "-m"])
        if out:
            for line in out.splitlines():
                if line.startswith("Name:"):
                    return line.split(":", 1)[1].strip()
    # X11: try xprop on root window
    if shutil.which("xprop"):
        out = _run_cmd(["xprop", "-root", "-notype", "_NET_WM_NAME", "_NET_SUPPORTING_WM_CHECK"])
        if out:
            match = re.search(r'_NET_WM_NAME\s*=\s*"(.+)"', out)
            if match:
                return match.group(1)
    # Common env vars
    for var in ("I3SOCK",):
        if os.environ.get(var):
            return "i3"
    return "N/A"


# ---------------------------------------------------------------------------
# Terminal
# ---------------------------------------------------------------------------

def _get_terminal() -> str:
    """Detect the active terminal emulator."""
    # Windows Terminal
    if os.environ.get("WT_SESSION"):
        return "Windows Terminal"
    # TERM_PROGRAM is set by many terminals (iTerm2, vscode, Alacritty, etc.)
    term_prog = os.environ.get("TERM_PROGRAM")
    if term_prog:
        ver = os.environ.get("TERM_PROGRAM_VERSION", "")
        return f"{term_prog} {ver}".strip() if ver else term_prog
    # Kitty
    if os.environ.get("KITTY_PID"):
        return "kitty"
    # Alacritty sets TERM=alacritty on some setups
    term = os.environ.get("TERM", "")
    if "alacritty" in term.lower():
        return "Alacritty"
    # Foot
    if "foot" in term.lower():
        return "foot"
    # Try to read the parent process name (Linux)
    if platform.system() == "Linux":
        ppid = os.getppid()
        try:
            comm = _read_file(f"/proc/{ppid}/comm")
            if comm and comm not in ("bash", "zsh", "fish", "sh", "dash", "python3", "python"):
                return comm
            # Go one level up
            stat = _read_file_full(f"/proc/{ppid}/status")
            if stat:
                for line in stat.splitlines():
                    if line.startswith("PPid:"):
                        gppid = line.split(":")[1].strip()
                        gcomm = _read_file(f"/proc/{gppid}/comm")
                        if gcomm and gcomm not in ("bash", "zsh", "fish", "sh", "dash", "python3", "python", "systemd", "init"):
                            return gcomm
        except Exception:
            pass
    # Conhost fallback for Windows
    if platform.system() == "Windows":
        return "Conhost"
    return os.environ.get("TERM", "N/A")


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------

def _get_cpu() -> str:
    """CPU model, core count, and max frequency."""
    model = None
    if platform.system() == "Linux":
        raw = _read_file_full("/proc/cpuinfo")
        if raw:
            for line in raw.splitlines():
                if line.lower().startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
    elif platform.system() == "Darwin":
        model = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
    elif platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            model = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except Exception:
            model = platform.processor()
    if not model:
        model = platform.processor() or "N/A"
    # Core count
    cores: str = ""
    if psutil:
        physical = psutil.cpu_count(logical=False)
        logical = psutil.cpu_count(logical=True)
        if physical and logical:
            cores = f" ({physical}C/{logical}T)"
        elif logical:
            cores = f" ({logical}T)"
    # Frequency
    freq_str = ""
    if psutil:
        try:
            freq = psutil.cpu_freq()
            if freq and freq.max:
                ghz = freq.max / 1000
                freq_str = f" @ {ghz:.2f} GHz"
            elif freq and freq.current:
                ghz = freq.current / 1000
                freq_str = f" @ {ghz:.2f} GHz"
        except Exception:
            pass
    return f"{model}{cores}{freq_str}"


# ---------------------------------------------------------------------------
# GPU
# ---------------------------------------------------------------------------

def _get_gpu() -> str:
    """GPU model name(s)."""
    # nvidia-smi
    out = _run_cmd(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"])
    if out:
        gpus = [l.strip() for l in out.splitlines() if l.strip()]
        return ", ".join(gpus)
    # lspci
    if shutil.which("lspci"):
        out = _run_cmd(["lspci"])
        if out:
            gpus: list[str] = []
            for line in out.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    desc = line.split(":", 2)[-1].strip()
                    gpus.append(desc)
            if gpus:
                return ", ".join(gpus)
    # macOS
    if platform.system() == "Darwin" and shutil.which("system_profiler"):
        out = _run_cmd(["system_profiler", "SPDisplaysDataType"])
        if out:
            match = re.search(r"Chipset Model:\s*(.+)", out)
            if match:
                return match.group(1).strip()
    # sysfs DRM (fallback for Linux without lspci)
    drm_base = Path("/sys/class/drm")
    if drm_base.is_dir():
        cards: list[str] = []
        for card_dir in sorted(drm_base.iterdir()):
            name_file = card_dir / "device" / "label"
            if not name_file.exists():
                name_file = card_dir / "device" / "product_name"
            if name_file.exists():
                name = _read_file(str(name_file))
                if name and name not in cards:
                    cards.append(name)
        if cards:
            return ", ".join(cards)
    return "N/A"


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

def _get_memory() -> str:
    """Used / Total RAM in MiB or GiB."""
    if psutil:
        vm = psutil.virtual_memory()
        used = vm.used
        total = vm.total
    elif os.path.exists("/proc/meminfo"):
        info: dict[str, int] = {}
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val_parts = parts[1].strip().split()
                        if val_parts:
                            try:
                                info[key] = int(val_parts[0]) * 1024  # kB → bytes
                            except ValueError:
                                pass
            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", info.get("MemFree", 0))
            used = total - available
        except Exception:
            return "N/A"
    else:
        return "N/A"
    def _fmt(b: int) -> str:
        if b >= 1024 ** 3:
            return f"{b / (1024 ** 3):.2f} GiB"
        return f"{b / (1024 ** 2):.0f} MiB"
    return f"{_fmt(used)} / {_fmt(total)}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def gather_system_info() -> dict[str, str]:
    """Gather all system metrics and return them as an ordered dict.

    Every value is a string ready for display.  Entries whose value is
    ``"N/A"`` can be omitted by the layout renderer if desired.
    """
    info: dict[str, str] = {}
    info["distro_id"] = _safe(_detect_distro_id, "linux")
    info["OS"] = f"{_safe(_get_os_name)} {_safe(_get_architecture)}"
    info["Host"] = _safe(_get_host)
    info["Kernel"] = _safe(_get_kernel)
    info["Uptime"] = _safe(_get_uptime)
    info["Packages"] = _safe(_count_packages)
    info["Shell"] = _safe(_get_shell)
    info["Resolution"] = _safe(_get_resolution)
    info["DE"] = _safe(_get_de)
    info["WM"] = _safe(_get_wm)
    info["Terminal"] = _safe(_get_terminal)
    info["CPU"] = _safe(_get_cpu)
    info["GPU"] = _safe(_get_gpu)
    info["Memory"] = _safe(_get_memory)
    return info
