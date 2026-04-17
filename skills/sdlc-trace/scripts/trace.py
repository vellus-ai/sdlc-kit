#!/usr/bin/env python3
"""Generate a traceability matrix linking requirements to design to tasks."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path


def _extract_requirements(text: str) -> list[str]:
    """Extract lines matching EARS notation keywords WHEN or SHALL."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and ("WHEN" in stripped or "SHALL" in stripped):
            lines.append(stripped)
    return lines


def _extract_tasks(text: str) -> list[str]:
    """Extract task lines starting with '- ['."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ["):
            # Strip markdown checkbox prefix: "- [ ] " or "- [x] "
            task_text = stripped
            if len(stripped) > 6:
                task_text = stripped[6:].strip() if stripped[3] in (" ", "x", "X") else stripped
            lines.append(task_text)
    return lines


def _build_table(requirements: list[str], tasks: list[str]) -> str:
    """Build a Markdown traceability matrix table."""
    rows = ["| Requirement | Design Ref | Task | Status |", "|-------------|-----------|------|--------|"]
    max_rows = max(len(requirements), len(tasks), 1)
    for i in range(max_rows):
        req = requirements[i] if i < len(requirements) else ""
        task = tasks[i] if i < len(tasks) else ""
        # Escape pipe characters in cells
        req = req.replace("|", "\\|")
        task = task.replace("|", "\\|")
        rows.append(f"| {req} | design.md | {task} | open |")
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate traceability matrix for a spec")
    parser.add_argument("--spec-slug", required=True)
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
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

    spec_dir = vault / "03-development" / args.spec_slug
    if not spec_dir.exists():
        print(json.dumps({"status": "error", "message": f"spec directory not found: {spec_dir}"}))
        sys.exit(1)

    req_path = spec_dir / "requirements.md"
    if not req_path.exists():
        print(json.dumps({"status": "error", "message": f"requirements.md not found in {spec_dir}"}))
        sys.exit(1)

    requirements = _extract_requirements(req_path.read_text(encoding="utf-8"))

    tasks_path = spec_dir / "tasks.md"
    tasks = []
    if tasks_path.exists():
        tasks = _extract_tasks(tasks_path.read_text(encoding="utf-8"))

    today = date.today().isoformat()
    table = _build_table(requirements, tasks)
    trace_path = spec_dir / "traceability.md"

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "spec_slug": args.spec_slug,
            "requirements_found": len(requirements),
            "tasks_found": len(tasks),
            "file": str(trace_path),
        }))
        return

    content = f"""---
title: "Traceability Matrix: {args.spec_slug}"
type: traceability
status: draft
phase: "03"
created: {today}
updated: {today}
---

# Traceability Matrix: {args.spec_slug}

> Gerado automaticamente. Verifique e ajuste referências manualmente.

{table}

## Legenda

- **Requirement**: Requisito extraído de `requirements.md` (EARS notation)
- **Design Ref**: Documento de design associado
- **Task**: Tarefa de implementação de `tasks.md`
- **Status**: `open` | `in-progress` | `done`
"""

    trace_path.write_text(content, encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "spec_slug": args.spec_slug,
        "requirements_found": len(requirements),
        "tasks_found": len(tasks),
        "file": str(trace_path),
    }))


if __name__ == "__main__":
    main()
