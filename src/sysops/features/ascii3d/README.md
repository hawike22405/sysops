# ascii3d — SysOps 3D ASCII/Unicode renderer

Modular, CPU-based pipeline that turns a 2D image (or a plain mesh, like a test cube) into an interactive 3D ASCII/Unicode terminal visualization.

```
image.py → depth.py → mesh.py → geometry.py/camera.py → rasterizer.py → terminal.py → viewer.py
```

This subsystem is intentionally a foundation scaffold. Image preprocessing, brightness-depth generation, mesh construction, geometry primitives, and the pipeline skeleton are present. Camera projection, triangle rasterization, lighting, interactive terminal input, and the viewer loop remain implementation milestones.

## Suggested build order

1. Height-field prototype.
2. Software renderer and cube validation.
3. ASCII shading.
4. Image → 2.5D.
5. Interactive controls.
6. ANSI color.
7. AI depth.
8. Mesh simplification/caching/adaptive resolution.
9. Expose `sysops 3d` after the viewer is functional.

## Dependencies

This subsystem uses `numpy` and `Pillow` in addition to normal SysOps dependencies.
