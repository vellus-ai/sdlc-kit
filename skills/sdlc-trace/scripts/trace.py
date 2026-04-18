#!/usr/bin/env python3
"""Report requirement-to-artifact traceability across the SDLC vault.

Read-only. Walks every markdown under the vault root (excluding `.sdlc-kit/`,
`_templates/`, and hidden folders), parses frontmatter and wikilinks, and
builds a matrix between planning/requirement artifacts (PRDs, specs) and
implementation artifacts (tasks, reviews, ADRs, TRDs).

The canonical chain:

    PRD (01-planning)
     └─ spec-requirements (04-specs/<slug>/)
         └─ spec-design (04-specs/<slug>/)
             └─ spec-tasks (04-specs/<slug>/)
                 └─ task records (04-specs/<slug>/)
                     └─ worktree/branch (05-development)
                         └─ review (07-retrospectives/reviews)
    ADR (02-architecture/ADR) ── supports design decisions
    TRD (02-architecture/trd) ── constrains designs

Single action: `report [--format json|markdown] [--slug S]`.

Emits a single JSON object on stdout. When `--format markdown`, the same
JSON is produced, but a `markdown` field carries the human-readable matrix
and the structured per-feature rows are dropped in favour of it. The
markdown is rendered from the JSON report — there is no parallel code path.

Exit codes: 0 ok, 1 user error (invalid args, not a vault), 2 fatal IO.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.regexes import FRONTMATTER_RE, WIKILINK_RE  # noqa: E402


MARKER_REL = ".sdlc-kit/marker.json"

# Phases we walk. Everything under the vault root that isn't one of these (or
# one of the root-level allow-listed files) is still scanned, but we don't
# special-case it.
PHASE_PREFIXES = (
    "00-steering", "01-planning", "02-architecture", "03-domain",
    "04-specs", "05-development", "06-design-system", "07-retrospectives",
)

SPEC_TYPES = {"spec", "spec-requirements", "spec-design", "spec-tasks"}

# ---------------------------------------------------------------------------
# regexes (mirrored from sync.py, on purpose — this script must stand alone)
# ---------------------------------------------------------------------------


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
    slug: str
    stem: str


@dataclass
class FeatureRow:
    slug: str
    prd_refs: list[str] = field(default_factory=list)
    requirements: dict[str, Any] = field(default_factory=lambda: {"exists": False, "path": ""})
    design: dict[str, Any] = field(default_factory=lambda: {"exists": False, "path": ""})
    tasks: dict[str, Any] = field(default_factory=lambda: {"exists": False, "path": "", "task_count": 0})
    reviews: list[str] = field(default_factory=list)
    coverage_status: str = "missing"

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "prd_refs": self.prd_refs,
            "requirements": self.requirements,
            "design": self.design,
            "tasks": self.tasks,
            "reviews": self.reviews,
            "coverage_status": self.coverage_status,
        }


@dataclass
class Report:
    status: str = "ok"
    action: str = "report"
    vault_root: str = ""
    format: str = "json"
    features: list[FeatureRow] = field(default_factory=list)
    orphan_adrs: list[str] = field(default_factory=list)
    orphan_trds: list[str] = field(default_factory=list)
    dangling_designs: list[str] = field(default_factory=list)
    unimplemented_prds: list[str] = field(default_factory=list)
    markdown: str = ""
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "status": self.status,
            "action": self.action,
            "vault_root": self.vault_root,
            "format": self.format,
        }
        if self.format == "markdown":
            d["markdown"] = self.markdown
        else:
            d["features"] = [f.as_dict() for f in self.features]
            d["orphan_adrs"] = self.orphan_adrs
            d["orphan_trds"] = self.orphan_trds
            d["dangling_designs"] = self.dangling_designs
            d["unimplemented_prds"] = self.unimplemented_prds
        d["errors"] = self.errors
        return d


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def die(report: Report, message: str, code: int = 2) -> None:
    report.status = "error"
    report.errors.append(message)
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(code)


def resolve_vault(arg: str, report: Report) -> Path:
    vault = Path(arg).resolve()
    if not vault.exists():
        die(report, f"vault root does not exist: {vault}", code=1)
    if not (vault / ".sdlc-kit").exists():
        die(report, f"not a vault (missing .sdlc-kit marker): {vault}", code=1)
    return vault


def phase_of(rel: str) -> str:
    parts = rel.replace("\\", "/").split("/", 1)
    head = parts[0] if parts else ""
    return head if head in PHASE_PREFIXES else ""


def should_skip(md_file: Path, vault_root: Path) -> bool:
    rel_parts = md_file.relative_to(vault_root).parts
    if ".sdlc-kit" in rel_parts:
        return True
    if "_templates" in rel_parts:
        return True
    for part in rel_parts[:-1]:  # exclude the file name itself
        if part.startswith(".") and part not in (".",):
            return True
    return False


def parse_frontmatter(text: str) -> dict[str, Any]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm: dict[str, Any] = {}
    for line in m.group(1).split("\n"):
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        if value.startswith("'") and value.endswith("'") and len(value) >= 2:
            value = value[1:-1]
        fm[key] = value
    return fm


def extract_wikilinks(text: str) -> list[str]:
    """Return the stem/title targets of every wikilink in the text (no alias,
    no anchor)."""
    out: list[str] = []
    for m in WIKILINK_RE.finditer(text):
        target = m.group(1).strip()
        if target:
            out.append(target)
    return out


def collect_notes(vault_root: Path) -> list[Note]:
    notes: list[Note] = []
    for md_file in sorted(vault_root.rglob("*.md")):
        if should_skip(md_file, vault_root):
            continue
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(md_file.relative_to(vault_root)).replace("\\", "/")
        fm = parse_frontmatter(text)
        wl = extract_wikilinks(text)
        notes.append(Note(
            path=md_file,
            rel=rel,
            phase=phase_of(rel),
            frontmatter=fm,
            wikilinks=wl,
            doc_type=str(fm.get("type", "")),
            title=str(fm.get("title", md_file.stem)),
            slug=str(fm.get("slug", "")),
            stem=md_file.stem,
        ))
    return notes


# ---------------------------------------------------------------------------
# task-record extraction
# ---------------------------------------------------------------------------

_TASK_CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s+.+$")


def count_task_records(tasks_note: Note, notes: list[Note]) -> int:
    """Two sources of 'individual task records':

       1. Every note with `type: task` whose `slug` matches the feature slug.
       2. Checkbox lines `- [ ]` / `- [x]` inside the tasks note body.

    We prefer #1 when any task notes exist; otherwise fall back to #2. This
    lets a team that stores tasks either as separate `task` notes (per the
    chain the brief describes) or as a checklist inside `<slug>-tasks.md`
    both produce a correct count.
    """
    slug = tasks_note.slug or ""
    task_notes = [
        n for n in notes
        if n.doc_type == "task" and (n.slug == slug or (slug and n.stem.startswith(slug)))
    ]
    if task_notes:
        return len(task_notes)

    try:
        text = tasks_note.path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    return sum(1 for line in body.splitlines() if _TASK_CHECKBOX_RE.match(line))


# ---------------------------------------------------------------------------
# index builders
# ---------------------------------------------------------------------------

def build_incoming_index(notes: list[Note]) -> dict[str, list[str]]:
    """Map wikilink target stem → list of source note stems that reference it."""
    incoming: dict[str, list[str]] = {}
    for n in notes:
        for target in n.wikilinks:
            incoming.setdefault(target, []).append(n.stem)
    return incoming


def discover_feature_slugs(notes: list[Note], vault_root: Path) -> list[str]:
    """Feature slugs come from two signals:

       a. `slug:` frontmatter on any `spec*` typed note.
       b. Subfolder names directly under `04-specs/` (so a feature whose specs
          are partially missing still gets a row in the matrix).
    """
    slugs: set[str] = set()

    for n in notes:
        if n.doc_type in SPEC_TYPES and n.slug:
            slugs.add(n.slug)

    specs_dir = vault_root / "04-specs"
    if specs_dir.exists():
        for child in specs_dir.iterdir():
            if not child.is_dir():
                continue
            if child.name.startswith("_") or child.name.startswith("."):
                continue
            slugs.add(child.name)

    return sorted(slugs)


# ---------------------------------------------------------------------------
# feature row construction
# ---------------------------------------------------------------------------

def _feature_note(
    notes: list[Note],
    slug: str,
    doc_type: str,
) -> Note | None:
    """Find the spec-requirements / spec-design / spec-tasks note for a slug.

    Strategy:
      1. Prefer a note whose frontmatter `slug:` matches AND `type:` matches.
      2. Fall back to filename convention `<slug>-{requirements|design|tasks}.md`
         under `04-specs/`.
    """
    for n in notes:
        if n.doc_type == doc_type and n.slug == slug:
            return n

    # filename fallback
    suffix_by_type = {
        "spec-requirements": "-requirements",
        "spec-design": "-design",
        "spec-tasks": "-tasks",
    }
    suffix = suffix_by_type.get(doc_type)
    if not suffix:
        return None
    target_stem = f"{slug}{suffix}"
    for n in notes:
        if n.phase != "04-specs":
            continue
        if n.stem == target_stem:
            return n
    return None


def _prd_refs_for_slug(
    slug: str,
    notes: list[Note],
) -> list[str]:
    """A PRD is considered to reference a feature when it wikilinks any of the
    spec-* notes for that feature (by slug or by filename convention)."""
    candidate_stems = {
        f"{slug}-requirements", f"{slug}-design", f"{slug}-tasks", slug,
    }
    refs: set[str] = set()
    for n in notes:
        if n.doc_type != "prd":
            continue
        for target in n.wikilinks:
            if target in candidate_stems or target == slug:
                refs.add(n.stem)
                break
            # also match by slug frontmatter on the target
            for m in notes:
                if m.slug == slug and m.stem == target:
                    refs.add(n.stem)
                    break
    return sorted(refs)


def _reviews_for_slug(slug: str, notes: list[Note]) -> list[str]:
    """A review wikilinks any spec-* note of the feature."""
    candidate_stems = {
        f"{slug}-requirements", f"{slug}-design", f"{slug}-tasks", slug,
    }
    # Also include all notes whose `slug:` matches — reviews may link to those.
    for n in notes:
        if n.slug == slug:
            candidate_stems.add(n.stem)

    out: set[str] = set()
    for n in notes:
        if n.doc_type != "review":
            continue
        for target in n.wikilinks:
            if target in candidate_stems:
                out.add(n.stem)
                break
    return sorted(out)


def _coverage_status(row: FeatureRow) -> str:
    has_req = row.requirements["exists"]
    has_design = row.design["exists"]
    has_tasks = row.tasks["exists"]
    has_prd = bool(row.prd_refs)

    if has_prd and has_req and has_design and has_tasks:
        return "complete"
    if has_req or has_design or has_tasks:
        return "partial"
    return "missing"


def build_feature_row(
    slug: str,
    notes: list[Note],
    vault_root: Path,
) -> FeatureRow:
    row = FeatureRow(slug=slug)

    req = _feature_note(notes, slug, "spec-requirements")
    if req:
        row.requirements = {"exists": True, "path": req.rel}

    design = _feature_note(notes, slug, "spec-design")
    if design:
        row.design = {"exists": True, "path": design.rel}

    tasks = _feature_note(notes, slug, "spec-tasks")
    if tasks:
        count = count_task_records(tasks, notes)
        row.tasks = {"exists": True, "path": tasks.rel, "task_count": count}

    row.prd_refs = _prd_refs_for_slug(slug, notes)
    row.reviews = _reviews_for_slug(slug, notes)
    row.coverage_status = _coverage_status(row)
    return row


# ---------------------------------------------------------------------------
# gap detection
# ---------------------------------------------------------------------------

def find_orphan_by_type(
    notes: list[Note],
    doc_type: str,
    incoming: dict[str, list[str]],
) -> list[str]:
    """Notes of the given type that no other note wikilinks to."""
    out: list[str] = []
    for n in notes:
        if n.doc_type != doc_type:
            continue
        refs = incoming.get(n.stem, [])
        # Self-references don't count.
        external = [r for r in refs if r != n.stem]
        if not external:
            out.append(n.stem)
    return sorted(out)


def find_dangling_designs(notes: list[Note]) -> list[str]:
    """A spec-design is dangling when it doesn't wikilink to any PRD."""
    prd_stems = {n.stem for n in notes if n.doc_type == "prd"}
    out: list[str] = []
    for n in notes:
        if n.doc_type != "spec-design":
            continue
        targets = set(n.wikilinks)
        if not targets & prd_stems:
            out.append(n.stem)
    return sorted(out)


