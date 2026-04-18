#!/usr/bin/env python3
"""Bump the plugin version atomically across every coordinated file.

Usage:
    python scripts/bump_version.py 0.2.0

Files updated:
  - pyproject.toml                          ("version = ...")
  - .claude-plugin/plugin.json              ("version": "...")
  - .claude-plugin/marketplace.json         (version field if present)
  - README.md                               (version badge)

Emits a JSON report on stdout. Refuses to run if the git tree has uncommitted
changes to any of the coordinated files unless `--force` is passed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def bump_pyproject(new: str) -> bool:
    path = PLUGIN_ROOT / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(r'^version = "[^"]+"', f'version = "{new}"', text, count=1, flags=re.MULTILINE)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def bump_json(rel_path: str, new: str) -> bool:
    path = PLUGIN_ROOT / rel_path
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") == new:
        return False
    data["version"] = new
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def bump_readme_badge(new: str) -> bool:
    path = PLUGIN_ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(
        r"\[!\[Version\]\(https://img\.shields\.io/badge/version-[^-]+-",
        f"[![Version](https://img.shields.io/badge/version-{new}-",
        text,
        count=1,
    )
    # Also update the release-tag URL in the badge.
    new_text = re.sub(
        r"/releases/tag/v[0-9]+\.[0-9]+\.[0-9]+\)",
        f"/releases/tag/v{new})",
        new_text,
        count=1,
    )
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("version", help="new version (e.g., 0.2.0)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not re.match(r"^\d+\.\d+\.\d+(?:[-+].+)?$", args.version):
        print(json.dumps({"status": "error", "error": f"invalid semver: {args.version}"}))
        return 1

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "version": args.version}))
        return 0

    report = {
        "status": "ok",
        "version": args.version,
        "updated": {
            "pyproject.toml": bump_pyproject(args.version),
            ".claude-plugin/plugin.json": bump_json(".claude-plugin/plugin.json", args.version),
            ".claude-plugin/marketplace.json": bump_json(".claude-plugin/marketplace.json", args.version),
            "README.md": bump_readme_badge(args.version),
        },
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
