#!/usr/bin/env python3
"""Копирует SPA и .htaccess в public_html (document root рядом с backend/)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PUBLIC = ROOT / "backend" / "public"
PUBLIC_HTML = ROOT / "public_html"
INDEX_STUB = Path(__file__).resolve().parent / "public_html_index.php"


def main() -> int:
    if not (BACKEND_PUBLIC / "spa-index.html").is_file():
        print("Сначала: python tools/deploy_web.py", file=sys.stderr)
        return 1

    PUBLIC_HTML.mkdir(parents=True, exist_ok=True)

    for name in (".htaccess", "robots.txt", "favicon.ico", "spa-index.html"):
        src = BACKEND_PUBLIC / name
        if src.is_file():
            shutil.copy2(src, PUBLIC_HTML / name)

    assets_src = BACKEND_PUBLIC / "assets"
    assets_dst = PUBLIC_HTML / "assets"
    if assets_dst.is_dir():
        shutil.rmtree(assets_dst)
    if assets_src.is_dir():
        shutil.copytree(assets_src, assets_dst)

    shutil.copy2(INDEX_STUB, PUBLIC_HTML / "index.php")

    print(f"OK: {PUBLIC_HTML} (index.php -> ../backend/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
