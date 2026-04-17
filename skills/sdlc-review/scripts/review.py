#!/usr/bin/env python3
"""Phase completeness checklist."""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

_REQUIRED_FRONTMATTER = {"title", "type", "status", "phase"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root
    from core.parser import parse
    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "message": "would check phase completeness"}))
        return

    issues = []
    checks = {}

    # Check 1: Spec trios completeness
    dev_dir = vault / "03-development"
    if dev_dir.exists():
        for spec_dir in dev_dir.iterdir():
            if spec_dir.is_dir() and not spec_dir.name.startswith("_"):
                for required in ("requirements.md", "design.md", "tasks.md"):
                    if not (spec_dir / required).exists():
                        issues.append({"check": "spec_trio", "missing": str(spec_dir / required)})
    checks["spec_trios"] = len([i for i in issues if i.get("check") == "spec_trio"]) == 0

    # Check 2: Frontmatter completeness
    fm_issues = 0
    for md in vault.rglob("*.md"):
        if ".sdlc-kit" in md.parts or "_templates" in md.parts:
            continue
        parsed = parse(md)
        for field in _REQUIRED_FRONTMATTER:
            if field not in parsed["frontmatter"]:
                issues.append({"check": "frontmatter", "file": str(md.relative_to(vault)), "missing_field": field})
                fm_issues += 1
    checks["frontmatter"] = fm_issues == 0

    # Check 3: TASKS.md exists
    checks["tasks_file"] = (vault / "03-development" / "TASKS.md").exists()
    if not checks["tasks_file"]:
        issues.append({"check": "tasks_file", "message": "TASKS.md not found in 03-development/"})

    # Check 4: ADRs not stuck
    adr_dir = vault / "02-architecture" / "ADR"
    stuck_adrs = 0
    if adr_dir.exists():
        today = date.today()
        for adr in adr_dir.glob("ADR-*.md"):
            parsed = parse(adr)
            if parsed["frontmatter"].get("status") == "proposed":
                created_str = parsed["frontmatter"].get("created", "")
                try:
                    created = datetime.strptime(str(created_str), "%Y-%m-%d").date()
                    if (today - created).days > 7:
                        issues.append({"check": "adr_stuck", "file": adr.name, "days": (today - created).days})
                        stuck_adrs += 1
                except ValueError:
                    pass
    checks["adrs_not_stuck"] = stuck_adrs == 0

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    print(json.dumps({
        "status": "ok",
        "passed": passed,
        "total": total,
        "checks": checks,
        "issues": issues
    }))


if __name__ == "__main__":
    main()
