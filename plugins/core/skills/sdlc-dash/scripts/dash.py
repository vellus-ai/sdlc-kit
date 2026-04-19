#!/usr/bin/env python3
"""Open the SDLC Kit dashboard in the default browser."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Open the SDLC Kit dashboard")
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root

    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({
            "status": "error",
            "message": "vault not found — run /sdlc-kit:init first",
        }))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    dashboard = vault / "dashboard.html"
    if not dashboard.exists():
        print(json.dumps({
            "status": "error",
            "message": f"dashboard.html not found in {vault} — run /sdlc-kit:sync to restore it",
        }))
        sys.exit(1)

    dashboard_path = str(dashboard.resolve())

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "path": dashboard_path}))
        return

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(dashboard_path)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.run(["open", dashboard_path], check=False)
        else:
            subprocess.run(["xdg-open", dashboard_path], check=False)
        opened = True
    except Exception:
        opened = False

    print(json.dumps({
        "status": "ok",
        "path": dashboard_path,
        "opened": opened,
    }))


if __name__ == "__main__":
    main()
