#!/usr/bin/env python3
"""Vault librarian: scan, validate frontmatter, update MOCs and INDEX."""
import argparse
import json
import sys
from pathlib import Path

_REQUIRED_FRONTMATTER = {"title", "type", "status", "phase"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    vault = _find_vault(args.vault_root)
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.db import connect, run_migrations
    from core.scanner import scan
    from core.parser import parse

    db_path = vault / ".sdlc-kit" / "db.sqlite"
    db_path.parent.mkdir(exist_ok=True)
    conn = connect(db_path)
    run_migrations(conn)

    scan_result = scan(vault, conn)

    anomalies = []
    scanned = 0

    for md_file in vault.rglob("*.md"):
        if ".sdlc-kit" in md_file.parts:
            continue
        if "_templates" in md_file.parts:
            continue
        scanned += 1
        parsed = parse(md_file)
        fm = parsed["frontmatter"]

        # Check required fields
        for field in _REQUIRED_FRONTMATTER:
            if field not in fm:
                anomalies.append({
                    "type": "missing_frontmatter_field",
                    "file": str(md_file.relative_to(vault)),
                    "field": field
                })

        # Check wikilinks (except _MOC.md and _INDEX.md)
        if md_file.stem not in ("_MOC", "_INDEX") and not parsed["wikilinks"]:
            anomalies.append({
                "type": "no_wikilinks",
                "file": str(md_file.relative_to(vault))
            })

    if not args.dry_run:
        _update_mocs(vault)
        _update_index(vault, conn)

    updated_mocs = [d.name for d in vault.iterdir()
                    if d.is_dir() and d.name[0].isdigit()]

    print(json.dumps({
        "status": "dry-run" if args.dry_run else "ok",
        "scanned": scanned,
        "db_changes": scan_result,
        "updated_mocs": updated_mocs,
        "anomalies": anomalies
    }))


def _find_vault(vault_root_arg: str | None) -> Path | None:
    if vault_root_arg:
        return Path(vault_root_arg)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root
    return find_vault_root()


def _update_mocs(vault: Path) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.parser import parse
    for phase_dir in sorted(vault.iterdir()):
        if not phase_dir.is_dir() or not phase_dir.name[0].isdigit():
            continue
        docs = []
        for md in sorted(phase_dir.rglob("*.md")):
            if "_templates" in md.parts or md.stem in ("_MOC", "_INDEX"):
                continue
            parsed = parse(md)
            title = parsed["frontmatter"].get("title", md.stem)
            status = parsed["frontmatter"].get("status", "")
            docs.append(f"| [[{md.stem}]] | {status} |")
        moc_path = phase_dir / "_MOC.md"
        if moc_path.exists():
            content = moc_path.read_text(encoding="utf-8")
            # Find and replace the ## Documentos section
            table = "## Documentos\n\n| Documento | Status |\n|-----------|--------|\n"
            table += "\n".join(docs) if docs else "| _Nenhum documento_ | — |"
            lines = content.split("\n")
            new_lines = []
            in_docs = False
            for line in lines:
                if line.startswith("## Documentos"):
                    in_docs = True
                    new_lines.append(table)
                elif in_docs and line.startswith("## "):
                    in_docs = False
                    new_lines.append(line)
                elif not in_docs:
                    new_lines.append(line)
            moc_path.write_text("\n".join(new_lines), encoding="utf-8")


def _update_index(vault: Path, conn) -> None:
    index_path = vault / "_INDEX.md"
    notes = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    open_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0]
    done_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    sections = []
    for phase_dir in sorted(vault.iterdir()):
        if not phase_dir.is_dir() or not phase_dir.name[0].isdigit():
            continue
        docs = [f for f in phase_dir.rglob("*.md")
                if "_templates" not in f.parts and f.stem not in ("_MOC",)]
        sections.append(f"### {phase_dir.name} ({len(docs)} docs)")
        if docs:
            sections.append("| Documento | Status |")
            sections.append("|-----------|--------|")
            from core.parser import parse as _parse
            for doc in sorted(docs):
                fm = _parse(doc)["frontmatter"]
                sections.append(f"| [[{doc.stem}]] | {fm.get('status', '—')} |")

    content = f"""# Index — Vault | Sync: {now}

> Gerado automaticamente por `/sdlc-kit:sync`. Não editar manualmente.

## Visão Geral

- Tasks abertas: {open_tasks} | Concluídas: {done_tasks}
- Total de documentos: {notes}

## Documentos por Fase

{chr(10).join(sections)}

## Anomalias Detectadas

_Execute `/sdlc-kit:sync` para verificar anomalias._
"""
    index_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
