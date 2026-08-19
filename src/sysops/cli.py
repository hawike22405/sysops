import argparse
import json
from pathlib import Path

from .ascii_art import UnsupportedImageError, render_ascii
from .output import render_json, render_pretty
from .probes import collect_all


def add_ascii_subcommand(subparsers):
    p = subparsers.add_parser("ascii", help="Render an image as ASCII art")
    p.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path to an image file. If omitted, shows your OS logo.",
    )
    p.add_argument("--width", type=int, default=80, help="Output width in characters")
    p.add_argument(
        "--invert",
        action="store_true",
        help="Invert the brightness ramp (plain-text mode only)",
    )
    color_group = p.add_mutually_exclusive_group()
    color_group.add_argument(
        "--color",
        dest="color",
        action="store_true",
        default=None,
        help="Force 24-bit ANSI color rendering (like neofetch/fastfetch)",
    )
    color_group.add_argument(
        "--no-color",
        dest="color",
        action="store_false",
        help="Force plain grayscale character-ramp rendering",
    )
    p.set_defaults(func=_run_ascii)


def _run_ascii(args):
    try:
        print(
            render_ascii(
                args.image,
                width=args.width,
                invert=args.invert,
                color=args.color,
            )
        )
    except (UnsupportedImageError, ValueError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def build_parser():
    p = argparse.ArgumentParser(
        prog="sysops", description="System spec reporter (prototype)"
    )
    p.add_argument(
        "--format",
        choices=["pretty", "json", "compact"],
        default="pretty",
        help="output format",
    )
    p.add_argument(
        "--detail",
        choices=["brief", "full"],
        default="brief",
        help="detail level",
    )
    p.add_argument("--output", "-o", help="write output to file (path)")
    p.add_argument("--modules", help="comma-separated modules to run (default: all)")
    p.add_argument("--watch", type=int, help="repeat every N seconds")
    p.add_argument(
        "--no-root", action="store_true", help="do not attempt privileged probes"
    )

    p.add_argument(
        "--image",
        metavar="PATH",
        default=None,
        help="Use this image as the logo instead of the built-in OS logo",
    )
    p.add_argument(
        "--logo-width",
        type=int,
        default=28,
        help="Logo width in characters (default: 28)",
    )
    p.add_argument(
        "--no-logo",
        action="store_true",
        help="Don't show a logo beside the system summary",
    )
    logo_color_group = p.add_mutually_exclusive_group()
    logo_color_group.add_argument(
        "--logo-color",
        dest="logo_color",
        action="store_true",
        default=None,
        help="Force 24-bit ANSI color for the logo",
    )
    logo_color_group.add_argument(
        "--no-logo-color",
        dest="logo_color",
        action="store_false",
        help="Force plain grayscale logo",
    )

    subparsers = p.add_subparsers(dest="command")
    add_ascii_subcommand(subparsers)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "command", None) == "ascii":
        args.func(args)
        return

    modules = None
    if args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    data = collect_all(detail=args.detail, modules=modules, no_root=args.no_root)

    def build_logo():
        if args.no_logo:
            return None
        try:
            return render_ascii(
                args.image,
                width=args.logo_width,
                color=args.logo_color,
            )
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
