"""
sysops.ascii_art
~~~~~~~~~~~~~~~~~

Render an image as ASCII art. If no image is supplied, falls back to a
built-in ASCII logo for the current operating system (Linux / macOS / Windows).

Public API:
    render_ascii(image_path=None, width=80, invert=False, color=True) -> str
    print_ascii(image_path=None, width=80, invert=False, color=True) -> None

Dependencies: Pillow (`pip install Pillow`)
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The 'ascii art' feature requires Pillow. Install it with: pip install Pillow"
    ) from exc

_RAMP = "@%#*+=-:. "
_CHAR_ASPECT_CORRECTION = 0.55

_UPPER_HALF_BLOCK = "\u2580"  # ▀
_RESET = "\x1b[0m"


def _fg(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"


def _bg(r: int, g: int, b: int) -> str:
    return f"\x1b[48;2;{r};{g};{b}m"


def supports_truecolor() -> bool:
    """Best-effort check for 24-bit ANSI color support in the current terminal.

    Modern Windows Terminal / PowerShell 7+ support this out of the box.
    Legacy conhost (old cmd.exe / PowerShell 5 outside Windows Terminal)
    generally does not unless VT processing has been explicitly enabled.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    if os.environ.get("WT_SESSION"):
        return True
    if platform.system() == "Windows":
        return os.environ.get("TERM") != "dumb"
    return os.environ.get("TERM", "") not in ("", "dumb")


class UnsupportedImageError(ValueError):
    """Raised when the given path isn't a readable image."""


def _load_image(image_path: str) -> "Image.Image":
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise UnsupportedImageError(f"No such image file: {path}")
    try:
        return Image.open(path)
    except Exception as exc:
        raise UnsupportedImageError(f"Could not read '{path}' as an image: {exc}") from exc


def _image_to_ascii(image: "Image.Image", width: int, invert: bool) -> str:
    image = image.convert("L")
    orig_w, orig_h = image.size
    height = max(1, int((orig_h / orig_w) * width * _CHAR_ASPECT_CORRECTION))
    image = image.resize((width, height))

    pixels = list(image.getdata())
    ramp = _RAMP[::-1] if invert else _RAMP

    lines = []
    for row in range(height):
        row_pixels = pixels[row * width:(row + 1) * width]
        line = "".join(
            ramp[min(len(ramp) - 1, pixel * len(ramp) // 256)]
            for pixel in row_pixels
        )
        lines.append(line)
    return "\n".join(lines)


def _image_to_ascii_color(image: "Image.Image", width: int) -> str:
    """Render using half-block characters + 24-bit ANSI color, like
    neofetch/fastfetch/chafa do. Each printed row packs 2 image rows: the
    top pixel becomes the glyph's foreground color, the bottom pixel becomes
    its background color, doubling vertical resolution for free.
    """
    image = image.convert("RGB")
    orig_w, orig_h = image.size

    height = max(2, round(width * (orig_h / orig_w)))
    if height % 2:
        height += 1
    image = image.resize((width, height))
    pixels = image.load()

    lines = []
    for row in range(0, height, 2):
        chars = []
        last_fg = last_bg = None
        for col in range(width):
            top = pixels[col, row]
            bottom = pixels[col, row + 1] if row + 1 < height else (0, 0, 0)
            prefix = ""
            if top != last_fg:
                prefix += _fg(*top)
                last_fg = top
            if bottom != last_bg:
                prefix += _bg(*bottom)
                last_bg = bottom
            chars.append(prefix + _UPPER_HALF_BLOCK)
        lines.append("".join(chars) + _RESET)
    return "\n".join(lines)


def _default_os_logo() -> str:
    system = platform.system()
    return _OS_LOGOS.get(system, _OS_LOGOS["Other"])


def render_ascii(
    image_path: Optional[str] = None,
    width: int = 80,
    invert: bool = False,
    color: Optional[bool] = None,
) -> str:
    """Return an ASCII-art rendering of `image_path`.

    color: True forces 24-bit ANSI color (half-block renderer), False forces
    the plain grayscale character-ramp renderer, None (default) auto-detects
    based on the terminal. The OS fallback logo (no image_path) is always
    plain text.
    """
    if width <= 0:
        raise ValueError("width must be greater than 0")

    if image_path is None:
        return _default_os_logo()

    image = _load_image(image_path)

    use_color = supports_truecolor() if color is None else color
    if use_color:
        return _image_to_ascii_color(image, width=width)
    return _image_to_ascii(image, width=width, invert=invert)


def print_ascii(
    image_path: Optional[str] = None,
    width: int = 80,
    invert: bool = False,
    color: Optional[bool] = None,
) -> None:
    """Convenience wrapper that prints the result of render_ascii()."""
    print(render_ascii(image_path=image_path, width=width, invert=invert, color=color))


_OS_LOGOS = {
    "Linux": r"""
        .--.
       |o_o |
       |:_/ |
      //   \ \
     (|     | )
    /'\_   _/`\
    \___)=(___/
      LINUX
""".strip("\n"),
    "Darwin": r"""
        ,--.
      ,'    `.
     /  .--.  \
    |  (    )  |
     \  `--'  /
      `.    ,'
        `--'
      macOS
""".strip("\n"),
    "Windows": r"""
    ██████╗ ██████╗
    ██╔══██╗██╔══██╗
    ██████╔╝██████╔╝
    ██╔══██╗██╔══██╗
    ██████╔╝██████╔╗
    ╚═════╝ ╚═════╝
     WINDOWS
""".strip("\n"),
    "Other": r"""
      +------+
      |  ?   |
      +------+
    UNKNOWN OS
""".strip("\n"),
}
