from __future__ import annotations

import numpy as np

from sysops.features.ascii3d.geometry import Mesh
from sysops.features.ascii3d.viewer import Viewer, ViewerConfig


def build_unit_cube() -> Mesh:
    vertices = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
    ], dtype=np.float64)
    faces = np.array([
        (0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
        (0, 4, 5), (0, 5, 1), (3, 2, 6), (3, 6, 7),
        (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2),
    ], dtype=np.int64)
    return Mesh(vertices=vertices, faces=faces)


if __name__ == "__main__":
    viewer = Viewer(config=ViewerConfig(terminal_width=80, terminal_height=30))
    viewer.load_mesh(build_unit_cube())
    viewer.yaw = 0.6
    viewer.pitch = 0.4
    print(viewer.render_frame())