def find_unimplemented_prds(notes: list[Note]) -> list[str]:
    """A PRD is unimplemented when no spec-* note wikilinks back to it."""
    prd_by_stem = {n.stem: n for n in notes if n.doc_type == "prd"}
    referenced: set[str] = set()
    for n in notes:
        if n.doc_type not in SPEC_TYPES:
            continue
        for target in n.wikilinks:
            if target in prd_by_stem:
                referenced.add(target)
    return sorted(set(prd_by_stem) - referenced)


# ---------------------------------------------------------------------------
# markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(report: Report) -> str:
    lines: list[str] = []
    lines.append("# Traceability report")
    lines.append("")
    lines.append(f"_Vault: `{report.vault_root}`_")
    lines.append("")

    lines.append("## Features")
    lines.append("")
    if not report.features:
        lines.append("_No feature slugs discovered under `04-specs/`._")
    else:
        lines.append("| Slug | PRD refs | Requirements | Design | Tasks (count) | Reviews | Coverage |")
        lines.append("|------|----------|--------------|--------|---------------|---------|----------|")
        for f in report.features:
            prd = ", ".join(f.prd_refs) or "—"
            req = "[x]" if f.requirements["exists"] else "[ ]"
            des = "[x]" if f.design["exists"] else "[ ]"
            tsk = (
                f"[x] ({f.tasks['task_count']})"
                if f.tasks["exists"]
                else "[ ]"
            )
            reviews = ", ".join(f.reviews) or "—"
            lines.append(
                f"| `{f.slug}` | {prd} | {req} | {des} | {tsk} | {reviews} | {f.coverage_status} |"
            )
    lines.append("")

    lines.append("## Gaps")
    lines.append("")
    lines.append(f"- **Dangling designs** (no upstream PRD): {', '.join(report.dangling_designs) or '_none_'}")
    lines.append(f"- **Unimplemented PRDs** (no downstream spec): {', '.join(report.unimplemented_prds) or '_none_'}")
    lines.append(f"- **Orphan ADRs** (no incoming wikilinks): {', '.join(report.orphan_adrs) or '_none_'}")
    lines.append(f"- **Orphan TRDs** (no incoming wikilinks): {', '.join(report.orphan_trds) or '_none_'}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# action: report
# ---------------------------------------------------------------------------

def action_report(
    vault_root: Path,
    *,
    slug_filter: str | None,
    output_format: str,
    report: Report,
) -> None:
    report.format = output_format

    notes = collect_notes(vault_root)
    incoming = build_incoming_index(notes)
    slugs = discover_feature_slugs(notes, vault_root)

    if slug_filter:
        if slug_filter not in slugs:
            # Still emit a row so the consumer knows the slug was unknown.
            report.features = [FeatureRow(slug=slug_filter, coverage_status="missing")]
        else:
            report.features = [build_feature_row(slug_filter, notes, vault_root)]
    else:
        report.features = [build_feature_row(s, notes, vault_root) for s in slugs]

    # Gap detection always runs over the whole vault, even with --slug: if the
    # user is focusing on one feature, they still benefit from the global view.
    report.orphan_adrs = find_orphan_by_type(notes, "adr", incoming)
    report.orphan_trds = find_orphan_by_type(notes, "trd", incoming)
    report.dangling_designs = find_dangling_designs(notes)
    report.unimplemented_prds = find_unimplemented_prds(notes)

    if output_format == "markdown":
        report.markdown = render_markdown(report)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit traceability reporter.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        default="report",
        choices=["report"],
        help="only `report` is supported",
    )
    p.add_argument("--slug", help="narrow the report to a single feature slug")
    p.add_argument(
        "--format",
        dest="fmt",
        default="json",
        choices=["json", "markdown"],
        help="output format (json default, markdown renders a human-readable matrix)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    try:
        action_report(
            vault,
            slug_filter=args.slug,
            output_format=args.fmt,
            report=report,
        )
    except PermissionError as exc:
        die(report, f"permission denied: {exc}", code=2)
    except OSError as exc:
        die(report, f"filesystem error: {exc}", code=2)

    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
