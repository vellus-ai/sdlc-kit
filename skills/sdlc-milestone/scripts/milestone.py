#!/usr/bin/env python3
"""Manage milestones under `01-planning/milestone/`.

A milestone is a delivery window that groups one or more epics toward a
single target date. It carries an RAG-style status through its lifecycle:
    planned → on-track → done
            ↘ at-risk ↗↘ slipped
    cancelled is reachable from any state.

One file per milestone — never auto-overwritten.

Actions:
    list                Enumerate every milestone in `01-planning/milestone/`.
    scaffold --slug X --title T [--owner O] [--target-date YYYY-MM-DD]
                        Copy `01-planning/_templates/milestone.md.tpl` →
                        `01-planning/milestone/<slug>.md`, applying
                        placeholders. Optionally sets the `target_date:`
                        frontmatter field. Refuses to overwrite unless
                        `--force`.
    transition --slug X --to {planned|on-track|at-risk|slipped|done|cancelled}
                        Flip `status:` and refresh `updated`. No-op when
                        already at the target status.

The LLM drives the interview (target date, scope, success criteria, risks,
dependencies) and section-by-section editing via Edit; this script only
handles deterministic file operations. RAG-style health is a qualitative
call the user makes — no auto-derivation from dates or percentages.

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
MILESTONE_DIR = "milestone"
TEMPLATES_DIR = "_templates"
TEMPLATE_NAME = "milestone.md.tpl"
MARKER_REL = ".sdlc-kit/marker.json"

VALID_STATUSES: tuple[str, ...] = (
    "planned", "on-track", "at-risk", "slipped", "done", "cancelled",
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class MilestoneState:
    slug: str
    path: str
    title: str = ""
    status: str = ""
    owner: str = ""
    target_date: str = ""
    updated: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    slug: str = ""
    milestone_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    milestones: list[MilestoneState] = field(default_factory=list)
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
            d["milestones"] = [vars(x) for x in self.milestones]
            d["count"] = self.count
        elif self.action == "scaffold":
            d["slug"] = self.slug
            d["milestone_path"] = self.milestone_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["slug"] = self.slug
            d["milestone_path"] = self.milestone_path
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


_TARGET_DATE_LINE = re.compile(r"^(target_date:\s*)(.*)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, report: Report) -> None:
    report.action = "list"
    ms_dir = vault / PLANNING_DIR / MILESTONE_DIR
    if not ms_dir.exists():
        report.count = 0
        return
    files = sorted(p for p in ms_dir.glob("*.md") if not p.name.startswith("_"))
    for path in files:
        fm = read_frontmatter(path)
        report.milestones.append(MilestoneState(
            slug=path.stem,
            path=rel(vault, path),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            owner=fm.get("owner", ""),
            target_date=fm.get("target_date", ""),
            updated=fm.get("updated", ""),
        ))
    report.count = len(report.milestones)


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


def set_target_date(text: str, target_date: str) -> str:
    """Rewrite the `target_date:` frontmatter field in-place."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return text
    fm_text = m.group(1)
    rest = text[m.end():]
    if _TARGET_DATE_LINE.search(fm_text):
        new_fm = _TARGET_DATE_LINE.sub(rf'\g<1>"{target_date}"', fm_text, count=1)
    else:
        new_fm = fm_text + f'\ntarget_date: "{target_date}"'
    return f"---\n{new_fm}\n---\n{rest}"


def action_scaffold(
    vault: Path,
    *,
    slug: str,
    title: str,
    owner: str | None,
    target_date: str | None,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.slug = slug

    if not SLUG_RE.match(slug):
        die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)
    if target_date and not _DATE_RE.match(target_date):
        die(report, f"invalid --target-date `{target_date}`: expected YYYY-MM-DD", code=1)

    template = vault / PLANNING_DIR / TEMPLATES_DIR / TEMPLATE_NAME
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target = vault / PLANNING_DIR / MILESTONE_DIR / f"{slug}.md"
    report.milestone_path = rel(vault, target)

    if target.exists() and not force:
        die(
            report,
            f"milestone already exists: {report.milestone_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    replacements = build_replacements(vault, title=title, slug=slug, owner=owner, today=today)
    content = apply_placeholders(template.read_text(encoding="utf-8"), replacements)
    if target_date:
        content = set_target_date(content, target_date)

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

    target = vault / PLANNING_DIR / MILESTONE_DIR / f"{slug}.md"
    report.milestone_path = rel(vault, target)

    if not target.exists():
        die(report, f"milestone not found: {report.milestone_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.milestone_path}", code=1)

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
    p = argparse.ArgumentParser(description="SDLC Kit milestone manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate milestones | scaffold: materialize from template | transition: change status",
    )
    p.add_argument("--slug", help="milestone slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="milestone owner (falls back to marker.json owner)")
    p.add_argument("--target-date", help="YYYY-MM-DD; written to `target_date:` frontmatter (scaffold only)")
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
                target_date=args.target_date,
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
