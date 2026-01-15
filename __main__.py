"""Entry point for MediaDownloader package.

Usage examples:
- python -m media_downloader images
- python -m media_downloader yts
- python -m media_downloader rarbg
- python -m media_downloader porn
- python -m media_downloader bitmagnet
"""
import argparse
import runpy
from typing import Dict


MODULE_MAP: Dict[str, str] = {
    "images": "media_downloader.images",
    "yts": "media_downloader.yts",
    "rarbg": "media_downloader.rarbg",
    "porn": "media_downloader.porn",
    "bitmagnet": "media_downloader.bitmagnet",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="MediaDownloader launcher")
    parser.add_argument(
        "command",
        choices=MODULE_MAP.keys(),
        help="Which downloader to run",
    )
    args, unknown = parser.parse_known_args()

    module_name = MODULE_MAP[args.command]
    runpy.run_module(module_name, run_name="__main__")


if __name__ == "__main__":
    main()
