from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ascii_art import UnsupportedImageError, render_ascii
from .config import config_path, load_config, save_config
from .dino import run_game
from .features.achievements import check_achievements, list_all_badges
from .features.benchmark import print_results, run_benchmark
from .features.htop_view import run_htop_view
from .features.interactive_menu import run_interactive_menu
from .features.os_logo import DEFAULT_FPS, animate_os_logo, detect_os, render_os_frame
from .features.updater import run_update
from .output import render, render_json
from .probes import collect_all


def add_ascii_subcommand(subparsers):
    parser = subparsers.add_parser("ascii", help="Render an image as ASCII art")
    parser.add_argument("image", nargs="?", default=None, help="Image path; omitted uses the detected OS logo")
    parser.add_argument("--width", type=int, default=80, help="Output width in characters")
    parser.add_argument("--invert", action="store_true", help="Invert the brightness ramp")
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument("--color", dest="color", action="store_true", default=None, help="Force ANSI color")
    color_group.add_argument("--no-color", dest="color", action="store_false", help="Disable ANSI color")
    parser.add_argument("--style", choices=["chars", "blocks", "image"], default="chars", help="Rendering style")
    parser.add_argument("--animate", action="store_true", help="Animate the built-in OS logo")
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS, help="Animation frame rate")
    parser.set_defaults(func=_run_ascii)


def _run_ascii(args):
    try:
        if args.animate and args.image is not None:
            raise ValueError("--animate cannot be used with an image path")
        if args.animate:
            animate_os_logo(width=args.width, fps=args.fps)
            return
        print(render_ascii(args.image, width=args.width, invert=args.invert, color=args.color, style=args.style))
    except (UnsupportedImageError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}")


def add_3d_subcommand(subparsers):
    parser = subparsers.add_parser("3d", help="Render an image in interactive 3D ASCII")
    parser.add_argument("image", help="Path to an image file")
    parser.add_argument("--width", type=int, default=100, help="Terminal width")
    parser.add_argument("--height", type=int, default=35, help="Terminal height")
    parser.add_argument("--scale", type=float, default=1.2, help="Depth extrusion scale")
    parser.add_argument("--no-color", action="store_true", help="Disable color")
    parser.set_defaults(func=_run_3d)


def _run_3d(args):
    from .features.ascii3d.cli import run_viewer
    run_viewer(args.image, args.width, args.height, args.scale, use_color=not args.no_color)


def add_logo_subcommand(subparsers):
    parser = subparsers.add_parser("logo", help="Manage the default custom image logo")
    logo_sub = parser.add_subparsers(dest="logo_command")

    set_parser = logo_sub.add_parser("set", help="Save an image as the default logo")
    set_parser.add_argument("image", help="Path to an image file")
    set_parser.add_argument("--width", type=int, help="Default logo width")
    color_group = set_parser.add_mutually_exclusive_group()
    color_group.add_argument("--color", dest="color", action="store_true", default=None, help="Force color")
    color_group.add_argument("--no-color", dest="color", action="store_false", help="Disable color")
    set_parser.add_argument("--style", choices=["chars", "blocks", "image"], default=None, help="Rendering style")
    set_parser.set_defaults(func=_run_logo_set)

    clear_parser = logo_sub.add_parser("clear", help="Remove the saved custom logo")
    clear_parser.set_defaults(func=_run_logo_clear)

    show_parser = logo_sub.add_parser("show", help="Show saved logo settings")
    show_parser.set_defaults(func=_run_logo_show)


def _run_logo_set(args):
    path = Path(args.image).expanduser()
    if not path.is_file():
        raise SystemExit(f"Error: No such image file: {path}")
    if args.width is not None and args.width <= 0:
        raise SystemExit("Error: width must be greater than 0")
    try:
        render_ascii(str(path), width=4, color=False)
    except (UnsupportedImageError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}")
    cfg = load_config()
    cfg["image"] = str(path.resolve())
    if args.width is not None:
        cfg["width"] = args.width
    if args.color is not None:
        cfg["color"] = args.color
    if args.style is not None:
        cfg["style"] = args.style
    save_config(cfg)
    print(f"Saved default logo: {cfg['image']}")


