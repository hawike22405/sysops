from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .camera import Camera
from .geometry import Mat4, Mesh, transform_direction, transform_point
from .lighting import DEFAULT_ASCII_RAMP, Light, brightness_to_char, face_brightness


@dataclass
class FrameBuffer:
    width: int
    height: int
    chars: np.ndarray = field(init=False)
    depth: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.clear()

    def clear(self, background_char: str = " ") -> None:
        self.chars = np.full((self.height, self.width), background_char, dtype="<U1")
        self.depth = np.full((self.height, self.width), np.inf, dtype=np.float64)


@dataclass
class Rasterizer:
    width: int
    height: int
    char_aspect_ratio: float = 0.5
    ramp: str = DEFAULT_ASCII_RAMP

    def render(self, mesh: Mesh, model_matrix: Mat4, camera: Camera, light: Light) -> FrameBuffer:
        framebuffer = FrameBuffer(self.width, self.height)
        view = camera.view_matrix()
        aspect = (self.width * self.char_aspect_ratio) / self.height
        projection = camera.projection_matrix(aspect)
        world_vertices = np.array([transform_point(model_matrix, v) for v in mesh.vertices])
        camera_vertices = np.array([transform_point(view, v) for v in world_vertices])
        clip_vertices = np.array([transform_point(projection, v) for v in camera_vertices])
        screen_vertices = self._to_screen_space(clip_vertices)
        for face_index, (i0, i1, i2) in enumerate(mesh.faces):
            local_normal = mesh.compute_face_normal(face_index)
            world_normal = transform_direction(model_matrix, local_normal)
            brightness = face_brightness(world_normal, light)
            char = brightness_to_char(brightness, self.ramp)
            self._rasterize_triangle(
                framebuffer,
                screen_vertices[i0], screen_vertices[i1], screen_vertices[i2],
                camera_vertices[i0][2], camera_vertices[i1][2], camera_vertices[i2][2],
                char,
            )
        return framebuffer

    def _to_screen_space(self, clip_vertices: np.ndarray) -> np.ndarray:
        screen = np.empty_like(clip_vertices)
        screen[:, 0] = (clip_vertices[:, 0] * 0.5 + 0.5) * (self.width - 1)
        screen[:, 1] = (1.0 - (clip_vertices[:, 1] * 0.5 + 0.5)) * (self.height - 1)
        screen[:, 2] = clip_vertices[:, 2]
        return screen

    def _rasterize_triangle(
        self,
        framebuffer: FrameBuffer,
        p0: np.ndarray,
        p1: np.ndarray,
        p2: np.ndarray,
        depth0: float,
        depth1: float,
        depth2: float,
        char: str,
    ) -> None:
        raise NotImplementedError("Implement barycentric triangle rasterization.")
