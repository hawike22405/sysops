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
        if not self.use_color:
            return "\n".join("".join(row) for row in framebuffer.chars)
        lines = []
        reset = "\033[0m"
        for y in range(framebuffer.height):
            parts = []
            for x in range(framebuffer.width):
                ch = framebuffer.chars[y, x]
                if ch == " ":
                    parts.append(" ")
                else:
                    r, g, b = int(framebuffer.colors[y, x, 0]), int(framebuffer.colors[y, x, 1]), int(framebuffer.colors[y, x, 2])
                    parts.append(f"\033[38;2;{r};{g};{b}m{ch}{reset}")
            lines.append("".join(parts))
        return "\n".join(lines)

    def read_key_nonblocking(self):
        try:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getwch()
            return None
        except ImportError:
            return None
