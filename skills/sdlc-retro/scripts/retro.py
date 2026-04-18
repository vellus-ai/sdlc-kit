#!/usr/bin/env python3
"""Manage sprint/iteration retrospectives under `07-retrospectives/retros/`.

A retro captures the outcome of a sprint or iteration retrospective — the
"went well / went badly" content, the action items with owner + due date,
and the team-mood + metrics snapshot. One file per retro, identified by
slug (usually `sprint-<NN>` or `iteration-YYYY-Qn-wW`), because the slug
is the stable reference a reader can recognize at a glance.

Files live at:

    07-retrospectives/retros/<slug>.md

Lifecycle:

    draft  →  final

`draft` is the scaffolded state — the facilitator is capturing meeting
notes and the team is still filling in Keep/Improve/Stop/Actions.
`final` means the retro meeting is over, action items are ratified
(each with owner + due date), and the record is historical.

Actions:
    list
        Enumerate every retro with slug, status, title, owner, sprint,
        updated.
    scaffold --slug S --title T [--owner O] [--sprint N] [--force]
        Copy `07-retrospectives/_templates/retro.md.tpl` to
        `07-retrospectives/retros/<slug>.md`, applying placeholders. If
        `--sprint` is passed, the `sprint:` frontmatter field is pre-filled
        so the note carries sprint context from the first save. Refuses to
        overwrite unless --force.
    transition --slug S --to {draft|final}
        Flip `status:` and refresh `updated`. Idempotent when already at
        the target status.

The LLM drives the content interview (Keep/Improve/Stop, action items,
team mood, metrics) via Edit/Write. This script only handles deterministic
file operations.

Emits a single JSON object on stdout. Exit codes: 0 ok/dry-run, 1 user
error, 2 fatal.
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

from core.frontmatter import read_frontmatter, set_quoted_field  # noqa: E402
from core.regexes import FRONTMATTER_RE, SLUG_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402

# Retro-specific frontmatter field (not shared with other skills).
_SPRINT_LINE = re.compile(r'^(sprint:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)


RETRO_DIR = "07-retrospectives"
RETROS_DIR = "retros"
TEMPLATES_DIR = "_templates"
TEMPLATE_NAME = "retro.md.tpl"
MARKER_REL = ".sdlc-kit/marker.json"

VALID_STATUSES: tuple[str, ...] = ("draft", "final")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class RetroState:
    slug: str
    path: str
    title: str = ""
    status: str = ""
    owner: str = ""
    sprint: str = ""
    updated: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    slug: str = ""
    retro_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    retros: list[RetroState] = field(default_factory=list)
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
            d["retros"] = [vars(x) for x in self.retros]
            d["count"] = self.count
        elif self.action == "scaffold":
            d["slug"] = self.slug
            d["retro_path"] = self.retro_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["slug"] = self.slug
            d["retro_path"] = self.retro_path
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


def retros_folder(vault: Path) -> Path:
    return vault / RETRO_DIR / RETROS_DIR


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, report: Report) -> None:
    report.action = "list"
    folder = retros_folder(vault)
    if not folder.exists():
        return
    for path in sorted(p for p in folder.glob("*.md") if not p.name.startswith("_")):
        fm = read_frontmatter(path)
        report.retros.append(RetroState(
            slug=path.stem,
            path=rel(vault, path),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            owner=fm.get("owner", ""),
            sprint=fm.get("sprint", ""),
            updated=fm.get("updated", ""),
        ))
    report.count = len(report.retros)


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
    sprint: str | None,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.slug = slug

    if not SLUG_RE.match(slug):
        die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)

    template = vault / RETRO_DIR / TEMPLATES_DIR / TEMPLATE_NAME
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target = retros_folder(vault) / f"{slug}.md"
    report.retro_path = rel(vault, target)

    if target.exists() and not force:
        die(
            report,
            f"retro already exists: {report.retro_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    replacements = build_replacements(vault, title=title, slug=slug, owner=owner, today=today)
    content = apply_placeholders(template.read_text(encoding="utf-8"), replacements)

    # Optional frontmatter metadata injected at scaffold time so the note carries
    # sprint context from the first save — no need for a manual edit pass.
    if sprint:
        m = FRONTMATTER_RE.match(content)
        if m:
            fm_text = m.group(1)
            body = content[m.end():]
            fm_text = set_quoted_field(fm_text, _SPRINT_LINE, "sprint", sprint)
            content = f"---\n{fm_text}\n---\n{body}"

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

    target = retros_folder(vault) / f"{slug}.md"
    report.retro_path = rel(vault, target)

    if not target.exists():
        die(report, f"retro not found: {report.retro_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.retro_path}", code=1)

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
    p = argparse.ArgumentParser(description="SDLC Kit retro manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate retros | scaffold: materialize from template | transition: change status",
    )
    p.add_argument("--slug", help="retro slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="retro owner/facilitator (falls back to marker.json owner)")
    p.add_argument("--sprint", help="sprint identifier to pre-fill in frontmatter (scaffold only)")
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
                sprint=args.sprint,
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
