"""
sysops.ascii_art
~~~~~~~~~~~~~~~~~

Render an image as ASCII art. If no image is supplied, falls back to a
built-in ASCII logo for the current operating system (Linux / macOS / Windows).

Public API:
    render_ascii(image_path=None, width=80, invert=False, color=True,
                 style="chars") -> str
    print_ascii(image_path=None, width=80, invert=False, color=True,
                style="chars") -> None

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

_RAMP = "@&%QWM0NB$gD#R8mHXKAUbGOpV4d9h6Pkqw2SE]ayjx5YZoen[ultI13fC}{iF|)(7Jv Tl?sz/*cr!+><;=^,_:'.-` "
_CHAR_ASPECT_CORRECTION = 0.55

_UPPER_HALF_BLOCK = "\u2580"
_RESET = "\x1b[0m"


def _fg(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"


def _bg(r: int, g: int, b: int) -> str:
    return f"\x1b[48;2;{r};{g};{b}m"


def supports_truecolor() -> bool:
    """Best-effort detection of 24-bit ANSI truecolor support."""
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
        raise UnsupportedImageError(
            f"Could not read '{path}' as an image: {exc}"
        ) from exc


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


def _image_to_ascii_color_blocks(image: "Image.Image", width: int) -> str:
    """Render with half-block cells and separate foreground/background colors."""
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


def _image_to_ascii_color_chars(
    image: "Image.Image", width: int, invert: bool = False
) -> str:
    """Render colored ASCII glyphs for a textured, classic ASCII look."""
    rgb_image = image.convert("RGB")
    orig_w, orig_h = rgb_image.size
    height = max(
        1, int((orig_h / orig_w) * width * _CHAR_ASPECT_CORRECTION)
    )
    rgb_image = rgb_image.resize((width, height))
    pixels = rgb_image.load()

    # Bright pixels are dense glyphs by default; --invert flips the ramp.
    ramp = _RAMP if invert else _RAMP[::-1]
    lines = []
    for row in range(height):
        chars = []
        last_fg = None
        for col in range(width):
            r, g, b = pixels[col, row]
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            glyph = ramp[min(len(ramp) - 1, lum * len(ramp) // 256)]
            prefix = ""
            if (r, g, b) != last_fg:
                prefix = _fg(r, g, b)
                last_fg = (r, g, b)
            chars.append(prefix + glyph)
        lines.append("".join(chars) + _RESET)
    return "\n".join(lines)


def _image_to_iterm2(image: "Image.Image", width: int) -> str:
    """Render the image using the iTerm2 inline image protocol (supported by Windows Terminal, iTerm2, WezTerm, etc.)."""
    import base64
    from io import BytesIO
    
    # Calculate height to maintain aspect ratio
    orig_w, orig_h = image.size
    height = max(1, int((orig_h / orig_w) * width * _CHAR_ASPECT_CORRECTION))
    
    # Save image to PNG bytes
    buf = BytesIO()
    image.save(buf, format="PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode("ascii")
    
    # We specify width and height in character cells.
    # The \033]1337 sequence is the standard iTerm2 protocol.
    osc = f"\033]1337;File=inline=1;width={width};height={height};preserveAspectRatio=1:{b64_data}\a"
    
    # To allow side-by-side layout, we output the image, then move the cursor UP by 'height' lines.
    # Then we pad the rest of the lines with spaces so the text renderer knows how wide the logo is.
    lines = []
    lines.append(f"{osc}\033[{height}A" + " " * width)
    for _ in range(height - 1):
        lines.append(" " * width)
        
    return "\n".join(lines)


def _default_os_logo() -> str:
    return _OS_LOGOS.get(platform.system(), _OS_LOGOS["Other"])


def render_ascii(
    image_path: Optional[str] = None,
    width: int = 80,
    invert: bool = False,
    color: Optional[bool] = None,
    style: str = "chars",
) -> str:
    """Return a rendering of ``image_path``.

    ``color`` forces or disables ANSI truecolor; ``None`` auto-detects.
    ``style`` controls rendering:
      - ``chars``: colored ASCII glyphs for a textured look.
      - ``blocks``: solid half-block cells for a sharper look.
      - ``image``: true terminal image using iTerm2 protocol (Windows Terminal, Kitty, etc.).
    """
    if width <= 0:
        raise ValueError("width must be greater than 0")
    if style not in ("chars", "blocks", "image"):
        raise ValueError("style must be 'chars', 'blocks', or 'image'")
    if image_path is None:
        return _default_os_logo()

    image = _load_image(image_path)
    if style == "image":
        return _image_to_iterm2(image, width=width)
        
    use_color = supports_truecolor() if color is None else color
    if use_color:
        if style == "blocks":
            return _image_to_ascii_color_blocks(image, width=width)
        return _image_to_ascii_color_chars(image, width=width, invert=invert)
    return _image_to_ascii(image, width=width, invert=invert)


def print_ascii(
    image_path: Optional[str] = None,
    width: int = 80,
    invert: bool = False,
    color: Optional[bool] = None,
    style: str = "chars",
) -> None:
    print(
        render_ascii(
            image_path=image_path,
            width=width,
            invert=invert,
            color=color,
            style=style,
        )
    )


_OS_LOGOS = {
    "Linux": """\x1b[37m
        .--.
       |o_o |
       |:_/ |
      //   \\ \\
     (|     | )
    /'\\_   _/`\\
    \\___)=(___/
      \x1b[33mLINUX\x1b[0m
""".strip("\n"),
    "Darwin": """\x1b[32m
        ,--.
      ,'    `.
     /  .--.  \\
    |  (    )  |
     \\  `--'  /
      `.    ,'
        `--'
      \x1b[37mmacOS\x1b[0m
""".strip("\n"),
    "Windows": """\x1b[36m
    ██████╗ ██████╗
    ██╔══██╗██╔══██╗
    ██████╔╝██████╔╝
    ██╔══██╗██╔══██╗
    ██████╔╝██████╔╗
    ╚═════╝ ╚═════╝
     \x1b[34mWINDOWS\x1b[0m
""".strip("\n"),
    "Other": """\x1b[31m
      +------+
      |  ?   |
      +------+
    UNKNOWN OS\x1b[0m
""".strip("\n"),
}
