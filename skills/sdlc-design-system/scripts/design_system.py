#!/usr/bin/env python3
"""Manage design-system entries under `06-design-system/`.

The design system is composed of three atomic kinds:

    design-token      — atomic visual value (color, spacing, typography, etc.)
    design-component  — reusable UI component spec (API, variants, states)
    design-pattern    — recurring combination of components solving an
                        interaction problem

One file per entry, stored under:

    06-design-system/tokens/<slug>.md
    06-design-system/components/<slug>.md
    06-design-system/patterns/<slug>.md

Lifecycle (shared by the three kinds):

    draft  → stable  → deprecated

`draft` is the scaffolded state; `stable` means the item is vetted and
approved for consumption; `deprecated` is kept for history but should no
longer be adopted in new work.

Actions:
    list [--kind {token|component|pattern}]
        Enumerate entries of the given kind, or all three kinds if --kind is
        omitted.
    scaffold --kind {token|component|pattern} --slug X --title T [--owner O]
        Copy the matching `_templates/<kind>.md.tpl` to
        `06-design-system/<kind>s/<slug>.md`, applying placeholders. Refuses
        to overwrite unless `--force`.
    transition --kind {token|component|pattern} --slug X --to {draft|stable|deprecated}
        Flip the `status:` frontmatter field and refresh `updated`.
        Idempotent: no write when already at the target status.

The LLM drives the interview (category/value/aliases for tokens, API/variants
/accessibility for components, structure/variations for patterns) and
section-by-section editing via Edit; this script only handles deterministic
file operations.

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


DESIGN_DIR = "06-design-system"
TEMPLATES_DIR = "_templates"
MARKER_REL = ".sdlc-kit/marker.json"

# Map of kind → (template filename, subfolder name, canonical doc_type).
KIND_CONFIG: dict[str, tuple[str, str, str]] = {
    "token":     ("token.md.tpl",     "tokens",     "design-token"),
    "component": ("component.md.tpl", "components", "design-component"),
    "pattern":   ("pattern.md.tpl",   "patterns",   "design-pattern"),
}

VALID_KINDS: tuple[str, ...] = tuple(KIND_CONFIG.keys())
VALID_STATUSES: tuple[str, ...] = ("draft", "stable", "deprecated")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class EntryState:
    kind: str
    slug: str
    path: str
    title: str = ""
    status: str = ""
    owner: str = ""
    updated: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    kind: str = ""
    slug: str = ""
    entry_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    entries: list[EntryState] = field(default_factory=list)
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
            d["kind"] = self.kind  # empty string = all kinds
            d["entries"] = [vars(x) for x in self.entries]
            d["count"] = self.count
        elif self.action == "scaffold":
            d["kind"] = self.kind
            d["slug"] = self.slug
            d["entry_path"] = self.entry_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["kind"] = self.kind
            d["slug"] = self.slug
            d["entry_path"] = self.entry_path
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


def subfolder_for(vault: Path, kind: str) -> Path:
    _, subfolder, _ = KIND_CONFIG[kind]
    return vault / DESIGN_DIR / subfolder


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def _collect_kind(vault: Path, kind: str) -> list[EntryState]:
    folder = subfolder_for(vault, kind)
    if not folder.exists():
        return []
    out: list[EntryState] = []
    for path in sorted(p for p in folder.glob("*.md") if not p.name.startswith("_")):
        fm = read_frontmatter(path)
        out.append(EntryState(
            kind=kind,
            slug=path.stem,
            path=rel(vault, path),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            owner=fm.get("owner", ""),
            updated=fm.get("updated", ""),
        ))
    return out


def action_list(vault: Path, *, kind: str | None, report: Report) -> None:
    report.action = "list"
    report.kind = kind or ""
    kinds = [kind] if kind else list(VALID_KINDS)
    for k in kinds:
        report.entries.extend(_collect_kind(vault, k))
    report.count = len(report.entries)


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
    kind: str,
    slug: str,
    title: str,
    owner: str | None,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.kind = kind
    report.slug = slug

    if kind not in KIND_CONFIG:
        die(report, f"invalid --kind `{kind}` — allowed: {', '.join(VALID_KINDS)}", code=1)
    if not SLUG_RE.match(slug):
        die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)

    template_name, _, _ = KIND_CONFIG[kind]
    template = vault / DESIGN_DIR / TEMPLATES_DIR / template_name
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target_dir = subfolder_for(vault, kind)
    target = target_dir / f"{slug}.md"
    report.entry_path = rel(vault, target)

    if target.exists() and not force:
        die(
            report,
            f"{kind} already exists: {report.entry_path} (use --force to overwrite)",
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
    kind: str,
    slug: str,
    target_status: str,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "transition"
    report.kind = kind
    report.slug = slug

    if kind not in KIND_CONFIG:
        die(report, f"invalid --kind `{kind}` — allowed: {', '.join(VALID_KINDS)}", code=1)
    if target_status not in VALID_STATUSES:
        die(
            report,
            f"invalid status `{target_status}` — allowed: {', '.join(VALID_STATUSES)}",
            code=1,
        )

    target = subfolder_for(vault, kind) / f"{slug}.md"
    report.entry_path = rel(vault, target)

    if not target.exists():
        die(report, f"{kind} not found: {report.entry_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.entry_path}", code=1)

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
    p = argparse.ArgumentParser(description="SDLC Kit design-system manager (tokens / components / patterns).")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate entries | scaffold: materialize from template | transition: change status",
    )
    p.add_argument(
        "--kind",
        choices=list(VALID_KINDS),
        help="token | component | pattern — required for scaffold/transition; optional filter for list",
    )
    p.add_argument("--slug", help="entry slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="entry owner (falls back to marker.json owner)")
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
        if not args.kind or not args.slug or not args.title:
            die(report, "--kind, --slug and --title are required for action `scaffold`", code=1)
    if args.action == "transition":
        if not args.kind or not args.slug or not args.to_status:
            die(report, "--kind, --slug and --to are required for action `transition`", code=1)

    try:
        if args.action == "list":
            action_list(vault, kind=args.kind, report=report)
        elif args.action == "scaffold":
            action_scaffold(
                vault,
                kind=args.kind,
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
                kind=args.kind,
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
