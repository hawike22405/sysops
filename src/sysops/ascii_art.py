"""
sysops.ascii_art
~~~~~~~~~~~~~~~~~

Render an image as ASCII art. If no image is supplied, falls back to a
built-in ASCII logo for the current operating system (Linux / macOS / Windows).

Public API:
    render_ascii(image_path=None, width=80, invert=False) -> str
    print_ascii(image_path=None, width=80, invert=False) -> None

Dependencies: Pillow (`pip install Pillow`)
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The 'ascii art' feature requires Pillow. Install it with: pip install Pillow"
    ) from exc

# Characters ordered from darkest to lightest. Longer ramps give smoother
# gradients; this one is a common, readable choice.
_RAMP = "@%#*+=-:. "

# Terminal character cells are roughly twice as tall as they are wide, so we
# compress vertically to keep the aspect ratio looking correct.
_CHAR_ASPECT_CORRECTION = 0.55


class UnsupportedImageError(ValueError):
    """Raised when the given path isn't a readable image."""


def _load_image(image_path: str) -> "Image.Image":
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise UnsupportedImageError(f"No such image file: {path}")
    try:
        return Image.open(path)
    except Exception as exc:  # Pillow raises various error types
        raise UnsupportedImageError(f"Could not read '{path}' as an image: {exc}") from exc


def _image_to_ascii(image: "Image.Image", width: int, invert: bool) -> str:
    image = image.convert("L")  # grayscale

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


def _default_os_logo() -> str:
    system = platform.system()
    return _OS_LOGOS.get(system, _OS_LOGOS["Other"])


def render_ascii(
    image_path: Optional[str] = None,
    width: int = 80,
    invert: bool = False,
) -> str:
    """
    Return an ASCII-art rendering of `image_path`.

    If `image_path` is None, returns a built-in ASCII logo for the current OS
    (Linux, Darwin/macOS, Windows) instead of converting an image.
    """
    if image_path is None:
        return _default_os_logo()

    image = _load_image(image_path)
    return _image_to_ascii(image, width=width, invert=invert)


def print_ascii(
    image_path: Optional[str] = None,
    width: int = 80,
    invert: bool = False,
) -> None:
    """Convenience wrapper that prints the result of render_ascii()."""
    print(render_ascii(image_path=image_path, width=width, invert=invert))


# --------------------------------------------------------------------------
# Built-in fallback logos (simple, generic silhouettes — not reproductions
# of any trademarked logo artwork).
# --------------------------------------------------------------------------

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
    ██████╔╝██████╔/
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
