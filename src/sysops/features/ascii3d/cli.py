import argparse
from pathlib import Path

from .viewer import Viewer, ViewerConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="3D ASCII Image Viewer")
    parser.add_argument("image", help="Path to an image file")
    parser.add_argument("--width", type=int, default=100, help="Terminal width")
    parser.add_argument("--height", type=int, default=35, help="Terminal height")
    parser.add_argument("--scale", type=float, default=1.2, help="Depth extrusion scale (default: 1.2)")
    parser.add_argument("--no-color", action="store_true", help="Disable color (plain ASCII)")
    parser.add_argument("--style", type=str, choices=["chars", "blocks"], default="blocks", help="Rendering style")
    args = parser.parse_args()

    run_viewer(args.image, args.width, args.height, args.scale, use_color=not args.no_color, style=args.style)

def run_viewer(image_path: str, width: int = 100, height: int = 35, scale: float = 1.2, use_color: bool = True, style: str = "blocks") -> None:
    config = ViewerConfig(
        terminal_width=width,
        terminal_height=height,
        depth_scale=scale,
        use_color=use_color,
        style=style
    )
    viewer = Viewer(config=config)
    
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise SystemExit(f"Error: No such image file: {path}")

    try:
        viewer.load_image(path)
        viewer.run()
    except Exception as exc:
        raise SystemExit(f"Error: {exc}")
