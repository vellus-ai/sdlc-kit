#!/usr/bin/env python3
"""Manage milestones with RAG status in 03-development/MILESTONES.md."""
import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path


def _rag_status(target_date_str: str, progress_pct: int) -> str:
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        today = date.today()
        days_left = (target - today).days
        if days_left < 0:
            return "red"
        if progress_pct >= 80 and days_left >= 7:
            return "green"
        if progress_pct < 40 and days_left <= 14:
            return "red"
        return "amber"
    except ValueError:
        return "amber"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--milestone-name", required=True)
    parser.add_argument("--target-date", default="")
    parser.add_argument("--epics", default="", help="Comma-separated epic names")
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true", help="Show RAG status of all milestones")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root
    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    milestones_file = vault / "03-development" / "MILESTONES.md"
    today = date.today().isoformat()

    if args.status:
        if not milestones_file.exists():
            print(json.dumps({"status": "ok", "milestones": [], "overall_rag": "green"}))
            return
        content = milestones_file.read_text(encoding="utf-8")
        milestones = []
        current: dict = {}
        for line in content.splitlines():
            if line.startswith("## ") and not line.startswith("## Milestones"):
                if current:
                    milestones.append(current)
                current = {"name": line.lstrip("# ").strip()}
            elif current:
                st_m = re.match(r"\*\*Status:\*\*\s*(.+)", line)
                if st_m:
                    st = st_m.group(1).lower()
                    if "green" in st or "🟢" in st:
                        current["rag"] = "green"
                    elif "red" in st or "🔴" in st:
                        current["rag"] = "red"
                    else:
                        current["rag"] = "amber"
                prog_m = re.match(r"\*\*Progresso:\*\*\s*(\d+)%", line)
                if prog_m:
                    current["progress"] = int(prog_m.group(1))
                target_m = re.match(r"\*\*Data-alvo:\*\*\s*(.+)", line)
                if target_m:
                    current["target_date"] = target_m.group(1).strip()
        if current:
            milestones.append(current)
        rag_order = {"red": 2, "amber": 1, "green": 0}
        worst = max((m.get("rag", "green") for m in milestones), key=lambda r: rag_order.get(r, 0), default="green")
        print(json.dumps({"status": "ok", "milestones": milestones, "overall_rag": worst}))
        return

    rag = _rag_status(args.target_date, 0)
    rag_emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(rag, "🟡")
    epics_list = [e.strip() for e in args.epics.split(",") if e.strip()]
    entry = f"\n## {args.milestone_name}\n\n**Status:** {rag_emoji} {rag.capitalize()}\n**Data-alvo:** {args.target_date}\n**Épicos:** {', '.join(epics_list) or '—'}\n**Progresso:** 0%\n"

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "milestone_name": args.milestone_name, "rag": rag}))
        return

    if not milestones_file.exists():
        milestones_file.parent.mkdir(parents=True, exist_ok=True)
        milestones_file.write_text(
            "---\ntitle: \"Milestones\"\ntype: milestone\nstatus: active\nphase: \"03\"\ncreated: " + today + "\nupdated: " + today + "\n---\n\n# Milestones\n",
            encoding="utf-8"
        )

    with open(milestones_file, "a", encoding="utf-8") as f:
        f.write(entry)

    print(json.dumps({"status": "ok", "milestone_name": args.milestone_name, "rag": rag, "file": str(milestones_file)}))


if __name__ == "__main__":
    main()
