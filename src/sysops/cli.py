import argparse
import json
from pathlib import Path
from .probes import collect_all
from .output import render_pretty, render_json


def build_parser():
    p = argparse.ArgumentParser(prog="sysops", description="System spec reporter (prototype)")
    p.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty", help="output format")
    p.add_argument("--detail", choices=["brief", "full"], default="brief", help="detail level")
    p.add_argument("--output", "-o", help="write output to file (path)")
    p.add_argument("--modules", help="comma-separated modules to run (default: all)")
    p.add_argument("--watch", type=int, help="repeat every N seconds")
    p.add_argument("--no-root", action="store_true", help="do not attempt privileged probes")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    modules = None
    if args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    data = collect_all(detail=args.detail, modules=modules, no_root=args.no_root)

    out_text = None
    if args.format == "pretty":
        render_pretty(data, detail=args.detail)
    elif args.format == "compact":
        render_pretty(data, detail="brief")
    else:
        out_text = render_json(data)
        print(out_text)

    if args.output:
        path = Path(args.output)
        if out_text is None:
            out_text = json.dumps(data, indent=2)
        path.write_text(out_text, encoding="utf-8")
        print(f"Wrote output to {path}")
