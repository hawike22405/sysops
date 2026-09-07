"""Cross-platform animated ASCII OS logo flipbook.

Uses pre-rendered, fixed-size sprites rather than rebuilding a 3D scene. The
result is deterministic, low-overhead terminal animation with safe cursor
handling and resize-aware rendering.
"""

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


# Each logo contains 8 key poses: front -> 3/4 -> edge -> 3/4 -> front,
# followed by the reverse path. Keeping the same row count avoids vertical jitter.
LOGOS: dict[str, LogoFrames] = {
    "Windows": LogoFrames(
        "Windows",
        (
            "   ██████  ██████   ",
            "   ██  ██  ██  ██   ",
            "   ██  ██  ██  ██   ",
            "   ██████  ██████   ",
            "   ██████  ██████   ",
            "   ██  ██  ██  ██   ",
            "   ██  ██  ██  ██   ",
            "   ██████  ██████   ",
            "   \u005c\u005c        //    ",
            "    \u005c\u005c      //     ",
            "     \u005c____//      ",
        ),
        (
            "    ██████  █████   ",
            "    ██  ██  ██  ██  ",
            "    ██  ██  ██  ██  ",
            "    ██████  █████   ",
            "    ██████  █████   ",
            "    ██  ██  ██  ██  ",
            "    ██  ██  ██  ██  ",
            "    ██████  █████   ",
            "      \u005c\u005c      //     ",
            "       \u005c____//      ",
            "         \u005c/         ",
        ),
        (
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "        ██          ",
            "        ██          ",
            "        ██          ",
        ),
        (
            "   █████  ██████    ",
            "   ██  ██ ██  ███   ",
            "   ██  ██ ██  ███   ",
            "   █████  ██████    ",
            "   █████  ██████    ",
            "   ██  ██ ██  ███   ",
            "   ██  ██ ██  ███   ",
            "   █████  ██████    ",
            "    \\         //    ",
            "     \_______//     ",
            "                       ",
        ),
            "   ██████  ██████   ",
            "   ██  ██  ██  ██   ",
            "   ██  ██  ██  ██   ",
            "   ██████  ██████   ",
            "   ██████  ██████   ",
            "   ██  ██  ██  ██   ",
            "   ██  ██  ██  ██   ",
            "   ██████  ██████   ",
            "   //        \\     ",
            "  //      __//      ",
            "  \\______/         ",
        ),
        (
            "    █████  ██████   ",
            "    ██  █  ██  ██   ",
            "    ██  █  ██  ██   ",
            "    █████  ██████   ",
            "    █████  ██████   ",
            "    ██  █  ██  ██   ",
            "    ██  █  ██  ██   ",
            "    █████  ██████   ",
            "     //      \      ",
            "    //       \     ",
            "   /__________\     ",
        ),
        (
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ████         ",
            "       ██           ",
            "       ██           ",
            "       ██           ",
        ),
        (
            "    █████  ██████   ",
            "   █████  ██████    ",
            "   ██  ██ ██  ██    ",
            "   █████  ██████    ",
            "   █████  ██████    ",
            "   ██  ██ ██  ██    ",
            "   █████  ██████    ",
            "    ████  ████      ",
            "      //     \\      ",
            "     //       \\     ",
            "    //_________\\    ",
        ),
        ),
    ),
    "Linux": LogoFrames(
        "Linux",
        (
            "       .--.         ",
            "      |o_o |        ",
            "      |:_/ |        ",
            "     //   \\ \\       ",
            "    (|     | )      ",
            "   /'\\_   _/`\\     ",
            "   \\___)=(___/     ",
            "      /____\\        ",
            "     /______\\       ",
            "       TUX           ",
        ),
        (
            "         .--.       ",
            "        /o_o|       ",
            "        |:_/|       ",
            "       //  /        ",
            "      (|  /         ",
            "     /'_/           ",
            "     \___           ",
            "       /__           ",
            "      /___           ",
            "       TX            ",
        ),
        (
            "          .-.       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          |_|       ",
        ),
        (
            "         .--.       ",
            "        |o_o/       ",
            "        |:_/        ",
            "        /  \\       ",
            "       /  |)        ",
            "      /_   \\       ",
            "     /___)=\\       ",
            "    /_______\\      ",
            "      /____\\        ",
            "       TUX           ",
        ),
        (
            "       .--.         ",
            "      | o_o|        ",
            "      |\_:/|        ",
            "      / /  \\        ",
            "     | |   |)       ",
            "     \\_\_/        ",
            "      \___/         ",
            "     /____\\        ",
            "    /______\\       ",
            "      TUX           ",
        ),
        (
            "         .--.       ",
            "        |o_o |      ",
            "        |:_/ |      ",
            "       //   /       ",
            "      (|   /        ",
            "     /'__/          ",
            "     \\___          ",
            "      /__           ",
            "     /___           ",
            "      TX            ",
        ),
        (
            "          .-.       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          | |       ",
            "          |_|       ",
        ),
        (
            "       .--.         ",
            "      |o_o |        ",
            "      |:_/ |        ",
            "     //   \\ \\       ",
            "    (|     | )      ",
            "   /'\\_   _/`\\     ",
            "   \\___)=(___/     ",
            "      /____\\        ",
            "     /______\\       ",
            "       TUX           ",
        ),
    ),
    "macOS": LogoFrames(
        "macOS",
        (
            "        ,--.        ",
            "      ,'    `.      ",
            "     /  .--.  \\     ",
            "    |  (    )  |    ",
            "     \\  `--'  /     ",
            "      `.    ,'      ",
            "        `--'        ",
            "       _/|          ",
            "      /__|          ",
            "       macOS        ",
        ),
        (
            "         ,-.        ",
            "       ,'   `.      ",
            "      /  .--  \\     ",
            "     |  (    )  |   ",
            "      \\ `--  /     ",
            "       `.  ,'       ",
            "         `'         ",
            "        /|          ",
            "       /_|          ",
            "        macOS       ",
        ),
        (
            "          /         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
        ),
        (
            "        .--,        ",
            "      ,'   `.       ",
            "     /  --.  \\      ",
            "    |  (   )  |     ",
            "     \\ `--' /      ",
            "      `.  ,'        ",
            "        `-'         ",
            "        /|          ",
            "       /_|          ",
            "       macOS        ",
        ),
        (
            "      .-==-.        ",
            "    ,'      `.      ",
            "   /  .--.   \\     ",
            "  |  (    )   |    ",
            "   \\  `--'  /     ",
            "    `.    ,'       ",
            "      `--'         ",
            "       /|          ",
            "      /_|          ",
            "      macOS        ",
        ),
        (
            "         ,-.        ",
            "       ,'   `.      ",
            "      /  .--  \\     ",
            "     |  (    )  |   ",
            "      \\ `--  /     ",
            "       `.  ,'       ",
            "         `'         ",
            "        /|          ",
            "       /_|          ",
            "        macOS       ",
        ),
        (
            "          /         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
            "          |         ",
        ),
        (
            "        ,--.        ",
            "      ,'    `.      ",
            "     /  .--.  \\     ",
            "    |  (    )  |    ",
            "     \\  `--'  /     ",
            "      `.    ,'      ",
            "        `--'        ",
            "       _/|          ",
            "      /__|          ",
            "       macOS        ",
        ),
    ),
    "Other": LogoFrames(
        "Other",
        (
            "      ┌────────┐    ",
            "      │ SYSOPS │    ",
            "      │  OS ?  │    ",
            "      └────────┘    ",
            "                    ",
        ) * 8,
    ),
}


