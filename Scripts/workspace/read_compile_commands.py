#!/usr/bin/env python3
"""Read or query a clangd compile_commands.json database."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT_DIR / "px4/px4_ws/build/compile_commands.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="read compile_commands.json or find the entry for a source file"
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="source path to find; an omitted path prints a database summary",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"compilation database (default: {DEFAULT_DATABASE})",
    )
    args = parser.parse_args()

    database = args.database.expanduser().resolve()
    try:
        entries = json.loads(database.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"compilation database not found: {database}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f"invalid compilation database {database}: {error}", file=sys.stderr)
        return 2

    if not isinstance(entries, list):
        print(f"compilation database must contain a JSON array: {database}", file=sys.stderr)
        return 2

    if args.source is None:
        print(json.dumps({"database": str(database), "entries": len(entries)}, indent=2))
        return 0

    source = Path(args.source).expanduser()
    if source.is_absolute() or source.exists():
        expected = str(source.resolve())
        matches = [entry for entry in entries if entry.get("file") == expected]
    elif len(source.parts) == 1:
        matches = [
            entry
            for entry in entries
            if Path(entry.get("file", "")).name == source.name
        ]
    else:
        suffix = source.as_posix()
        matches = [
            entry
            for entry in entries
            if Path(entry.get("file", "")).as_posix().endswith(suffix)
        ]

    if not matches:
        print(f"no compile command found for: {args.source}", file=sys.stderr)
        return 1

    print(json.dumps(matches, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
