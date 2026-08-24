from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .camera import Camera
from .depth import BrightnessDepthGenerator, DepthGenerator, apply_depth_scale
from .geometry import Mesh, rotation_x, rotation_y
from .image import PreprocessConfig, preprocess, preprocess_color
from .lighting import Light
from .mesh import generate_mesh_from_depth
from .rasterizer import Rasterizer
from .terminal import TerminalRenderer


@dataclass
class ViewerConfig:
    terminal_width: int = 80
    terminal_height: int = 24
    depth_scale: float = 3.0
    fps: int = 10
    update_hz: int = 30
    wireframe: bool = False
    use_color: bool = True
    style: str = "blocks"


@dataclass
class Viewer:
    config: ViewerConfig = field(default_factory=ViewerConfig)
    camera: Camera = field(default_factory=Camera)
    light: Light = field(default_factory=Light)
    depth_generator: DepthGenerator = field(default_factory=BrightnessDepthGenerator)
    yaw: float = 0.0
    pitch: float = 0.0
    mesh: Mesh | None = field(default=None, init=False)

    def load_image(self, path: str | Path, preprocess_config: PreprocessConfig | None = None) -> None:
        if preprocess_config is None:
            preprocess_config = PreprocessConfig()
        grayscale, rgb = preprocess_color(path, preprocess_config)
        depth = self.depth_generator.generate(grayscale)
        depth = apply_depth_scale(depth, self.config.depth_scale)
        self.mesh = generate_mesh_from_depth(depth, depth_scale=1.0, rgb=rgb)

    def load_mesh(self, mesh: Mesh) -> None:
        self.mesh = mesh

    def render_frame(self) -> str:
        if self.mesh is None:
            raise RuntimeError("Call load_image() or load_mesh() before render_frame().")
        ramp = "█" if self.config.style == "blocks" else None
        rasterizer = Rasterizer(self.config.terminal_width, self.config.terminal_height, ramp=ramp) if ramp else Rasterizer(self.config.terminal_width, self.config.terminal_height)
        model_matrix = rotation_y(self.yaw) @ rotation_x(self.pitch)
        framebuffer = rasterizer.render(self.mesh, model_matrix, self.camera, self.light)
        renderer = TerminalRenderer(use_color=self.config.use_color)
        return renderer.render_to_string(framebuffer)

    def handle_key(self, key: str) -> bool:
        key = key.lower()
        if key in ("q", "esc"):
            return False
        if key in ("left", "a"):
            self.yaw -= 0.1
        elif key in ("right", "d"):
            self.yaw += 0.1
        elif key in ("up", "w"):
            self.pitch = max(-1.4, self.pitch - 0.1)
        elif key in ("down", "s"):
            self.pitch = min(1.4, self.pitch + 0.1)
        elif key in ("+", "="):
            self.camera.dolly(0.35)
        elif key == "-":
            self.camera.dolly(-0.35)
        elif key == "r":
            self.yaw = 0.0
            self.pitch = 0.0
            self.camera.position = self.camera.target + [0.0, 0.0, 5.0]
        return True

    def run(self) -> None:
        import time
        import sys

        if self.mesh is None:
            raise RuntimeError("Call load_image() or load_mesh() before run().")
        delay = 1.0 / max(1, self.config.fps)
        
        is_windows = sys.platform == "win32"
        if is_windows:
            import msvcrt
        else:
            import select
            import tty
            import termios

        if not is_windows:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

        try:
            while True:
                print("\033[2J\033[H", end="")
                print(self.render_frame())
                print("\n[a/d] rotate  [w/s] tilt  [+/-] zoom  [r] reset  [q] quit")
                
                start_time = time.time()
                key_pressed = None
                while time.time() - start_time < delay:
                    if is_windows:
                        if msvcrt.kbhit():
                            ch = msvcrt.getch()
                            if ch in (b'\x00', b'\xe0'):
                                msvcrt.getch()
                            else:
                                key_pressed = ch.decode("utf-8", "ignore")
                                break
                    else:
                        dr, _, _ = select.select([sys.stdin], [], [], 0.05)
                        if dr:
                            key_pressed = sys.stdin.read(1)
                            break
                    time.sleep(0.01)

                if key_pressed:
                    if not self.handle_key(key_pressed):
                        break
        finally:
            if not is_windows:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
