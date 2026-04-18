#!/usr/bin/env python3
"""Vault librarian: scan, validate frontmatter, regenerate MOCs and _INDEX.md.

Single JSON object on stdout. Diagnostics on stderr. Exit codes: 0 ok, 1 user error,
2 fatal.

Pipeline (runs on every invocation):
    1. Delta-scan via core.scanner → SQLite tables (notes, events)
    2. Walk vault, parse each markdown, build in-memory index grouped by phase/type
    3. Validate: required frontmatter (per type), status enums, broken wikilinks,
       orphans, duplicate titles, stale `updated` (>90 days)
    4. Regenerate every `<phase>/_MOC.md` `## Artifacts` section
    5. Regenerate `_INDEX.md` preserving the canonical template structure

Flags:
    --vault-root <path>   (required)  target vault (the `.sdlc/` directory)
    --dry-run             report only, write nothing
    --fix                 reserved for a future revision; currently a no-op that
                          emits a warning on stderr if passed
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------

REQUIRED_FIELDS_BY_TYPE: dict[str, set[str]] = {
    "moc":       {"type", "phase", "title"},
    "index":     {"type", "title"},
    "note":      {"type", "title"},
    "prd":       {"type", "title", "status"},
    "adr":       {"type", "title", "status"},
    "epic":      {"type", "title", "status"},
    "milestone": {"type", "title", "status"},
    "spec-requirements": {"type", "title", "status", "slug"},
    "spec-design":       {"type", "title", "status", "slug"},
    "spec-tasks":        {"type", "title", "status", "slug"},
    "trd":       {"type", "title", "status"},
    "retro":     {"type", "title", "status"},
    "review":    {"type", "title", "status"},
    "incident":  {"type", "title", "severity", "status"},
    "incident-lessons":           {"type", "title", "slug", "status"},
    "steering-product":           {"type", "title", "status"},
    "steering-tech":              {"type", "title", "status"},
    "steering-standards":         {"type", "title", "status"},
    "domain-aggregate":           {"type", "title", "slug", "status"},
    "domain-event":               {"type", "title", "slug", "status"},
    "domain-contract":            {"type", "title", "slug", "status"},
    "domain-context-map":         {"type", "title", "status"},
    "domain-ubiquitous-language": {"type", "title", "status"},
    "c4-context":                 {"type", "title", "status"},
    "c4-container":               {"type", "title", "status"},
    "c4-component":               {"type", "title", "slug", "status"},
    "api-rest":                   {"type", "title", "slug", "status"},
    "api-async":                  {"type", "title", "slug", "status"},
    "api-grpc":                   {"type", "title", "slug", "status"},
    "api-webhook":                {"type", "title", "slug", "status"},
    "design-token":     {"type", "title", "status", "slug"},
    "design-component": {"type", "title", "status", "slug"},
    "design-pattern":   {"type", "title", "status", "slug"},
    "worktree":  {"type", "title", "status"},
    "branch":    {"type", "title", "slug"},
}

VALID_STATUS_BY_TYPE: dict[str, set[str]] = {
    "index":     {"active"},
    "prd":       {"draft", "active", "shipped", "archived"},
    "adr":       {"proposed", "accepted", "rejected", "superseded", "deprecated"},
    "epic":      {"planned", "in-progress", "done", "cancelled"},
    "milestone": {"planned", "on-track", "at-risk", "slipped", "done", "cancelled"},
    "spec-requirements": {"draft", "approved", "implemented", "archived"},
    "spec-design":       {"draft", "approved", "implemented", "archived"},
    "spec-tasks":        {"draft", "approved", "implemented", "archived"},
    "trd":       {"draft", "approved", "deprecated"},
    "retro":     {"draft", "final"},
    "incident":  {"open", "mitigated", "resolved", "post-mortem"},
    "incident-lessons":           {"draft", "approved", "deprecated"},
    "steering-product":           {"draft", "active", "archived"},
    "steering-tech":              {"draft", "active", "archived"},
    "steering-standards":         {"draft", "active", "archived"},
    "worktree":  {"active", "merged", "abandoned"},
    "design-token":     {"draft", "stable", "deprecated"},
    "design-component": {"draft", "stable", "deprecated"},
    "design-pattern":   {"draft", "stable", "deprecated"},
    "domain-aggregate":           {"draft", "approved", "deprecated"},
    "domain-event":               {"draft", "approved", "deprecated"},
    "domain-contract":            {"draft", "approved", "deprecated"},
    "domain-context-map":         {"draft", "approved", "deprecated"},
    "domain-ubiquitous-language": {"draft", "approved", "deprecated"},
    "c4-context":                 {"draft", "approved", "deprecated"},
    "c4-container":               {"draft", "approved", "deprecated"},
    "c4-component":               {"draft", "approved", "deprecated"},
    "api-rest":                   {"draft", "approved", "deprecated"},
    "api-async":                  {"draft", "approved", "deprecated"},
    "api-grpc":                   {"draft", "approved", "deprecated"},
    "api-webhook":                {"draft", "approved", "deprecated"},
}

# Folder prefixes the script recognizes as phases (everything else under vault
# root is flagged as "orphan").
PHASE_PREFIXES = (
    "00-steering", "01-planning", "02-architecture", "03-domain",
    "04-specs", "05-development", "06-design-system", "07-retrospectives",
)

STALE_THRESHOLD_DAYS = 90


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class Note:
    path: Path
    rel: str
    phase: str
    frontmatter: dict[str, Any]
    wikilinks: list[str]
    doc_type: str
    title: str
    status: str


@dataclass
class Anomaly:
    severity: str      # error | warning | info
    type: str
    file: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "type": self.type,
            "file": self.file,
            "detail": self.detail,
        }


@dataclass
class Report:
    status: str = "ok"
    vault_root: str = ""
    scanned: int = 0
    db_changes: dict[str, int] = field(default_factory=dict)
    mocs_regenerated: list[str] = field(default_factory=list)
    index_regenerated: bool = False
    anomalies: list[Anomaly] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        grouped: dict[str, int] = {}
        for a in self.anomalies:
            grouped[a.severity] = grouped.get(a.severity, 0) + 1
        return {
            "status": self.status,
            "vault_root": self.vault_root,
            "scanned": self.scanned,
            "db_changes": self.db_changes,
            "mocs_regenerated": sorted(self.mocs_regenerated),
            "index_regenerated": self.index_regenerated,
            "anomalies": [a.as_dict() for a in self.anomalies],
            "anomaly_counts": grouped,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def die(report: Report, message: str, code: int = 2) -> None:
    report.status = "error"
    report.errors.append(message)
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(code)


def resolve_vault(vault_arg: str, report: Report) -> Path:
    vault = Path(vault_arg).resolve()
    if not vault.exists():
        die(report, f"vault root does not exist: {vault}", code=1)
    if not (vault / ".sdlc-kit").exists():
        die(report, f"not a vault (missing .sdlc-kit marker): {vault}", code=1)
    return vault


def import_core(plugin_root: Path) -> dict[str, Any]:
    """Dynamically import the plugin's core library so this script works
    regardless of how it's invoked."""
    if str(plugin_root) not in sys.path:
        sys.path.insert(0, str(plugin_root))
    from core.db import connect, run_migrations
    from core.parser import parse
    from core.scanner import scan
    return {
        "connect": connect,
        "run_migrations": run_migrations,
        "parse": parse,
        "scan": scan,
    }