def detect_os() -> str:
    name = platform.system()
    if name == "Windows":
        return "Windows"
    if name == "Darwin":
        return "macOS"
    if name == "Linux":
        return "Linux"
    return "Other"


def _ansi_color(os_name: str, frame_index: int, text: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    if os_name == "Windows":
        code = ("96", "94", "36", "94", "96", "94", "36", "94")[frame_index % 8]
        return f"{CSI}1;{code}m{text}{RESET}"
    if os_name == "Linux":
        code = ("97", "33", "30", "37", "97", "33", "30", "37")[frame_index % 8]
        return f"{CSI}1;{code}m{text}{RESET}"
    if os_name == "macOS":
        code = ("97", "37", "36", "95", "97", "37", "36", "95")[frame_index % 8]
        return f"{CSI}1;{code}m{text}{RESET}"
    return f"{CSI}2m{text}{RESET}"


def render_os_frame(os_name: str | None = None, width: int = 28, frame_index: int = 0, color: bool = True) -> str:
    if width <= 0:
        raise ValueError("width must be greater than 0")
    key = os_name or detect_os()
    frames = LOGOS.get(key, LOGOS["Other"]).frames
    frame = frames[frame_index % len(frames)]
    target = max(MIN_WIDTH, width)
    rendered: list[str] = []
    for line in frame.splitlines():
        if len(line) > target:
            start = (len(line) - target) // 2
            line = line[start : start + target]
        else:
            line = line.center(target)
        rendered.append(_ansi_color(key, frame_index, line) if color else line)
    return "\n".join(rendered)


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
    """Run the OS logo flipbook until Ctrl+C, or for ``loops`` cycles in tests."""
    if fps <= 0:
        raise ValueError("fps must be greater than 0")
    os_name = detect_os()
    frames = logo_frames(os_name)
    interval = 1.0 / fps
    index = 0
    completed = 0
    rendered_rows = len(frames[0].splitlines())

    # Avoid full-screen clears every frame. HOME once, then cursor-up by the
    # exact previous frame height. The sprites have a constant row count.
    with CursorGuard():
        try:
            sys.stdout.write(CURSOR_HOME)
            sys.stdout.flush()
            next_frame_at = time.monotonic()
            while loops is None or completed < loops:
                requested_width = width if width is not None else _terminal_width()
                frame = render_os_frame(os_name, requested_width, index, color=True)
                if index or completed:
                    sys.stdout.write(f"{CSI}{rendered_rows}A")
                sys.stdout.write(frame + "\n" + ERASE_DOWN)
                sys.stdout.flush()

                index = (index + 1) % len(frames)
                if index == 0:
                    completed += 1
                next_frame_at += interval
                delay = next_frame_at - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    # Skip accumulated lag instead of busy-spinning.
                    next_frame_at = time.monotonic()
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
