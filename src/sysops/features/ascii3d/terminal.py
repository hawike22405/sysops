from __future__ import annotations

from dataclasses import dataclass

from .rasterizer import FrameBuffer

DEFAULT_KEY_BINDINGS = {
    "left": "rotate_left",
    "right": "rotate_right",
    "up": "rotate_up",
    "down": "rotate_down",
    "+": "zoom_in",
    "-": "zoom_out",
    "w": "wireframe",
    "s": "shaded",
    "c": "toggle_color",
    "r": "reset",
    "d": "cycle_depth",
    "q": "quit",
}


@dataclass
class TerminalRenderer:
    use_color: bool = False

    def render_to_string(self, framebuffer: FrameBuffer) -> str:
        return "\n".join("".join(row) for row in framebuffer.chars)

    def read_key_nonblocking(self):
        try:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getwch()
            return None
        except ImportError:
            return None
