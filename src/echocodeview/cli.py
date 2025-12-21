import argparse
import os
import sys

from .server import start_document_web_server


def build_parser():
    parser = argparse.ArgumentParser(
        prog="echocodeview",
        description="Local markdown reader with web UI.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Root directory path",
    )
    parser.add_argument(
        "--dir",
        dest="root",
        help="Root directory path",
    )
    parser.add_argument(
        "--file",
        dest="entry",
        help="Markdown entry file (inside root)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port number",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open browser automatically",
    )
    return parser


def parse_args(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    root_dir = args.root or args.path or os.getcwd()
    return parser, {
        "serve": True,
        "root_dir": root_dir,
        "entry": args.entry,
        "host": args.host,
        "port": args.port,
        "open_browser": not args.no_open,
    }


def main(argv=None):
    parser, config = parse_args(argv or sys.argv[1:])
    try:
        start_document_web_server(
            root_dir=config["root_dir"],
            entry_path=config["entry"],
            host=config["host"],
            port=config["port"],
            open_browser=config["open_browser"],
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
