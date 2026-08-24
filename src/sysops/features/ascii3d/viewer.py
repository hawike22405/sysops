from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .camera import Camera
from .depth import BrightnessDepthGenerator, DepthGenerator, apply_depth_scale
from .geometry import Mesh, rotation_x, rotation_y
from .image import PreprocessConfig, preprocess
from .lighting import Light
from .mesh import generate_mesh_from_depth
from .rasterizer import Rasterizer
from .terminal import TerminalRenderer


@dataclass
class ViewerConfig:
    terminal_width: int = 100
    terminal_height: int = 35
    depth_scale: float = 3.0
    fps: int = 15
    update_hz: int = 60
    wireframe: bool = False
    use_color: bool = False


@dataclass
class Viewer:
    config: ViewerConfig = field(default_factory=ViewerConfig)
    camera: Camera = field(default_factory=Camera)
    light: Light = field(default_factory=Light)
    depth_generator: DepthGenerator = field(default_factory=BrightnessDepthGenerator)
    yaw: float = 0.0
    pitch: float = 0.0
    mesh: Mesh | None = field(default=None, init=False)

    def load_image(self, path: str | Path, preprocess_config: PreprocessConfig = PreprocessConfig()) -> None:
        grayscale = preprocess(path, preprocess_config)
        depth = self.depth_generator.generate(grayscale)
        depth = apply_depth_scale(depth, self.config.depth_scale)
        self.mesh = generate_mesh_from_depth(depth, depth_scale=1.0)

    def load_mesh(self, mesh: Mesh) -> None:
        self.mesh = mesh

    def render_frame(self) -> str:
        if self.mesh is None:
            raise RuntimeError("Call load_image() or load_mesh() before render_frame().")
        rasterizer = Rasterizer(self.config.terminal_width, self.config.terminal_height)
        model_matrix = rotation_y(self.yaw) @ rotation_x(self.pitch)
        framebuffer = rasterizer.render(self.mesh, model_matrix, self.camera, self.light)
        renderer = TerminalRenderer(use_color=self.config.use_color)
        return renderer.render_to_string(framebuffer)

    def handle_key(self, key: str) -> bool:
        raise NotImplementedError("Implement interactive key bindings.")

    def run(self) -> None:
        raise NotImplementedError("Implement the interactive render loop.")