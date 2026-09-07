"""Cross-platform animated ASCII OS logo flipbook."""

from __future__ import annotations

import os
import platform
import shutil
import sys
import time
from dataclasses import dataclass

CSI = "\x1b["
RESET = f"{CSI}0m"
HIDE_CURSOR = f"{CSI}?25l"
SHOW_CURSOR = f"{CSI}?25h"
CURSOR_HOME = f"{CSI}H"
ERASE_DOWN = f"{CSI}J"
DEFAULT_FPS = 12.0
MIN_WIDTH = 16


@dataclass(frozen=True)
class LogoFrames:
    name: str
    frames: tuple[str, ...]


# Eight pre-rendered poses per supported OS. All frames in one animation have
# identical row counts, so the renderer never changes vertical footprint.
LOGOS: dict[str, LogoFrames] = {
    "Windows": LogoFrames("Windows", (
        "   ██████  ██████   \n   ██  ██  ██  ██   \n   ██  ██  ██  ██   \n   ██████  ██████   \n   ██████  ██████   \n   ██  ██  ██  ██   \n   ██  ██  ██  ██   \n   ██████  ██████   \n   \\          //    \n    \\        //     \n     \\______/      ",
        "    ██████  █████   \n    ██  ██  ██  ██  \n    ██  ██  ██  ██  \n    ██████  █████   \n    ██████  █████   \n    ██  ██  ██  ██  \n    ██  ██  ██  ██  \n    ██████  █████   \n      \\      //     \n       \\____//      \n         \\/         ",
        "        ████        \n        ████        \n        ████        \n        ████        \n        ████        \n        ████        \n        ████        \n        ████        \n        ██          \n        ██          \n        ██          ",
        "   █████  ██████    \n   ██  ██ ██  ███    \n   ██  ██ ██  ███    \n   █████  ██████     \n   █████  ██████     \n   ██  ██ ██  ███    \n   ██  ██ ██  ███    \n   █████  ██████     \n    \\        //     \n     \\______/       \n                     ",
        "   ██████  ██████   \n   ██  ██  ██  ██   \n   ██  ██  ██  ██   \n   ██████  ██████   \n   ██████  ██████   \n   ██  ██  ██  ██   \n   ██  ██  ██  ██   \n   ██████  ██████   \n    //        \\    \n   //____    _\\    \n   \\________/      ",
        "    █████  ██████   \n    ██  █  ██  ██   \n    ██  █  ██  ██   \n    █████  ██████   \n    █████  ██████   \n    ██  █  ██  ██   \n    ██  █  ██  ██   \n    █████  ██████   \n     //      \\     \n    //        \\    \n   /__________\\    ",
        "       ████         \n       ████         \n       ████         \n       ████         \n       ████         \n       ████         \n       ████         \n       ████         \n       ██           \n       ██           \n       ██           ",
        "    █████  ██████   \n   █████  ██████    \n   ██  ██ ██  ██    \n   █████  ██████    \n   █████  ██████    \n   ██  ██ ██  ██    \n   █████  ██████    \n    ████  ████      \n      //     \\      \n     //_______\\     \n    /__________\\    ",
    )),
    "Linux": LogoFrames("Linux", (
        "       .--.         \n      |o_o |        \n      |:_/ |        \n     //   \\ \\       \n    (|     | )      \n   /'\\_   _/`\\     \n   \\___)=(___/     \n      /____\\        \n     /______\\       \n       TUX           ",
        "         .--.       \n        /o_o |       \n        |:_/ |       \n       //   /        \n      (|   /         \n     /'__/          \n     \\___           \n       /__           \n      /___           \n       TX            ",
        "          .-.       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          |_|       ",
        "         .--.       \n        |o_o/       \n        |:_/        \n        /  \\       \n       /  |)        \n      /_   \\       \n     /___)=\\       \n    /_______\\      \n      /____\\        \n       TUX           ",
        "       .--.         \n      | o_o|        \n      |\\_:/|        \n      / /  \\        \n     | |   |)       \n     \\_\_/        \n      \___/         \n     /____\\        \n    /______\\       \n      TUX           ",
        "         .--.       \n        |o_o |      \n        |:_/ |      \n       //   /       \n      (|   /        \n     /'__/          \n     \\___          \n      /__           \n     /___           \n      TX            ",
        "          .-.       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          | |       \n          |_|       ",
        "       .--.         \n      |o_o |        \n      |:_/ |        \n     //   \\ \\       \n    (|     | )      \n   /'\\_   _/`\\     \n   \\___)=(___/     \n      /____\\        \n     /______\\       \n       TUX           ",
    )),
    "macOS": LogoFrames("macOS", (
        "        ,--.        \n      ,'    `.      \n     /  .--.  \\     \n    |  (    )  |    \n     \\  `--'  /     \n      `.    ,'      \n        `--'        \n       _/|          \n      /__|          \n       macOS        ",
        "         ,-.        \n       ,'   `.      \n      /  .--  \\     \n     |  (   )  |    \n      \\  `--  /     \n       `.   ,'       \n         `-'         \n        /|          \n       /_|          \n        macOS       ",
        "          /         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         ",
        "        .--,        \n      ,'   `.       \n     /  --.  \\      \n    |  (   )  |     \n     \\ `--' /      \n      `.  ,'        \n        `-'         \n        /|          \n       /_|          \n       macOS        ",
        "      .-==-.        \n    ,'      `.      \n   /  .--.   \\     \n  |  (    )   |     \n   \\  `--'  /     \n    `.    ,'       \n      `--'         \n       /|          \n      /_|          \n      macOS        ",
        "         ,-.        \n       ,'   `.      \n      /  .--  \\     \n     |  (   )  |    \n      \\  `--  /    \n       `.   ,'      \n         `-'        \n        /|          \n       /_|          \n        macOS       ",
        "          /         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         \n          |         ",
        "        ,--.        \n      ,'    `.      \n     /  .--.  \\     \n    |  (    )  |    \n     \\  `--'  /     \n      `.    ,'      \n        `--'        \n       _/|          \n      /__|          \n       macOS        ",
    )),
    "Other": LogoFrames("Other", ("      ┌────────┐    \n      │ SYSOPS │    \n      │  OS ?  │    \n      └────────┘    \n                    ",) * 8),
}