def _run_logo_clear(_args):
    cfg = load_config()
    if not cfg.get("image"):
        print("No custom logo is set.")
        return
    for key in ("image", "width", "color", "style"):
        cfg.pop(key, None)
    save_config(cfg)
    print("Cleared custom logo. Built-in OS animation is restored.")


def _run_logo_show(_args):
    cfg = load_config()
    if not cfg.get("image"):
        print(f"No custom logo set; using detected {detect_os()} logo.\nConfig file: {config_path()}")
        return
    print(f"Image: {cfg['image']}")
    print(f"Width: {cfg.get('width', 28)}")
    print(f"Color: {cfg.get('color', 'auto')}")
    print(f"Style: {cfg.get('style', 'chars')}")
    print(f"Config file: {config_path()}")


def add_play_subcommand(subparsers):
    parser = subparsers.add_parser("play", help="Play the Dino run game")
    parser.set_defaults(func=lambda _args: run_game())


def add_dashboard_subcommand(subparsers):
    parser = subparsers.add_parser("dashboard", aliases=["menu"], help="Open the live interactive dashboard")
    parser.set_defaults(func=lambda _args: run_interactive_menu())


def add_monitor_subcommand(subparsers):
    parser = subparsers.add_parser("monitor", aliases=["htop"], help="Open the htop-style process monitor")
    parser.add_argument("--refresh", type=float, default=1.5, help="Redraw interval in seconds")
    parser.add_argument("--sort", choices=["cpu", "mem", "pid", "name"], default="cpu", help="Initial process sort")
    parser.set_defaults(func=_run_monitor)


def _run_monitor(args):
    if args.refresh <= 0:
        raise SystemExit("Error: --refresh must be greater than 0")
    run_htop_view(refresh_seconds=args.refresh, sort_key=args.sort)


def add_benchmark_subcommand(subparsers):
    parser = subparsers.add_parser("benchmark", help="Run a quick CPU and disk benchmark")
    parser.add_argument("--duration", type=float, default=0.33, help="Seconds per benchmark stage")
    parser.add_argument("--no-multi", action="store_true", help="Skip the multi-core CPU benchmark")
    parser.set_defaults(func=_run_benchmark)


def _run_benchmark(args):
    if args.duration <= 0:
        raise SystemExit("Error: --duration must be greater than 0")
    print_results(run_benchmark(args.duration, include_multi_core=not args.no_multi))


def add_achievements_subcommand(subparsers):
    parser = subparsers.add_parser("achievements", help="Check or list achievement badges")
    parser.add_argument("--list", action="store_true", help="List all badges")
    parser.set_defaults(func=_run_achievements)


def _run_achievements(args):
    if args.list:
        list_all_badges()
        return
    found = check_achievements()
    if not found:
        print("No new achievements this run.")


def add_update_subcommand(subparsers):
    parser = subparsers.add_parser("update", help="Check for and install the latest SysOps update")
    parser.set_defaults(func=lambda _args: run_update())


