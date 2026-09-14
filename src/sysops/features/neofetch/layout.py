"""Split-pane terminal layout: coloured ASCII logo on the left, stats on the right.

The renderer dynamically measures the visible width of the logo (stripping
ANSI escapes) so that the stats column always starts at the same position
regardless of which OS art is selected.
"""

from __future__ import annotations

import os
import platform
import re
import socket
import sys

from .ascii_logos import colorize_logo, get_logo, get_logo_colors

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

CSI = "\x1b["
RESET = f"{CSI}0m"
BOLD = f"{CSI}1m"

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")


def _strip_ansi(text: str) -> str:
    """Return *text* with all ANSI escape sequences removed."""
    text = _OSC_RE.sub("", text)
    return _ANSI_RE.sub("", text)


def _visible_len(text: str) -> int:
    """Return the visible (non-escape) character count of *text*."""
    return len(_strip_ansi(text))


def _color(code: str) -> str:
    return f"{CSI}{code}m"


def _use_color() -> bool:
    """Return True if ANSI colors should be emitted."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


# ---------------------------------------------------------------------------
# Stats formatting
# ---------------------------------------------------------------------------

# Display order and the label colours  (matches neofetch convention)
_DISPLAY_KEYS = [
    "OS", "Host", "Kernel", "Uptime", "Packages",
    "Shell", "Resolution", "DE", "WM", "Terminal",
    "CPU", "GPU", "Memory",
]


def _build_info_lines(
    info: dict[str, str],
    distro_id: str,
    use_color: bool = True,
) -> list[str]:
    """Build the right-side stats block as a list of pre-formatted strings."""
    primary_sgr, _ = get_logo_colors(distro_id)
    hostname = _safe_hostname()
    username = _safe_username()
    title = f"{username}@{hostname}"

    lines: list[str] = []
    if use_color:
        title_colored = f"{_color(primary_sgr)}{BOLD}{title}{RESET}"
        separator = f"{_color(primary_sgr)}{'─' * len(title)}{RESET}"
        lines.append(title_colored)
        lines.append(separator)
    else:
        lines.append(title)
        lines.append("─" * len(title))

    for key in _DISPLAY_KEYS:
        value = info.get(key, "")
        if not value or value == "N/A":
            continue
        if use_color:
            lines.append(f"{_color(primary_sgr)}{BOLD}{key}{RESET}: {value}")
        else:
            lines.append(f"{key}: {value}")

    # Colour palette bar (a row of 8 coloured blocks)
    if use_color:
        lines.append("")
        palette = ""
        for code in range(30, 38):
            palette += f"{_color(str(code))}███"
        palette += RESET
        lines.append(palette)
        palette2 = ""
        for code in range(90, 98):
            palette2 += f"{_color(str(code))}███"
        palette2 += RESET
        lines.append(palette2)

    return lines


def _safe_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "localhost"


def _safe_username() -> str:
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USER") or os.environ.get("USERNAME") or "user"


# ---------------------------------------------------------------------------
# Layout rendering
# ---------------------------------------------------------------------------

_GAP = "   "  # 3-space gap between logo and stats


def render_fetch(info: dict[str, str]) -> str:
    """Render the full neofetch-style output and return it as a string.

    Parameters
    ----------
    info:
        Dictionary returned by :func:`system_info.gather_system_info`.
    """
    distro_id = info.get("distro_id", "linux")
    use_color = _use_color()

    # Get and optionally colorize the logo
    logo_raw = get_logo(distro_id)
    if use_color:
        logo = colorize_logo(logo_raw, distro_id)
    else:
        logo = logo_raw

    logo_lines = logo.splitlines()
    info_lines = _build_info_lines(info, distro_id, use_color)

    # Calculate the visible width of the widest logo line
    logo_width = max((_visible_len(line) for line in logo_lines), default=0)

    # Merge side-by-side
    max_lines = max(len(logo_lines), len(info_lines))
    output_lines: list[str] = []
    for i in range(max_lines):
        left = logo_lines[i] if i < len(logo_lines) else ""
        right = info_lines[i] if i < len(info_lines) else ""
        # Pad the left side to logo_width visible characters
        padding = logo_width - _visible_len(left)
        output_lines.append(f"{left}{' ' * max(0, padding)}{_GAP}{right}")

    # Add a trailing blank line
    output_lines.append("")
    return "\n".join(output_lines)


def print_fetch(info: dict[str, str]) -> None:
    """Render and print the neofetch output to stdout."""
    sys.stdout.write(render_fetch(info))
    sys.stdout.flush()
