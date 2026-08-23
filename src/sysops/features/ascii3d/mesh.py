from __future__ import annotations

import numpy as np

from .geometry import Mesh


def generate_mesh_from_depth(depth: np.ndarray, depth_scale: float = 1.0) -> Mesh:
    height, width = depth.shape
    vertices = []
    faces = []
    for y in range(height):
        for x in range(width):
            nx = (x / max(width - 1, 1)) * 2.0 - 1.0
            ny = 1.0 - (y / max(height - 1, 1)) * 2.0
            vertices.append((nx, ny, float(depth[y, x]) * depth_scale))
    for y in range(height - 1):
        for x in range(width - 1):
            a = y * width + x
            b = a + 1
            c = a + width
            d = c + 1
            faces.extend(((a, b, d), (a, d, c)))
    return Mesh(vertices=np.asarray(vertices, dtype=np.float64), faces=np.asarray(faces, dtype=np.int64))


def simplify_mesh(mesh: Mesh, target_vertices: int) -> Mesh:
    raise NotImplementedError("Implement mesh simplification/adaptive resolution.")
