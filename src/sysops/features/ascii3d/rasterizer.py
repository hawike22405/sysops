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
    colors: np.ndarray = field(init=False)  # (H, W, 3) uint8 RGB per pixel

    def __post_init__(self) -> None:
        self.clear()

    def clear(self, background_char: str = " ") -> None:
        self.chars = np.full((self.height, self.width), background_char, dtype="<U1")
        self.depth = np.full((self.height, self.width), np.inf, dtype=np.float64)
        self.colors = np.zeros((self.height, self.width, 3), dtype=np.uint8)


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
        clip_vertices = np.array([projection @ np.array([v[0], v[1], v[2], 1.0]) for v in camera_vertices])
        visible = np.ones(len(clip_vertices), dtype=bool)
        for index, value in enumerate(clip_vertices):
            w = value[3]
            if abs(w) < 1e-12:
                visible[index] = False
            else:
                clip_vertices[index, :3] /= w
                clip_vertices[index, 3] = 1.0
        screen_vertices = self._to_screen_space(clip_vertices[:, :3])

        has_colors = mesh.colors is not None
        for face_index, (i0, i1, i2) in enumerate(mesh.faces):
            if not (visible[i0] and visible[i1] and visible[i2]):
                continue
            local_normal = mesh.compute_face_normal(face_index)
            world_normal = transform_direction(model_matrix, local_normal)
            brightness = face_brightness(world_normal, light)
            char = brightness_to_char(brightness, self.ramp)

            c0 = mesh.colors[i0] if has_colors else None
            c1 = mesh.colors[i1] if has_colors else None
            c2 = mesh.colors[i2] if has_colors else None

            self._rasterize_triangle(
                framebuffer,
                screen_vertices[i0], screen_vertices[i1], screen_vertices[i2],
                camera_vertices[i0][2], camera_vertices[i1][2], camera_vertices[i2][2],
                char,
                brightness,
                c0, c1, c2,
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
        brightness: float = 1.0,
        c0: np.ndarray | None = None,
        c1: np.ndarray | None = None,
        c2: np.ndarray | None = None,
    ) -> None:
        x0, y0 = float(p0[0]), float(p0[1])
        x1, y1 = float(p1[0]), float(p1[1])
        x2, y2 = float(p2[0]), float(p2[1])
        area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        if abs(area) < 1e-9:
            return

        min_x = max(0, int(np.floor(min(x0, x1, x2))))
        max_x = min(framebuffer.width - 1, int(np.ceil(max(x0, x1, x2))))
        min_y = max(0, int(np.floor(min(y0, y1, y2))))
        max_y = min(framebuffer.height - 1, int(np.ceil(max(y0, y1, y2))))

        has_color = c0 is not None

        for y in range(min_y, max_y + 1):
            py = y + 0.5
            for x in range(min_x, max_x + 1):
                px = x + 0.5
                w0 = ((x1 - x0) * (py - y0) - (y1 - y0) * (px - x0)) / area
                w1 = ((x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)) / area
                w2 = 1.0 - w0 - w1
                if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                    continue
                depth = w0 * depth2 + w1 * depth0 + w2 * depth1
                if depth < framebuffer.depth[y, x]:
                    framebuffer.depth[y, x] = depth
                    framebuffer.chars[y, x] = char
                    if has_color:
                        # Interpolate vertex colors and modulate by lighting brightness
                        r = int(np.clip((w2 * c0[0] + w0 * c2[0] + w1 * c1[0]) * brightness, 0, 255))
                        g = int(np.clip((w2 * c0[1] + w0 * c2[1] + w1 * c1[1]) * brightness, 0, 255))
                        b = int(np.clip((w2 * c0[2] + w0 * c2[2] + w1 * c1[2]) * brightness, 0, 255))
                        framebuffer.colors[y, x] = (r, g, b)
