"""Cross-platform animated ASCII OS logo flipbook.

The renderer deliberately uses pre-rendered, fixed-width frames rather than
recomputing a 3D mesh every draw. That keeps CPU use low and makes terminal
animation deterministic and smooth on modest machines.
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
HOME = f"{CSI}H"
CLEAR = f"{CSI}2J{HOME}"
ERASE_DOWN = f"{CSI}J"

DEFAULT_FPS = 12.0
MIN_WIDTH = 16


def detect_os() -> str:
    """Return the normalized host OS family used by the flipbook."""
    name = platform.system()
    if name == "Darwin":
        return "macOS"
    if name == "Windows":
        return "Windows"
    if name == "Linux":
        return "Linux"
    return "Other"


def _c(code: str, text: str) -> str:
    return f"{CSI}{code}m{text}{RESET}"


@dataclass(frozen=True)
class LogoFrames:
    name: str
    frames: tuple[str, ...]
    accent: str


# Each frame uses the same number of visible rows. Width is stabilized by
# padding at render time, preventing horizontal jitter during rotation.
LOGOS = {
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
            "    \u005c\u005c        //     ",
            "     \u005c\u005c      //      ",
            "      \u005c____//       ",
        ),
        "38;2;0;174;255",
    ),
    "Linux": LogoFrames(
        "Linux",
        (
            "       .--.       ",
            "      |o_o |      ",
            "      |:_/ |      ",
            "     //   \\ \\     ",
            "    (|     | )    ",
            "   /'\\_   _/`\\   ",
            "   \\___)=(___/   ",
            "       /___\\      ",
            "      /_____\\     ",
            "     /_______\\    ",
            "       T U X       ",
        ),
        "38;2;255;205;0",
    ),
    "macOS": LogoFrames(
        "macOS",
        (
            "        ,--.       ",
            "      ,'    `.     ",
            "     /  .--.  \\    ",
            "    |  (    )  |   ",
            "     \\  `--'  /    ",
            "      `.    ,'     ",
            "        `--'       ",
            "      _/|          ",
            "    _/  |          ",
            "   /____|          ",
            "     macOS         ",
        ),
        "38;2;225;225;225",
    ),
    "Other": LogoFrames(
        "Other",
        (
            "      ┌───────┐      ",
            "      │  SYS  │      ",
            "      │  OPS  │      ",
            "      │  ? ?  │      ",
            "      └───────┘      ",
        ),
        "38;2;180;180;180",
    ),
}


def _visible_width(text: str) -> int:
    # Frames in this module intentionally contain no ANSI, so len() is safe.
    return len(text)


def _palette(line: str, os_name: str, frame_index: int) -> str:
    """Apply brand-aware ANSI color without changing visible frame width."""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return line

    if os_name == "Linux":
        # Alternate Tux regions by line to mimic shaded rotation.
        if frame_index % 4 == 1:
            return f"{CSI}30m{line}{RESET}"
        if frame_index % 4 == 2:
            return f"{CSI}37m{line}{RESET}"
        if frame_index % 4 == 3:
            return f"{CSI}33m{line}{RESET}"
        return f"{CSI}1;37m{line}{RESET}"

    if os_name == "Windows":
        # Cyan front / blue-ish side illusion using ANSI 256-color accents.
        code = "96" if frame_index in (0, 4) else "94" if frame_index in (1, 3, 5, 7) else "36"
        return f"{CSI}1;{code}m{line}{RESET}"

    if os_name == "macOS":
        codes = ("97", "37", "36", "95", "97", "90", "37", "97")
        return f"{CSI}1;{codes[frame_index % len(codes)]}m{line}{RESET}"

    return f"{CSI}2m{line}{RESET}"


def render_os_frame(os_name: str | None = None, width: int = 28, frame_index: int = 0, color: bool = True) -> str:
    """Render one fixed-width flipbook frame as a string."""
    if width <= 0:
        raise ValueError("width must be greater than 0")
    key = os_name or detect_os()
    logo = LOGOS.get(key, LOGOS["Other"])
    target = min(max(width, MIN_WIDTH), max(width, MIN_WIDTH))
    max_width = max(_visible_width(line) for line in logo.frames)
    scale = min(1.0, target / max_width)

    # Keep the ASCII logo intact whenever it fits. On very narrow terminals,
    # crop symmetrically rather than wrapping, which would destroy alignment.
    lines: list[str] = []
    for line in logo.frames[frame_index % len(logo.frames)].splitlines():
        if len(line) > target:
            start = max((len(line) - target) // 2, 0)
            line = line[start : start + target]
        else:
            line = line.center(target)
        lines.append(_palette(line, key, frame_index) if color else line)
    return "\n".join(lines)


def _terminal_width(fallback: int = 32) -> int:
    try:
        return max(MIN_WIDTH, shutil.get_terminal_size(fallback=(fallback, 24)).columns - 2)
    except OSError:
        return max(MIN_WIDTH, fallback)


class CursorGuard:
    """Hide the cursor for animation and guarantee restoration on exit."""

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
    """Play the detected OS flipbook until Ctrl+C (or loop count) stops it."""
    if fps <= 0:
        raise ValueError("fps must be greater than 0")
    os_name = detect_os()
    frames = LOGOS.get(os_name, LOGOS["Other"]).frames
    frame_count = len(frames)
    interval = 1.0 / fps
    frame_index = 0
    completed_loops = 0
    previous_lines = 0
    requested_width = width

    # Clear once; subsequent frames are updated in place. The frame's visible
    # row count never changes, so no full-screen clear is needed per iteration.
    with CursorGuard():
        try:
            while loops is None or completed_loops < loops:
                current_width = requested_width or _terminal_width()
                frame = render_os_frame(os_name, current_width, frame_index, color=True)
                output = frame
                if previous_lines:
                    output = f"{CSI}{previous_lines}A"
                output += HOME if not previous_lines else ""
                sys.stdout.write(output + ERASE_DOWN)
                sys.stdout.flush()

                start = time.monotonic()
                frame_index = (frame_index + 1) % frame_count
                if frame_index == 0:
                    completed_loops += 1
                sleep_for = interval - (time.monotonic() - start)
                if sleep_for > 0:
                    time.sleep(sleep_for)
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()


def logo_frames(os_name: str | None = None) -> tuple[str, ...]:
    """Expose the pre-rendered sprite array for testing/integration."""
    return LOGOS.get(os_name or detect_os(), LOGOS["Other"]).frames