def detect_os() -> str:
    name = platform.system()
    return {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}.get(name, "Other")


def _colorize(os_name: str, frame_index: int, text: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    if os_name == "Windows":
        code = ("96", "94", "36", "94", "96", "94", "36", "94")[frame_index % 8]
    elif os_name == "Linux":
        code = ("97", "33", "30", "37", "97", "33", "30", "37")[frame_index % 8]
    elif os_name == "macOS":
        code = ("97", "37", "36", "95", "97", "37", "36", "95")[frame_index % 8]
    else:
        code = "90"
    return f"{CSI}1;{code}m{text}{RESET}"


def render_os_frame(os_name: str | None = None, width: int = 28, frame_index: int = 0, color: bool = True) -> str:
    if width <= 0:
        raise ValueError("width must be greater than 0")
    key = os_name or detect_os()
    frame = LOGOS.get(key, LOGOS["Other"]).frames[frame_index % 8]
    target = max(MIN_WIDTH, width)
    lines = []
    for line in frame.splitlines():
        if len(line) > target:
            start = (len(line) - target) // 2
            line = line[start:start + target]
        else:
            line = line.center(target)
        lines.append(_colorize(key, frame_index, line) if color else line)
    return "\n".join(lines)


def logo_frames(os_name: str | None = None) -> tuple[str, ...]:
    key = os_name or detect_os()
    return LOGOS.get(key, LOGOS["Other"]).frames


def _terminal_width(fallback: int = 32) -> int:
    try:
        return max(MIN_WIDTH, shutil.get_terminal_size(fallback=(fallback, 24)).columns - 2)
    except OSError:
        return max(MIN_WIDTH, fallback)


class CursorGuard:
    def __enter__(self):
        if sys.stdout.isatty():
            sys.stdout.write(HIDE_CURSOR)
            sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc, tb):
        if sys.stdout.isatty():
            sys.stdout.write(SHOW_CURSOR + RESET)
            sys.stdout.flush()
        return False


def animate_os_logo(width: int | None = None, fps: float = DEFAULT_FPS, loops: int | None = None) -> None:
    if fps <= 0:
        raise ValueError("fps must be greater than 0")
    key = detect_os()
    frames = logo_frames(key)
    interval = 1.0 / fps
    index = 0
    completed = 0
    rows = len(frames[0].splitlines())

    with CursorGuard():
        try:
            sys.stdout.write(CURSOR_HOME)
            sys.stdout.flush()
            next_at = time.monotonic()
            while loops is None or completed < loops:
                frame_width = width if width is not None else _terminal_width()
                frame = render_os_frame(key, frame_width, index, color=True)
                if index or completed:
                    sys.stdout.write(f"{CSI}{rows}A")
                sys.stdout.write(frame + "\n" + ERASE_DOWN)
                sys.stdout.flush()
                index = (index + 1) % len(frames)
                if index == 0:
                    completed += 1
                next_at += interval
                delay = next_at - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_at = time.monotonic()
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
