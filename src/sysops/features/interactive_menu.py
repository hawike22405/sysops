#!/usr/bin/env python3
"""Live terminal dashboard for quick system statistics."""

import os
import platform
import select
import shutil
import subprocess
import sys
import time

THEMES = {
    "default": {"header": "\033[1;36m", "label": "\033[0;37m", "value": "\033[1;37m", "accent": "\033[1;33m", "reset": "\033[0m"},
    "dark": {"header": "\033[1;35m", "label": "\033[0;90m", "value": "\033[1;97m", "accent": "\033[1;34m", "reset": "\033[0m"},
    "mono": {"header": "\033[1;37m", "label": "\033[0;37m", "value": "\033[1;37m", "accent": "\033[1;37m", "reset": "\033[0m"},
}
THEME_ORDER = list(THEMES)


def _run(command):
    try:
        return subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL).strip() or "N/A"
    except Exception:
        return "N/A"


def get_basic_stats():
    uname = platform.uname()
    return {
        "Hostname": uname.node,
        "OS": f"{uname.system} {uname.release}",
        "Architecture": uname.machine,
        "CPU cores": str(os.cpu_count() or "N/A"),
        "Uptime": _run("uptime -p 2>/dev/null || uptime"),
    }


def get_hidden_stats():
    return {
        "Load average": _run("cat /proc/loadavg 2>/dev/null"),
        "Memory": _run("free -h 2>/dev/null | awk 'NR==2{print $3\"/\"$2}'"),
        "Swap": _run("free -h 2>/dev/null | awk 'NR==3{print $3\"/\"$2}'"),
        "Disk (/)": _run("df -h / 2>/dev/null | awk 'NR==2{print $3\"/\"$2\" (\"$5\")\"}'"),
        "Processes": _run("ps -e --no-headers 2>/dev/null | wc -l"),
        "Kernel": _run("uname -r"),
    }


def copy_to_clipboard(text):
    candidates = [
        ("pbcopy", []),
        ("xclip", ["-selection", "clipboard"]),
        ("xsel", ["--clipboard", "--input"]),
        ("wl-copy", []),
        ("clip.exe", []),
    ]
    for binary, args in candidates:
        path = shutil.which(binary)
        if path:
            try:
                subprocess.run([path, *args], input=text, text=True, check=True)
                return True, binary
            except (OSError, subprocess.SubprocessError):
                pass
    return False, None


def _getch(timeout=0.5):
    """Read one key without Enter on POSIX and Windows terminals."""
    if os.name == "nt":
        import msvcrt
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                return msvcrt.getwch()
            time.sleep(0.05)
        return None

    import termios
    import tty
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        return sys.stdin.read(1) if ready else None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _render(theme_name, show_hidden, message=""):
    theme = THEMES[theme_name]
    print("\033[2J\033[H", end="")
    print(f"{theme['header']}=== SysOps Interactive Dashboard ==={theme['reset']}")
    print(f"{theme['label']}Theme:{theme['reset']} {theme['accent']}{theme_name}{theme['reset']}   "
          f"{theme['label']}Hidden stats:{theme['reset']} {theme['accent']}{'ON' if show_hidden else 'OFF'}{theme['reset']}\n")

    stats = get_basic_stats()
    if show_hidden:
        stats.update(get_hidden_stats())

    lines = []
    for key, value in stats.items():
        print(f"{theme['label']}{key:<18}{theme['reset']} {theme['value']}{value}{theme['reset']}")
        lines.append(f"{key}: {value}")

    print(f"\n{theme['label']}[h]{theme['reset']} hidden  "
          f"{theme['label']}[t]{theme['reset']} theme  "
          f"{theme['label']}[c]{theme['reset']} copy  "
          f"{theme['label']}[r]{theme['reset']} refresh  "
          f"{theme['label']}[q]{theme['reset']} quit")
    if message:
        print(f"\n{theme['accent']}{message}{theme['reset']}")
    return "\n".join(lines)


def run_interactive_menu():
    """Run the dashboard until the user presses ``q`` or Ctrl+C."""
    theme_name = "default"
    show_hidden = False
    message = ""
    try:
        while True:
            clip_text = _render(theme_name, show_hidden, message)
            message = ""
            key = _getch(timeout=2.0)
            if key is None:
                continue
            key = key.lower()
            if key == "q":
                print("\nExiting interactive dashboard.")
                return
            if key == "h":
                show_hidden = not show_hidden
            elif key == "t":
                theme_name = THEME_ORDER[(THEME_ORDER.index(theme_name) + 1) % len(THEME_ORDER)]
            elif key == "c":
                ok, backend = copy_to_clipboard(clip_text)
                message = f"Copied system info via {backend}." if ok else "Clipboard backend not found."
            elif key == "r":
                message = "Refreshed."
    except KeyboardInterrupt:
        print("\nInterrupted.")


if __name__ == "__main__":
    run_interactive_menu()