def build_parser():
    parser = argparse.ArgumentParser(
        prog="sysops",
        description="Cross-platform terminal-first system information and operations toolkit",
    )
    parser.add_argument("--detail", choices=["brief", "full"], default="brief", help="Detail level")
    parser.add_argument("--output", "-o", help="Write JSON output to a file")
    parser.add_argument("--modules", help="Comma-separated modules: cpu,memory,disks,network,gpu,sensors")
    parser.add_argument("--watch", type=int, help="Repeat report every N seconds")
    parser.add_argument("--no-root", action="store_true", help="Do not attempt privileged probes")
    parser.add_argument("--play", action="store_true", help="Play the Dino game")
    parser.add_argument("--image", metavar="PATH", help="Use this image as the logo")
    parser.add_argument("--logo-width", type=int, default=None, help="Logo width in characters")
    parser.add_argument("--no-logo", action="store_true", help="Do not show a logo")
    parser.add_argument("--animate-logo", action="store_true", help="Animate the detected built-in OS logo")
    parser.add_argument("--logo-fps", type=float, default=DEFAULT_FPS, help="OS logo animation frame rate")
    logo_color_group = parser.add_mutually_exclusive_group()
    logo_color_group.add_argument("--logo-color", dest="logo_color", action="store_true", default=None, help="Force color")
    logo_color_group.add_argument("--no-logo-color", dest="logo_color", action="store_false", help="Disable color")
    parser.add_argument("--logo-style", choices=["chars", "blocks", "image"], default=None, help="Logo style for image logos")

    subparsers = parser.add_subparsers(dest="command")
    add_ascii_subcommand(subparsers)
    add_3d_subcommand(subparsers)
    add_logo_subcommand(subparsers)
    add_play_subcommand(subparsers)
    add_dashboard_subcommand(subparsers)
    add_monitor_subcommand(subparsers)
    add_benchmark_subcommand(subparsers)
    add_achievements_subcommand(subparsers)
    add_update_subcommand(subparsers)
    return parser


def _selected_modules(args) -> list[str] | None:
    if not args.modules:
        return None
    modules = [item.strip().lower() for item in args.modules.split(",") if item.strip()]
    valid = {"cpu", "memory", "disks", "network", "gpu", "sensors"}
    invalid = [item for item in modules if item not in valid]
    if invalid:
        raise SystemExit(f"Error: unknown module(s): {', '.join(invalid)}")
    return modules or None


def _show_report_once(args, parser):
    modules = _selected_modules(args)
    cfg = load_config()
    image_path = args.image or cfg.get("image")
    logo_width = args.logo_width or cfg.get("width", 28)
    logo_color = args.logo_color if args.logo_color is not None else cfg.get("color")
    logo_style = args.logo_style or cfg.get("style", "chars")

    if logo_width <= 0:
        parser.error("--logo-width must be greater than 0")

    data = collect_all(args.detail, modules, args.no_root)
    if args.output:
        Path(args.output).expanduser().write_text(render_json(data), encoding="utf-8")
        print(f"Report written to {Path(args.output).expanduser()}")
        return

    logo = None
    if not args.no_logo:
        if image_path:
            try:
                logo = render_ascii(image_path, width=logo_width, color=logo_color, style=logo_style)
            except (UnsupportedImageError, ValueError) as exc:
                print(f"Warning: {exc}; falling back to built-in OS logo.")
                logo = render_os_frame(detect_os(), width=min(logo_width, 40), color=True)
        else:
            if args.animate_logo:
                animate_os_logo(width=min(logo_width, 40), fps=args.logo_fps)
                logo = render_os_frame(detect_os(), width=min(logo_width, 40), color=True)
            else:
                logo = render_os_frame(detect_os(), width=min(logo_width, 40), color=True)
    render(data, logo=logo)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.play or args.command == "play":
        run_game()
        return

    if args.command in {"ascii", "3d"}:
        args.func(args)
        return

    if args.command == "logo":
        if getattr(args, "func", None):
            args.func(args)
        else:
            parser.error("usage: sysops logo {set,clear,show}")
        return

    if args.command in {"dashboard", "menu", "monitor", "htop", "benchmark", "achievements", "update"}:
        result = args.func(args)
        if args.command == "update" and result:
            raise SystemExit(result)
        return

    if args.logo_fps <= 0:
        parser.error("--logo-fps must be greater than 0")
    if args.watch is not None and args.watch <= 0:
        parser.error("--watch must be greater than 0")

    if args.watch:
        while True:
            _show_report_once(args, parser)
            import time
            time.sleep(args.watch)
    else:
        _show_report_once(args, parser)


if __name__ == "__main__":
    main()