def phase_of(rel: str) -> str:
    parts = rel.replace("\\", "/").split("/", 1)
    head = parts[0] if parts else ""
    return head if head in PHASE_PREFIXES else ""


# Files the librarian indexes but excludes from frontmatter/wikilink validation
# (they are sovereign or owned by the sync script itself).
VALIDATION_EXEMPT = {"CLAUDE.md", "_INDEX.md"}


def should_skip(md_file: Path, vault_root: Path) -> bool:
    rel_parts = md_file.relative_to(vault_root).parts
    if ".sdlc-kit" in rel_parts:
        return True
    if "_templates" in rel_parts:
        return True
    return False


def _is_placeholder_link(target: str) -> bool:
    """True for wikilink targets that are template placeholders like `<slug>`."""
    t = target.strip()
    return ("<" in t) or (">" in t) or t.startswith("{{") or t.endswith("}}")


def collect_notes(vault_root: Path, parse_fn) -> list[Note]:
    notes: list[Note] = []
    for md_file in sorted(vault_root.rglob("*.md")):
        if should_skip(md_file, vault_root):
            continue
        rel = str(md_file.relative_to(vault_root)).replace("\\", "/")
        parsed = parse_fn(md_file)
        fm = parsed["frontmatter"] or {}
        notes.append(Note(
            path=md_file,
            rel=rel,
            phase=phase_of(rel),
            frontmatter=fm,
            wikilinks=list(parsed["wikilinks"] or []),
            doc_type=str(fm.get("type", "")),
            title=str(fm.get("title", md_file.stem)),
            status=str(fm.get("status", "")),
        ))
    return notes


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def validate_notes(notes: list[Note]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    title_index: dict[str, list[str]] = {}
    stem_index: set[str] = set()
    for n in notes:
        title_index.setdefault(n.title.strip().lower(), []).append(n.rel)
        stem_index.add(n.path.stem)

    today = _dt.date.today()

    for n in notes:
        if n.rel in VALIDATION_EXEMPT:
            continue

        # 1. Required frontmatter
        required = REQUIRED_FIELDS_BY_TYPE.get(n.doc_type, REQUIRED_FIELDS_BY_TYPE["note"])
        for field_name in required:
            if field_name not in n.frontmatter or n.frontmatter.get(field_name) in (None, ""):
                anomalies.append(Anomaly(
                    severity="error",
                    type="missing_field",
                    file=n.rel,
                    detail=f"missing required frontmatter field `{field_name}` for type `{n.doc_type or 'note'}`",
                ))

        # 2. Status enum
        valid_statuses = VALID_STATUS_BY_TYPE.get(n.doc_type)
        if valid_statuses and n.status and n.status not in valid_statuses:
            anomalies.append(Anomaly(
                severity="warning",
                type="invalid_status",
                file=n.rel,
                detail=f"status `{n.status}` not in allowed set {sorted(valid_statuses)}",
            ))

        # 3. Broken wikilinks (ignore template placeholders)
        for target in n.wikilinks:
            if _is_placeholder_link(target):
                continue
            if target.strip() not in stem_index:
                anomalies.append(Anomaly(
                    severity="warning",
                    type="broken_wikilink",
                    file=n.rel,
                    detail=f"wikilink target `[[{target}]]` not found in vault",
                ))

        # 4. Orphan (outside any phase and not a root-level canonical doc)
        root_level_allowed = {"CLAUDE.md", "_INDEX.md", "dashboard.html"}
        if n.phase == "" and n.rel not in root_level_allowed:
            anomalies.append(Anomaly(
                severity="warning",
                type="orphan",
                file=n.rel,
                detail="file lives outside any recognized phase folder",
            ))

        # 5. Stale `updated`
        updated_val = n.frontmatter.get("updated")
        if isinstance(updated_val, (_dt.date, _dt.datetime)):
            age = (today - (updated_val if isinstance(updated_val, _dt.date) else updated_val.date())).days
            if age > STALE_THRESHOLD_DAYS:
                anomalies.append(Anomaly(
                    severity="info",
                    type="stale_update",
                    file=n.rel,
                    detail=f"`updated` field is {age} days old (threshold {STALE_THRESHOLD_DAYS})",
                ))

    # 6. Duplicate titles (across the whole vault)
    for title_key, paths in title_index.items():
        if len(paths) > 1 and title_key:
            for p in paths:
                anomalies.append(Anomaly(
                    severity="info",
                    type="duplicate_title",
                    file=p,
                    detail=f"title `{title_key}` shared with: {[q for q in paths if q != p]}",
                ))

    return anomalies


# ---------------------------------------------------------------------------
# MOC regeneration
# ---------------------------------------------------------------------------

MOC_ANCHOR = "## Artifacts"


def render_moc_artifacts(notes_in_phase: list[Note]) -> list[str]:
    """Build the `## Artifacts` section body (table or empty-state).

    Returns a list of lines (no trailing blank)."""
    items = [n for n in notes_in_phase if n.path.stem not in ("_MOC", "_INDEX")]
    lines: list[str] = [MOC_ANCHOR, ""]
    if not items:
        lines.append("_No artifacts yet._")
        return lines

    lines.append("| Document | Type | Status | Updated |")
    lines.append("|----------|------|--------|---------|")
    for n in sorted(items, key=lambda x: (x.doc_type, x.title)):
        updated = n.frontmatter.get("updated", "—")
        if isinstance(updated, (_dt.date, _dt.datetime)):
            updated = updated.isoformat()
        lines.append(
            f"| [[{n.path.stem}]] | {n.doc_type or '—'} | {n.status or '—'} | {updated} |"
        )
    return lines


def regenerate_mocs(
    vault_root: Path,
    notes_by_phase: dict[str, list[Note]],
    *,
    dry_run: bool,
    report: Report,
) -> None:
    for phase in PHASE_PREFIXES:
        moc_path = vault_root / phase / "_MOC.md"
        if not moc_path.exists():
            continue
        content = moc_path.read_text(encoding="utf-8")
        # Replace `## Artifacts` block (up to next `## ` or EOF)
        lines = content.split("\n")
        out: list[str] = []
        i = 0
        replaced = False
        artifacts_lines = render_moc_artifacts(notes_by_phase.get(phase, []))
        while i < len(lines):
            line = lines[i]
            if line.strip() == MOC_ANCHOR and not replaced:
                out.extend(artifacts_lines)
                out.append("")  # blank line before next section
                i += 1
                while i < len(lines) and not lines[i].startswith("## "):
                    i += 1
                replaced = True
                continue
            out.append(line)
            i += 1

        new_content = "\n".join(out)
        if new_content == content:
            continue
        if dry_run:
            report.mocs_regenerated.append(f"{phase}/_MOC.md")
            continue
        moc_path.write_text(new_content, encoding="utf-8")
        report.mocs_regenerated.append(f"{phase}/_MOC.md")


# ---------------------------------------------------------------------------
# _INDEX.md regeneration (preserves the canonical scaffolded structure)
# ---------------------------------------------------------------------------

def _status_mark(status: str) -> str:
    if status in {"done", "shipped", "accepted", "final", "approved", "implemented", "resolved"}:
        return "[x]"
    return "[ ]"


def _note_by_stem(notes: list[Note], stem: str, phase: str) -> Note | None:
    for n in notes:
        if n.phase == phase and n.path.stem == stem:
            return n
    return None


def render_index(
    project_name: str,
    sync_ts: str,
    notes: list[Note],
    anomalies: list[Anomaly],
) -> str:
    notes_by_phase: dict[str, list[Note]] = {p: [] for p in PHASE_PREFIXES}
    for n in notes:
        if n.phase in notes_by_phase:
            notes_by_phase[n.phase].append(n)

    by_type: dict[str, list[Note]] = {}
    for n in notes:
        by_type.setdefault(n.doc_type, []).append(n)

    total_notes = len(notes)
    open_tasks = sum(1 for n in by_type.get("task", []) if n.status in {"open", "in-progress", "blocked"})
    done_tasks = sum(1 for n in by_type.get("task", []) if n.status == "done")
    open_incidents = sum(1 for n in by_type.get("incident", []) if n.status in {"open", "mitigated"})
    adrs = by_type.get("adr", [])
    active_specs = len({
        n.frontmatter.get("slug") or n.path.parent.name
        for n in notes
        if n.doc_type in {"spec", "spec-requirements", "spec-design", "spec-tasks"}
        and n.status in {"draft", "approved"}
    })
    active_epics = sum(1 for n in by_type.get("epic", []) if n.status in {"planned", "in-progress"})

    out: list[str] = []
    out.append("---")
    out.append("type: index")
    out.append(f'title: "Índice — {project_name}"')
    out.append("status: active")
    out.append("generated_by: sdlc-sync")
    out.append(f"updated: {sync_ts}")
    out.append("---")
    out.append("")
    out.append(f"# Índice — {project_name}")
    out.append("")
    out.append("> Gerado automaticamente por `/sdlc-kit:sync`. **Não editar manualmente.**")
    out.append(f"> Última sincronização: **{sync_ts}**")
    out.append("")
    out.append("---")
    out.append("")

    # --- Panorama
    out.append("## Panorama")
    out.append("")
    out.append("| Métrica | Valor |")
    out.append("|---|---|")
    out.append(f"| Total de documentos | {total_notes} |")
    out.append(f"| Epics ativos | {active_epics} |")
    out.append(f"| Specs em andamento | {active_specs} |")
    out.append(f"| Tasks abertas | {open_tasks} |")
    out.append(f"| Tasks concluídas | {done_tasks} |")
    out.append(f"| Incidents abertos | {open_incidents} |")
    out.append(f"| ADRs registrados | {len(adrs)} |")
    out.append("")
    out.append("---")
    out.append("")

    # --- 00 Steering
    out.append("## Direção (00-steering)")
    out.append("")
    for stem, label in (("product", "Visão de produto"),
                        ("tech", "Princípios técnicos"),
                        ("standards", "Padrões do time")):
        n = _note_by_stem(notes, stem, "00-steering")
        if n:
            out.append(f"- [x] [[{stem}]] — {label} — _{n.status or 'registrado'}_")
        else:
            out.append(f"- [ ] `{stem}.md` — {label} — _pendente_")
    out.append("")

    # --- 01 Planning
    out.append("## Planejamento (01-planning)")
    out.append("")
    out.append("### PRDs")
    prds = [n for n in notes_by_phase["01-planning"] if n.doc_type == "prd"]
    if prds:
        for n in sorted(prds, key=lambda x: x.title):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append('_Nenhum PRD registrado. Rode `/sdlc-kit:prd new "<iniciativa>"`._')
    out.append("")
    out.append("### Epics")
    epics = [n for n in notes_by_phase["01-planning"] if n.doc_type == "epic"]
    if epics:
        for n in sorted(epics, key=lambda x: x.title):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append("_Nenhum epic registrado._")
    out.append("")
    out.append("### Milestones")
    milestones = [n for n in notes_by_phase["01-planning"] if n.doc_type == "milestone"]
    if milestones:
        for n in sorted(milestones, key=lambda x: x.title):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append("_Nenhum milestone registrado._")
    out.append("")

    # --- 02 Architecture
    out.append("## Arquitetura (02-architecture)")
    out.append("")
    out.append("### ADRs")
    if adrs:
        for n in sorted(adrs, key=lambda x: x.path.stem):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append('_Nenhum ADR registrado. Rode `/sdlc-kit:adr new "<título>"` para a primeira decisão._')
    out.append("")
    out.append("### C4")
    for stem, level in (("context", "Nível 1 (Contexto)"),
                        ("container", "Nível 2 (Containers)"),
                        ("component", "Nível 3 (Componentes)")):
        n = _note_by_stem(notes, stem, "02-architecture")
        if n:
            out.append(f"- [x] [[{stem}]] — {level}")
        else:
            out.append(f"- [ ] `{stem}.md` — {level} — _pendente_")
    out.append("")
    out.append("### TRDs")
    trds = [n for n in notes_by_phase["02-architecture"] if n.doc_type == "trd"]
    if trds:
        for n in sorted(trds, key=lambda x: x.title):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append("_Nenhum TRD registrado._")
    out.append("")
    out.append("### APIs")
    apis = [n for n in notes_by_phase["02-architecture"] if n.doc_type.startswith("api-")]
    if apis:
        for n in sorted(apis, key=lambda x: (x.doc_type, x.title)):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append("_Nenhum contrato de API registrado. Rode `/sdlc-kit:spec api {rest|grpc|async|webhook} <feature>`._")
    out.append("")

    # --- 03 Domain
    out.append("## Domínio (03-domain)")
    out.append("")
    for stem, label in (("context-map", "Mapa de bounded contexts"),
                        ("ubiquitous-language", "Glossário")):
        n = _note_by_stem(notes, stem, "03-domain")
        if n:
            out.append(f"- [x] [[{stem}]] — {label}")
        else:
            out.append(f"- [ ] `{stem}.md` — {label} — _pendente_")
    out.append("")
    domain_artifacts = [n for n in notes_by_phase["03-domain"]
                        if n.doc_type in {"domain-aggregate", "domain-event", "domain-contract"}]
    if domain_artifacts:
        for n in sorted(domain_artifacts, key=lambda x: (x.doc_type, x.title)):
            out.append(f"- [[{n.path.stem}]] — {n.title} _({n.doc_type})_")
    else:
        out.append("_Nenhum aggregate, evento ou contrato registrado._")
    out.append("")

    # --- 04 Specs
    out.append("## Specs (04-specs)")
    out.append("")
    spec_types = {"spec", "spec-requirements", "spec-design", "spec-tasks"}
    spec_docs = [n for n in notes_by_phase["04-specs"] if n.doc_type in spec_types]
    if spec_docs:
        by_feature: dict[str, list[Note]] = {}
        for n in spec_docs:
            slug = str(n.frontmatter.get("slug") or n.path.parent.name)
            by_feature.setdefault(slug, []).append(n)
        for slug in sorted(by_feature):
            docs = sorted(by_feature[slug], key=lambda x: x.doc_type)
            out.append(f"- **{slug}**")
            for n in docs:
                kind = n.doc_type.replace("spec-", "") if n.doc_type != "spec" else "spec"
                out.append(f"  - {_status_mark(n.status)} [[{n.path.stem}]] — _{kind}_ — _{n.status or '—'}_")
    else:
        out.append('_Nenhuma spec criada. Rode `/sdlc-kit:spec new <feature>` para o trio SDD (requirements + design + tasks)._')
    out.append("")

    # --- 05 Development
    out.append("## Desenvolvimento (05-development)")
    out.append("")
    out.append("### Worktrees")
    worktrees = [n for n in notes_by_phase["05-development"] if n.doc_type == "worktree"]
    if worktrees:
        for n in sorted(worktrees, key=lambda x: x.title):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append("_Nenhum worktree ativo._")
    out.append("")
    out.append("### Branches rastreadas")
    branches = [n for n in notes_by_phase["05-development"] if n.doc_type == "branch"]
    if branches:
        for n in sorted(branches, key=lambda x: x.title):
            out.append(f"- [[{n.path.stem}]] — {n.title}")
    else:
        out.append("_Nenhuma branch registrada._")
    out.append("")

    # --- 06 Design System
    out.append("## Design System (06-design-system)")
    out.append("")
    ds_items = [n for n in notes_by_phase["06-design-system"]
                if n.doc_type in {"design-token", "design-component", "design-pattern"}]
    if ds_items:
        for n in sorted(ds_items, key=lambda x: (x.doc_type, x.title)):
            out.append(f"- [[{n.path.stem}]] — {n.title} _({n.doc_type})_")
    else:
        out.append("_Vazio. Rode `/sdlc-kit:design-system {token|component|pattern} <nome>` quando começar a documentar o DS._")
    out.append("")

    # --- 07 Retrospectives
    out.append("## Retrospectivas (07-retrospectives)")
    out.append("")
    out.append("### Retros")
    retros = [n for n in notes_by_phase["07-retrospectives"] if n.doc_type == "retro"]
    if retros:
        for n in sorted(retros, key=lambda x: x.path.stem, reverse=True):
            out.append(f"- [[{n.path.stem}]] — {n.title}")
    else:
        out.append("_Nenhuma retro registrada. Rode `/sdlc-kit:retro` para criar a primeira retrospectiva._")
    out.append("")
    out.append("### Code Reviews")
    reviews = [n for n in notes_by_phase["07-retrospectives"] if n.doc_type == "review"]
    if reviews:
        for n in sorted(reviews, key=lambda x: x.path.stem, reverse=True):
            out.append(f"- [[{n.path.stem}]] — {n.title}")
    else:
        out.append("_Nenhum review registrado._")
    out.append("")
    out.append("### Incidents")
    incidents = [n for n in notes_by_phase["07-retrospectives"] if n.doc_type == "incident"]
    if incidents:
        for n in sorted(incidents, key=lambda x: x.path.stem, reverse=True):
            out.append(f"- {_status_mark(n.status)} [[{n.path.stem}]] — {n.title} — _{n.status or '—'}_")
    else:
        out.append("_Nenhum incident registrado._")
    out.append("")

    # --- Anomalies
    out.append("---")
    out.append("")
    out.append("## Anomalias detectadas")
    out.append("")
    if not anomalies:
        out.append("_Nenhuma anomalia._")
    else:
        counts: dict[str, int] = {}
        for a in anomalies:
            counts[a.severity] = counts.get(a.severity, 0) + 1
        summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
        out.append(f"_Total: {len(anomalies)} ({summary}). Detalhe via `/sdlc-kit:status` ou `sdlc-kit sync --json`._")
        out.append("")
        # Top 10
        for a in anomalies[:10]:
            out.append(f"- **{a.severity.upper()}** `{a.type}` · `{a.file}` — {a.detail}")
        if len(anomalies) > 10:
            out.append(f"- _… +{len(anomalies) - 10} more_")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Atalhos úteis")
    out.append("")
    out.append("- [[CLAUDE]] — doutrina do vault (leitura obrigatória)")
    out.append("- `dashboard.html` — painel autocontido (`/sdlc-kit:dash` para abrir)")
    out.append("- `/sdlc-kit:status` — relatório de saúde via CLI")
    out.append("")
    return "\n".join(out)


def _strip_sync_timestamp(text: str) -> str:
    """Remove lines that carry the sync timestamp so we can compare
    content-for-content across runs."""
    out: list[str] = []
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("updated:"):
            continue
        if stripped.startswith("> Última sincronização"):
            continue
        out.append(line)
    return "\n".join(out)


def regenerate_index(
    vault_root: Path,
    notes: list[Note],
    anomalies: list[Anomaly],
    *,
    dry_run: bool,
    report: Report,
) -> None:
    marker_path = vault_root / ".sdlc-kit" / "marker.json"
    project_name = "Projeto"
    if marker_path.exists():
        try:
            project_name = json.loads(marker_path.read_text(encoding="utf-8")).get("project_name") or project_name
        except Exception:
            pass

    sync_ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = render_index(project_name, sync_ts, notes, anomalies)
    index_path = vault_root / "_INDEX.md"

    # Idempotency: only rewrite if the non-timestamp content changed.
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        if _strip_sync_timestamp(existing) == _strip_sync_timestamp(content):
            report.index_regenerated = False
            return

    report.index_regenerated = True
    if dry_run:
        return
    index_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit vault librarian.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    p.add_argument("--fix", action="store_true", help="reserved for future — currently no-op; prints a warning if used")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()

    if args.fix:
        print(
            "warning: --fix is reserved for a future revision and has no effect today; "
            "sync ran as read-only (use --dry-run to preview, omit both flags to write).",
            file=sys.stderr,
        )

    vault_root = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault_root)

    plugin_root = Path(__file__).resolve().parent.parent.parent.parent
    try:
        core = import_core(plugin_root)
    except Exception as exc:
        die(report, f"failed to import core library: {exc}", code=2)

    # --- 1. DB scan
    db_path = vault_root / ".sdlc-kit" / "db.sqlite"
    db_path.parent.mkdir(exist_ok=True)
    try:
        conn: sqlite3.Connection = core["connect"](db_path)
        core["run_migrations"](conn)
        report.db_changes = core["scan"](vault_root, conn)
    except Exception as exc:
        die(report, f"database scan failed: {exc}", code=2)

    # --- 2. Collect + index notes
    notes = collect_notes(vault_root, core["parse"])
    report.scanned = len(notes)
    notes_by_phase: dict[str, list[Note]] = {p: [] for p in PHASE_PREFIXES}
    for n in notes:
        if n.phase in notes_by_phase:
            notes_by_phase[n.phase].append(n)

    # --- 3. Validate
    report.anomalies = validate_notes(notes)

    # --- 4. Regenerate MOCs
    try:
        regenerate_mocs(vault_root, notes_by_phase, dry_run=args.dry_run, report=report)
    except Exception as exc:
        die(report, f"MOC regeneration failed: {exc}", code=2)

    # --- 5. Regenerate _INDEX.md
    try:
        regenerate_index(vault_root, notes, report.anomalies, dry_run=args.dry_run, report=report)
    except Exception as exc:
        die(report, f"INDEX regeneration failed: {exc}", code=2)

    report.status = "dry-run" if args.dry_run else "ok"
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
