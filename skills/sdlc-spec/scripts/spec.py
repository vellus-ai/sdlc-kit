#!/usr/bin/env python3
"""Manage Spec-Driven Development trios under `04-specs/<slug>/`.

Each spec is a folder containing three documents that share one feature slug:
    requirements.md  — what the system must do (EARS notation).
    design.md        — how it will be built (architecture, flows, data model).
    tasks.md         — executable task list traced back to requirements.

The trio is the unit of work — scaffolding creates all three at once, and the
LLM drives the section-by-section content authoring through approval gates
(requirements → design → tasks). Status transitions are per-doc: requirements
can be `approved` while design is still `draft`.

Actions:
    list                       Enumerate every spec folder under `04-specs/`,
                               grouped by feature slug, each with the three
                               doc statuses.
    scaffold --slug X --title T [--owner O]
                               Copy the three templates from
                               `04-specs/_templates/` into
                               `04-specs/<slug>/{requirements,design,tasks}.md`
                               applying placeholders. Per-file: skip if it
                               already exists (unless `--force`).
    transition --slug X --doc {requirements|design|tasks|all}
               --to {draft|approved|implemented|archived}
                               Flip `status:` in the selected doc(s) and
                               refresh `updated`. No-op when already at the
                               target status.

Emits a single JSON object on stdout. Exit codes: 0 ok/dry-run, 1 user error,
2 fatal.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.frontmatter import read_frontmatter  # noqa: E402
from core.regexes import FRONTMATTER_RE, SLUG_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402

SPECS_DIR = "04-specs"
TEMPLATES_DIR = "_templates"
MARKER_REL = ".sdlc-kit/marker.json"

# Three canonical documents of the SDD trio. Filename (without extension) is
# also the "kind" identifier exposed to the CLI.
DOC_KINDS: tuple[str, ...] = ("requirements", "design", "tasks")
TEMPLATE_BY_KIND: dict[str, str] = {
    "requirements": "requirements.md.tpl",
    "design":       "design.md.tpl",
    "tasks":        "tasks.md.tpl",
}

VALID_STATUSES: tuple[str, ...] = ("draft", "approved", "implemented", "archived")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class SpecDoc:
    kind: str              # requirements | design | tasks
    path: str              # vault-relative path
    exists: bool = False
    title: str = ""
    status: str = ""
    updated: str = ""


@dataclass
class SpecFeature:
    slug: str
    path: str              # vault-relative path to the feature folder
    docs: list[SpecDoc] = field(default_factory=list)


@dataclass
class DocResult:
    kind: str
    path: str
    was_new: bool = False
    skipped: bool = False              # scaffold: existed and no --force
    previous_status: str = ""          # transition
    new_status: str = ""               # transition
    changed: bool = False              # transition: false when idempotent


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    slug: str = ""
    spec_dir: str = ""
    docs: list[DocResult] = field(default_factory=list)
    features: list[SpecFeature] = field(default_factory=list)
    count: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d: dict = {
            "status": self.status,
            "action": self.action,
            "vault_root": self.vault_root,
            "errors": self.errors,
        }
        if self.action == "list":
            d["features"] = [
                {
                    "slug": f.slug,
                    "path": f.path,
                    "docs": [vars(x) for x in f.docs],
                }
                for f in self.features
            ]
            d["count"] = self.count
        elif self.action == "scaffold" or self.action == "transition":
            d["slug"] = self.slug
            d["spec_dir"] = self.spec_dir
            d["docs"] = [vars(x) for x in self.docs]
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


def load_marker(vault: Path) -> dict:
    path = vault / MARKER_REL
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def rel(vault: Path, path: Path) -> str:
    return str(path.relative_to(vault)).replace("\\", "/")


# that usually follows the closing frontmatter fence.


def resolve_doc_selector(raw: str) -> list[str]:
    """Turn `--doc requirements|design|tasks|all` into a list of kinds."""
    norm = raw.strip().lower()
    if norm == "all":
        return list(DOC_KINDS)
    if norm in DOC_KINDS:
        return [norm]
    raise ValueError(
        f"invalid --doc `{raw}` — expected one of: {', '.join(list(DOC_KINDS) + ['all'])}"
    )


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, report: Report) -> None:
    report.action = "list"
    specs_dir = vault / SPECS_DIR
    if not specs_dir.exists():
        report.count = 0
        return

    for sub in sorted(p for p in specs_dir.iterdir() if p.is_dir()):
        if sub.name.startswith("_") or sub.name.startswith("."):
            continue  # skip _templates, hidden dirs

        feature = SpecFeature(slug=sub.name, path=rel(vault, sub))
        for kind in DOC_KINDS:
            doc_path = sub / f"{kind}.md"
            doc = SpecDoc(kind=kind, path=rel(vault, doc_path))
            if doc_path.exists():
                fm = read_frontmatter(doc_path)
                doc.exists = True
                doc.title = fm.get("title", "")
                doc.status = fm.get("status", "")
                doc.updated = fm.get("updated", "")
            feature.docs.append(doc)
        report.features.append(feature)
    report.count = len(report.features)


# ---------------------------------------------------------------------------
# action: scaffold
# ---------------------------------------------------------------------------

def build_replacements(
    vault: Path,
    *,
    title: str,
    slug: str,
    owner: str | None,
    today: str,
) -> dict[str, str]:
    marker = load_marker(vault)
    resolved_owner = owner or marker.get("owner") or "_tbd_"
    return {
        "{{TITLE}}": title,
        "{{SLUG}}": slug,
        "{{OWNER}}": resolved_owner,
        "{{DATE}}": today,
        "{{PROJECT_NAME}}": marker.get("project_name") or "",
    }


def apply_placeholders(text: str, replacements: dict[str, str]) -> str:
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def action_scaffold(
    vault: Path,
    *,
    slug: str,
    title: str,
    owner: str | None,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.slug = slug

    if not SLUG_RE.match(slug):
        die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)

    templates_dir = vault / SPECS_DIR / TEMPLATES_DIR
    for kind in DOC_KINDS:
        tpl = templates_dir / TEMPLATE_BY_KIND[kind]
        if not tpl.exists():
            die(report, f"template not found: {rel(vault, tpl)}", code=2)

    spec_dir = vault / SPECS_DIR / slug
    report.spec_dir = rel(vault, spec_dir)

    today = _dt.date.today().isoformat()
    replacements = build_replacements(vault, title=title, slug=slug, owner=owner, today=today)

    # Plan all three doc operations before writing anything.
    plan: list[tuple[str, Path, Path, bool]] = []  # (kind, template, target, skip)
    for kind in DOC_KINDS:
        tpl = templates_dir / TEMPLATE_BY_KIND[kind]
        target = spec_dir / f"{kind}.md"
        skip = target.exists() and not force
        plan.append((kind, tpl, target, skip))

    for kind, tpl, target, skip in plan:
        result = DocResult(kind=kind, path=rel(vault, target))
        if skip:
            result.skipped = True
            result.was_new = False
        else:
            result.skipped = False
            result.was_new = not target.exists()
            if not dry_run:
                spec_dir.mkdir(parents=True, exist_ok=True)
                content = apply_placeholders(tpl.read_text(encoding="utf-8"), replacements)
                target.write_text(content, encoding="utf-8")
        report.docs.append(result)

    if dry_run:
        report.status = "dry-run"


# ---------------------------------------------------------------------------
# action: transition
# ---------------------------------------------------------------------------

def transition_one(
    vault: Path,
    *,
    target_path: Path,
    target_status: str,
) -> DocResult:
    """Flip status in one doc; idempotent if already at target."""
    kind = target_path.stem  # requirements | design | tasks
    result = DocResult(kind=kind, path=rel(vault, target_path))

    if not target_path.exists():
        result.previous_status = ""
        result.new_status = ""
        result.changed = False
        return result

    text = target_path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        result.previous_status = ""
        result.new_status = ""
        result.changed = False
        return result

    fm_text = m.group(1)
    body = text[m.end():]

    status_match = STATUS_LINE.search(fm_text)
    current_status = status_match.group(2) if status_match else ""
    result.previous_status = current_status
    result.new_status = target_status

    if current_status == target_status:
        result.changed = False
        return result

    new_fm = (
        STATUS_LINE.sub(rf"\g<1>{target_status}", fm_text, count=1)
        if status_match
        else fm_text + f"\nstatus: {target_status}"
    )
    today = _dt.date.today().isoformat()
    if UPDATED_LINE.search(new_fm):
        new_fm = UPDATED_LINE.sub(rf"\g<1>{today}", new_fm, count=1)
    else:
        new_fm = new_fm + f"\nupdated: {today}"

    new_text = f"---\n{new_fm}\n---\n{body}"
    target_path.write_text(new_text, encoding="utf-8")
    result.changed = True
    return result


def action_transition(
    vault: Path,
    *,
    slug: str,
    kinds: list[str],
    target_status: str,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "transition"
    report.slug = slug

    if target_status not in VALID_STATUSES:
        die(
            report,
            f"invalid status `{target_status}` — allowed: {', '.join(VALID_STATUSES)}",
            code=1,
        )

    spec_dir = vault / SPECS_DIR / slug
    report.spec_dir = rel(vault, spec_dir)
    if not spec_dir.exists():
        die(report, f"spec folder not found: {report.spec_dir} (run scaffold first)", code=1)

    # Report a missing doc per kind rather than aborting when only one is absent.
    for kind in kinds:
        target = spec_dir / f"{kind}.md"
        if not target.exists():
            result = DocResult(kind=kind, path=rel(vault, target))
            result.changed = False
            report.docs.append(result)
            continue
        if dry_run:
            # Simulate without writing.
            text = target.read_text(encoding="utf-8")
            fm_match = FRONTMATTER_RE.match(text)
            current = ""
            if fm_match:
                s = STATUS_LINE.search(fm_match.group(1))
                current = s.group(2) if s else ""
            result = DocResult(kind=kind, path=rel(vault, target))
            result.previous_status = current
            result.new_status = target_status
            result.changed = current != target_status
            report.docs.append(result)
        else:
            report.docs.append(
                transition_one(vault, target_path=target, target_status=target_status)
            )

    if dry_run:
        report.status = "dry-run"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit spec-trio manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate specs | scaffold: create the trio | transition: change status",
    )
    p.add_argument("--slug", help="feature slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="owner (falls back to marker.json owner)")
    p.add_argument(
        "--doc",
        choices=list(DOC_KINDS) + ["all"],
        help="which doc(s) to transition (required for transition)",
    )
    p.add_argument(
        "--to",
        dest="to_status",
        choices=list(VALID_STATUSES),
        help="target status (required for transition)",
    )
    p.add_argument("--force", action="store_true", help="overwrite existing targets (scaffold only)")
    p.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    if args.action == "scaffold":
        if not args.slug or not args.title:
            die(report, "--slug and --title are required for action `scaffold`", code=1)
    if args.action == "transition":
        if not args.slug or not args.doc or not args.to_status:
            die(report, "--slug, --doc and --to are required for action `transition`", code=1)

    try:
        if args.action == "list":
            action_list(vault, report)
        elif args.action == "scaffold":
            action_scaffold(
                vault,
                slug=args.slug,
                title=args.title,
                owner=args.owner,
                force=args.force,
                dry_run=args.dry_run,
                report=report,
            )
        elif args.action == "transition":
            try:
                kinds = resolve_doc_selector(args.doc)
            except ValueError as exc:
                die(report, str(exc), code=1)
            action_transition(
                vault,
                slug=args.slug,
                kinds=kinds,
                target_status=args.to_status,
                dry_run=args.dry_run,
                report=report,
            )
    except PermissionError as exc:
        die(report, f"permission denied: {exc}", code=2)
    except OSError as exc:
        die(report, f"filesystem error: {exc}", code=2)

    if report.status == "ok" and args.dry_run:
        report.status = "dry-run"
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
