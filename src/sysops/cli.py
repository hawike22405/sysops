import argparse
import json
from pathlib import Path

from .ascii_art import UnsupportedImageError, render_ascii
from .config import config_path, load_config, save_config
from .dino import run_game
from .features.achievements import check_achievements, list_all_badges
from .features.benchmark import print_results, run_benchmark
from .features.interactive_menu import run_interactive_menu
from .features.updater import update
from .output import render_json, render_pretty
from .probes import collect_all


def add_ascii_subcommand(subparsers):
    parser = subparsers.add_parser("ascii", help="Render an image as ASCII art")
    parser.add_argument("image", nargs="?", default=None, help="Path to an image file. If omitted, shows your OS logo.")
    parser.add_argument("--width", type=int, default=80, help="Output width in characters")
    parser.add_argument("--invert", action="store_true", help="Invert the brightness ramp (plain-text mode only)")
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument("--color", dest="color", action="store_true", default=None, help="Force 24-bit ANSI color rendering")
    color_group.add_argument("--no-color", dest="color", action="store_false", help="Force plain grayscale character-ramp rendering")
    parser.add_argument("--style", choices=["chars", "blocks"], default="chars", help="Color rendering style")
    parser.set_defaults(func=_run_ascii)


def _run_ascii(args):
    try:
        print(render_ascii(args.image, width=args.width, invert=args.invert, color=args.color, style=args.style))
    except (UnsupportedImageError, ValueError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def add_logo_subcommand(subparsers):
    parser = subparsers.add_parser("logo", help="Manage the default logo shown beside `sysops`")
    logo_sub = parser.add_subparsers(dest="logo_command")
    set_parser = logo_sub.add_parser("set", help="Save an image as your default logo")
    set_parser.add_argument("image", help="Path to an image file")
    set_parser.add_argument("--width", type=int, help="Default logo width in characters")
    color_group = set_parser.add_mutually_exclusive_group()
    color_group.add_argument("--color", dest="color", action="store_true", default=None, help="Always render this logo in 24-bit ANSI color")
    color_group.add_argument("--no-color", dest="color", action="store_false", help="Always render this logo in plain grayscale")
    set_parser.add_argument("--style", choices=["chars", "blocks"], default=None, help="Color rendering style")
    set_parser.set_defaults(func=_run_logo_set)
    clear_parser = logo_sub.add_parser("clear", help="Remove the saved logo")
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
    print("Cleared custom logo. 'sysops' will show the built-in OS logo again.")


def _run_logo_show(_args):
    cfg = load_config()
    if not cfg.get("image"):
        print(f"No custom logo set (using built-in OS logo).\nConfig file: {config_path()}")
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
    parser = subparsers.add_parser("dashboard", aliases=["menu"], help="Open the live interactive system dashboard")
    parser.set_defaults(func=lambda _args: run_interactive_menu())


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
    parser = subparsers.add_parser("achievements", help="Check or list system achievement badges")
    parser.add_argument("--list", action="store_true", help="List all badges and their status")
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
    parser.set_defaults(func=lambda _args: update())


def build_parser():
    parser = argparse.ArgumentParser(prog="sysops", description="System spec reporter")
    parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty", help="output format")
    parser.add_argument("--detail", choices=["brief", "full"], default="brief", help="detail level")
    parser.add_argument("--output", "-o", help="write output to file")
    parser.add_argument("--modules", help="comma-separated modules to run")
    parser.add_argument("--watch", type=int, help="repeat every N seconds")
    parser.add_argument("--no-root", action="store_true", help="do not attempt privileged probes")
    parser.add_argument("--play", action="store_true", help="play the Dino run game")
    parser.add_argument("--image", metavar="PATH", default=None, help="Use this image as the logo")
    parser.add_argument("--logo-width", type=int, default=None, help="Logo width in characters")
    parser.add_argument("--no-logo", action="store_true", help="Do not show a logo")
    logo_color_group = parser.add_mutually_exclusive_group()
    logo_color_group.add_argument("--logo-color", dest="logo_color", action="store_true", default=None, help="Force 24-bit ANSI color for the logo")
    logo_color_group.add_argument("--no-logo-color", dest="logo_color", action="store_false", help="Force plain grayscale logo")
    parser.add_argument("--logo-style", choices=["chars", "blocks"], default=None, help="Logo color style")
    subparsers = parser.add_subparsers(dest="command")
    add_ascii_subcommand(subparsers)
    add_logo_subcommand(subparsers)
    add_play_subcommand(subparsers)
    add_dashboard_subcommand(subparsers)
    add_benchmark_subcommand(subparsers)
    add_achievements_subcommand(subparsers)
    add_update_subcommand(subparsers)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.play or args.command == "play":
        run_game()
        return
    if args.command == "ascii":
        args.func(args)
        return
    if args.command == "logo":
        if getattr(args, "func", None):
            args.func(args)
        else:
            parser.error("usage: sysops logo {set,clear,show}")
        return
    if args.command in {"dashboard", "menu", "benchmark", "achievements", "update"}:
        result = args.func(args)
        if args.command == "update" and result:
            raise SystemExit(result)
        return

    modules = None
    if args.modules:
        modules = [item.strip() for item in args.modules.split(",") if item.strip()]
    data = collect_all(detail=args.detail, modules=modules, no_root=args.no_root)

    def build_logo():
        if args.no_logo:
            return None
        cfg = load_config()
        image = args.image if args.image is not None else cfg.get("image")
        width = args.logo_width if args.logo_width is not None else cfg.get("width", 28)
        color = args.logo_color if args.logo_color is not None else cfg.get("color")
        style = args.logo_style if args.logo_style is not None else cfg.get("style", "chars")
        try:
            return render_ascii(image, width=width, color=color, style=style)
        except (UnsupportedImageError, ValueError) as exc:
            print(f"Warning: couldn't render logo: {exc}")
            return None

    out_text = None
    if args.format == "pretty":
        render_pretty(data, detail=args.detail, logo=build_logo())
    elif args.format == "compact":
        render_pretty(data, detail="brief", logo=build_logo())
    else:
        out_text = render_json(data)
        print(out_text)
    if args.output:
        path = Path(args.output)
        if out_text is None:
            out_text = json.dumps(data, indent=2)
        path.write_text(out_text, encoding="utf-8")
        print(f"Wrote output to {path}")
