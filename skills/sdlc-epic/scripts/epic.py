#!/usr/bin/env python3
"""Manage epics under `01-planning/epic/`.

An epic is a large deliverable decomposed from a PRD: it groups related
stories (often 1 story = 1 spec trio under `04-specs/<feature>/`) and usually
rolls up into a milestone. One file per epic — never auto-overwritten.

Actions:
    list                Enumerate every epic found in `01-planning/epic/`.
    scaffold --slug X --title T [--owner O]
                        Copy `01-planning/_templates/epic.md.tpl` →
                        `01-planning/epic/<slug>.md`, applying placeholders.
                        Refuses to overwrite unless `--force`.
    transition --slug X --to {planned|in-progress|done|cancelled}
                        Flip `status:` in the frontmatter and refresh
                        `updated`. No-op when already at the target status.

The LLM drives the interview (objective, stories, scope, acceptance,
dependencies) and section-by-section editing via Edit/Write; this script
only handles deterministic file operations.

Emits a single JSON object on stdout. Exit codes: 0 ok/dry-run, 1 user error,
2 fatal.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.regexes import FRONTMATTER_RE, SLUG_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402
from core.frontmatter import read_frontmatter  # noqa: E402


PLANNING_DIR = "01-planning"
EPIC_DIR = "epic"
TEMPLATES_DIR = "_templates"
TEMPLATE_NAME = "epic.md.tpl"
MARKER_REL = ".sdlc-kit/marker.json"

VALID_STATUSES: tuple[str, ...] = ("planned", "in-progress", "done", "cancelled")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class EpicState:
    slug: str
    path: str
    title: str = ""
    status: str = ""
    owner: str = ""
    prd: str = ""
    milestone: str = ""
    updated: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    slug: str = ""
    epic_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    epics: list[EpicState] = field(default_factory=list)
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
            d["epics"] = [vars(x) for x in self.epics]
            d["count"] = self.count
        elif self.action == "scaffold":
            d["slug"] = self.slug
            d["epic_path"] = self.epic_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["slug"] = self.slug
            d["epic_path"] = self.epic_path
            d["previous_status"] = self.previous_status
            d["new_status"] = self.new_status
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


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, report: Report) -> None:
    report.action = "list"
    epic_dir = vault / PLANNING_DIR / EPIC_DIR
    if not epic_dir.exists():
        report.count = 0
        return
    files = sorted(p for p in epic_dir.glob("*.md") if not p.name.startswith("_"))
    for path in files:
        fm = read_frontmatter(path)
        report.epics.append(EpicState(
            slug=path.stem,
            path=rel(vault, path),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            owner=fm.get("owner", ""),
            prd=fm.get("prd", ""),
            milestone=fm.get("milestone", ""),
            updated=fm.get("updated", ""),
        ))
    report.count = len(report.epics)


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

    template = vault / PLANNING_DIR / TEMPLATES_DIR / TEMPLATE_NAME
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target = vault / PLANNING_DIR / EPIC_DIR / f"{slug}.md"
    report.epic_path = rel(vault, target)

    if target.exists() and not force:
        die(
            report,
            f"epic already exists: {report.epic_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    replacements = build_replacements(vault, title=title, slug=slug, owner=owner, today=today)
    content = apply_placeholders(template.read_text(encoding="utf-8"), replacements)

    report.was_new = not target.exists()
    if dry_run:
        report.status = "dry-run"
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# action: transition
# ---------------------------------------------------------------------------

def action_transition(
    vault: Path,
    *,
    slug: str,
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

    target = vault / PLANNING_DIR / EPIC_DIR / f"{slug}.md"
    report.epic_path = rel(vault, target)

    if not target.exists():
        die(report, f"epic not found: {report.epic_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.epic_path}", code=1)

    fm_text = m.group(1)
    body = text[m.end():]

    status_match = STATUS_LINE.search(fm_text)
    current_status = status_match.group(2) if status_match else ""
    report.previous_status = current_status
    report.new_status = target_status

    if current_status == target_status:
        return  # idempotent

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

    if dry_run:
        report.status = "dry-run"
        return
    target.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit epic manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate epics | scaffold: materialize from template | transition: change status",
    )
    p.add_argument("--slug", help="epic slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="epic owner (falls back to marker.json owner)")
    p.add_argument(
        "--to",
        dest="to_status",
        choices=list(VALID_STATUSES),
        help="target status (required for transition)",
    )
    p.add_argument("--force", action="store_true", help="overwrite existing target (scaffold only)")
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
        if not args.slug or not args.to_status:
            die(report, "--slug and --to are required for action `transition`", code=1)

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
            action_transition(
                vault,
                slug=args.slug,
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
