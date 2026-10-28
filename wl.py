#!/usr/bin/env python3
"""wl - list locally installed Wallpaper Engine wallpapers

Reads project.json from each wallpaper folder and maps workshop IDs to
titles, types, tags, ...

Requires: rich (pip install "rich>=13,<15")

Usage:
    wl                     list all wallpapers
    wl -t video            show video wallpapers only
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

try:
    from rich import box
    from rich.console import Console
    from rich.filesize import decimal
    from rich.table import Table
except ImportError:
    sys.exit('wl requires rich: python3 -m pip install "rich>=13,<15"')

DEFAULT_ROOTS = [
    Path.home() / "壁纸",
    Path.home() / "Wallpapers",
    Path.home() / ".steam/steam/steamapps/workshop/content/431960",
    Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/workshop/content/431960",
    Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / "Steam/steamapps/workshop/content/431960",
]

def find_root(explicit=None):
    if explicit:
        return Path(explicit).expanduser()
    for root in DEFAULT_ROOTS:
        if root.is_dir():
            return root
    return DEFAULT_ROOTS[0]


def directory_size(path):
    total = 0
    for current, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(os.path.join(current, name)).st_size
            except OSError:
                pass
    return total


def load_wallpapers(root):
    items = []
    if not root.is_dir():
        sys.exit("Wallpaper directory not found: %s" % root)
    for folder in sorted(root.iterdir(), key=lambda p: p.name):
        if not folder.is_dir():
            continue
        project = folder / "project.json"
        if not project.is_file():
            continue
        try:
            data = json.loads(project.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        items.append({
            "id": folder.name,
            "title": data.get("title") or "Untitled",
            "type": data.get("type") or "?",
            "tags": ", ".join(data.get("tags") or []),
            "size": directory_size(folder),
        })
    return items


def print_table(items, console):
    table = Table(
        box=box.SIMPLE_HEAD,
        show_edge=False,
        pad_edge=False,
        padding=(0, 1),
        expand=True,
        header_style="dim",
        border_style="dim",
    )
    table.add_column("ID", style="cyan", no_wrap=True, width=10)
    table.add_column("TITLE", style="bold", no_wrap=True, overflow="ellipsis", ratio=3)
    table.add_column("TYPE", style="yellow", no_wrap=True, width=5)
    table.add_column("TAGS", no_wrap=True, overflow="ellipsis", max_width=30, ratio=2)
    table.add_column("SIZE", justify="right", no_wrap=True, width=8)

    for item in items:
        table.add_row(
            item["id"],
            item["title"],
            item["type"],
            item["tags"],
            decimal(item["size"], precision=1, separator=""),
        )

    console.print(table)

    total = sum(item["size"] for item in items)
    console.print()
    console.print(
        "Total: %d wallpaper%s, %s"
        % (len(items), "" if len(items) == 1 else "s", decimal(total, precision=1, separator="")),
        style="dim",
    )


def main():
    parser = argparse.ArgumentParser(
        prog="wl",
        description="List locally installed Wallpaper Engine wallpapers (ID, title, type, tags, size)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  wl                    list all wallpapers\n"
               "  wl -t video           show video wallpapers only",
    )
    parser.add_argument("-t", "--type", help="filter by type, e.g. scene / video / web")
    parser.add_argument("--root", help="wallpaper root directory (default: auto-detect)")
    parser.add_argument("--no-color", action="store_true", help="disable colors")
    args = parser.parse_args()

    items = load_wallpapers(find_root(args.root))
    if args.type:
        items = [item for item in items if item["type"].casefold() == args.type.casefold()]

    items.sort(key=lambda item: item["title"].casefold())

    if not items:
        sys.exit("No matching wallpapers")

    console = Console(
        width=shutil.get_terminal_size((120, 24)).columns or 120,
        no_color=args.no_color,
        force_terminal=False if args.no_color else None,
        highlight=False,
        markup=False,
    )
    print_table(items, console)


if __name__ == "__main__":
    main()
