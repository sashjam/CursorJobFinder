#!/usr/bin/env python3
"""Сборка Vue SPA и копирование в backend/public (без dev-серверов)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
PUBLIC = ROOT / "backend" / "public"
ASSETS = PUBLIC / "assets"
SPA_INDEX = PUBLIC / "spa-index.html"


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not (FRONTEND / "package.json").is_file():
        print("frontend/package.json not found", file=sys.stderr)
        return 1

    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    if not (FRONTEND / "node_modules").is_dir():
        run([npm, "ci"], cwd=FRONTEND)
    run([npm, "run", "build"], cwd=FRONTEND)

    if not DIST.is_dir():
        print("frontend/dist missing after build", file=sys.stderr)
        return 1

    dist_index = DIST / "index.html"
    if not dist_index.is_file():
        print("frontend/dist/index.html missing", file=sys.stderr)
        return 1

    if ASSETS.is_dir():
        shutil.rmtree(ASSETS)
    dist_assets = DIST / "assets"
    if dist_assets.is_dir():
        shutil.copytree(dist_assets, ASSETS)
    else:
        ASSETS.mkdir(parents=True, exist_ok=True)

    shutil.copy2(dist_index, SPA_INDEX)

    for name in ("favicon.ico", "favicon.svg", "robots.txt"):
        src = DIST / name
        if src.is_file():
            shutil.copy2(src, PUBLIC / name)

    print(f"OK: SPA -> {SPA_INDEX}, assets -> {ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
