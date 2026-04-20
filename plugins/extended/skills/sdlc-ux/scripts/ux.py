#!/usr/bin/env python3
"""Manage UX research artifacts under `06-design-system/`.

Three kinds are supported:

    ux-criteria     — personas, JTBD, acceptance criteria (singleton per vault)
    user-flows      — user journey flows mapped to JTBDs (singleton per vault)
    wireframe       — lo-fi screen spec (collection; one file per slug)

Paths:

    06-design-system/ux-criteria.md
    06-design-system/user-flows.md
    06-design-system/wireframes/<slug>.md

Lifecycle (shared):

    draft  →  approved  →  deprecated

Actions:
    list [--kind K]
        Enumerate UX artifacts (all kinds if --kind omitted).
    scaffold --kind K --title T [--slug S] [--prd-slug P] [--owner O] [--force]
        Copy template into the right target. --slug required for wireframe,
        forbidden for ux-criteria / user-flows.
    transition --kind K [--slug S] --to {draft|approved|deprecated}
        Flip status + refresh updated. Idempotent.

Emits a single JSON object on stdout. Exit codes: 0 ok/dry-run, 1 user error, 2 fatal.
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
from core.regexes import SLUG_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402

DESIGN_DIR = "06-design-system"
TEMPLATES_DIR = "_templates"
MARKER_REL = ".sdlc-kit/marker.json"

# (template_name, subfolder_or_None, doc_type, is_singleton)
KIND_CONFIG: dict[str, tuple[str, str | None, str, bool]] = {
    "ux-criteria": ("ux-criteria.md.tpl",   None,         "ux-criteria", True),
    "user-flows":  ("user-flows.md.tpl",    None,         "user-flows",  True),
    "wireframe":   ("wireframe.md.tpl",      "wireframes", "wireframe",   False),
}

VALID_KINDS: tuple[str, ...] = tuple(KIND_CONFIG.keys())
VALID_STATUSES: tuple[str, ...] = ("draft", "approved", "deprecated")


@dataclass
class ArtifactState:
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
    artifact_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    artifacts: list[ArtifactState] = field(default_factory=list)
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
            d["kind"] = self.kind
            d["artifacts"] = [vars(x) for x in self.artifacts]
            d["count"] = self.count
        elif self.action == "scaffold":
            d["kind"] = self.kind
            d["slug"] = self.slug
            d["artifact_path"] = self.artifact_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["kind"] = self.kind
            d["slug"] = self.slug
            d["artifact_path"] = self.artifact_path
            d["previous_status"] = self.previous_status
            d["new_status"] = self.new_status
        return d


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


def target_path(vault: Path, kind: str, slug: str | None) -> Path:
    _, subfolder, _, is_singleton = KIND_CONFIG[kind]
    base = vault / DESIGN_DIR
    if is_singleton:
        return base / f"{kind}.md"
    return base / subfolder / f"{slug}.md"


def action_list(vault: Path, *, kind: str | None, report: Report) -> None:
    report.action = "list"
    report.kind = kind or ""
    kinds = [kind] if kind else list(VALID_KINDS)
    for k in kinds:
        _, subfolder, _, is_singleton = KIND_CONFIG[k]
        if is_singleton:
            p = vault / DESIGN_DIR / f"{k}.md"
            if p.exists():
                fm = read_frontmatter(p)
                report.artifacts.append(ArtifactState(
                    kind=k, slug=k, path=rel(vault, p),
                    title=fm.get("title", ""), status=fm.get("status", ""),
                    owner=fm.get("owner", ""), updated=fm.get("updated", ""),
                ))
        else:
            folder = vault / DESIGN_DIR / subfolder
            if folder.exists():
                for p in sorted(x for x in folder.glob("*.md") if not x.name.startswith("_")):
                    fm = read_frontmatter(p)
                    report.artifacts.append(ArtifactState(
                        kind=k, slug=p.stem, path=rel(vault, p),
                        title=fm.get("title", ""), status=fm.get("status", ""),
                        owner=fm.get("owner", ""), updated=fm.get("updated", ""),
                    ))
    report.count = len(report.artifacts)


def action_scaffold(
    vault: Path,
    *,
    kind: str,
    slug: str | None,
    title: str,
    prd_slug: str,
    owner: str | None,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.kind = kind

    if kind not in KIND_CONFIG:
        die(report, f"invalid --kind `{kind}` — allowed: {', '.join(VALID_KINDS)}", code=1)

    template_name, _, _, is_singleton = KIND_CONFIG[kind]

    if is_singleton and slug:
        die(report, f"--slug is forbidden for singleton kind `{kind}`", code=1)
    if not is_singleton:
        if not slug:
            die(report, f"--slug is required for collection kind `{kind}`", code=1)
        if not SLUG_RE.match(slug):
            die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)

    effective_slug = slug or kind
    report.slug = effective_slug

    template = vault / DESIGN_DIR / TEMPLATES_DIR / template_name
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target = target_path(vault, kind, slug)
    report.artifact_path = rel(vault, target)

    if target.exists() and not force:
        die(report, f"{kind} already exists: {report.artifact_path} (use --force to overwrite)", code=1)

    marker = load_marker(vault)
    resolved_owner = owner or marker.get("owner") or "_tbd_"
    today = _dt.date.today().isoformat()
    project_name = marker.get("project_name") or title

    content = template.read_text(encoding="utf-8")
    for placeholder, value in {
        "{{TITLE}}": title or project_name,
        "{{SLUG}}": effective_slug,
        "{{OWNER}}": resolved_owner,
        "{{DATE}}": today,
        "{{PROJECT_NAME}}": project_name,
        "{{PRD_SLUG}}": prd_slug,
    }.items():
        content = content.replace(placeholder, value)

    report.was_new = not target.exists()
    if dry_run:
        report.status = "dry-run"
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def action_transition(
    vault: Path,
    *,
    kind: str,
    slug: str | None,
    to: str,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "transition"
    report.kind = kind

    if kind not in KIND_CONFIG:
        die(report, f"invalid --kind `{kind}` — allowed: {', '.join(VALID_KINDS)}", code=1)
    if to not in VALID_STATUSES:
        die(report, f"invalid --to `{to}` — allowed: {', '.join(VALID_STATUSES)}", code=1)

    _, _, _, is_singleton = KIND_CONFIG[kind]
    if is_singleton and slug:
        die(report, f"--slug is forbidden for singleton kind `{kind}`", code=1)
    if not is_singleton and not slug:
        die(report, f"--slug is required for collection kind `{kind}`", code=1)

    effective_slug = slug or kind
    report.slug = effective_slug

    target = target_path(vault, kind, slug)
    report.artifact_path = rel(vault, target)
    if not target.exists():
        die(report, f"{kind} not found: {report.artifact_path}", code=1)

    content = target.read_text(encoding="utf-8")
    fm = read_frontmatter(target)
    current = fm.get("status", "")
    report.previous_status = current
    report.new_status = to

    if current == to:
        return  # idempotent

    if dry_run:
        report.status = "dry-run"
        return

    today = _dt.date.today().isoformat()
    content = STATUS_LINE.sub(f"status: {to}", content, count=1)
    content = UPDATED_LINE.sub(f"updated: {today}", content, count=1)
    target.write_text(content, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Manage UX research artifacts in the SDLC vault.")
    p.add_argument("--vault-root", required=True)
    p.add_argument("--action", choices=["list", "scaffold", "transition"], required=True)
    p.add_argument("--kind", choices=list(VALID_KINDS))
    p.add_argument("--slug")
    p.add_argument("--title", default="")
    p.add_argument("--prd-slug", default="")
    p.add_argument("--owner")
    p.add_argument("--to", choices=list(VALID_STATUSES))
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    if args.action == "list":
        action_list(vault, kind=args.kind, report=report)
    elif args.action == "scaffold":
        if not args.kind:
            die(report, "--kind is required for scaffold", code=1)
        if not args.title:
            die(report, "--title is required for scaffold", code=1)
        action_scaffold(
            vault, kind=args.kind, slug=args.slug, title=args.title,
            prd_slug=args.prd_slug or "", owner=args.owner,
            force=args.force, dry_run=args.dry_run, report=report,
        )
    elif args.action == "transition":
        if not args.kind:
            die(report, "--kind is required for transition", code=1)
        if not args.to:
            die(report, "--to is required for transition", code=1)
        action_transition(
            vault, kind=args.kind, slug=args.slug, to=args.to,
            dry_run=args.dry_run, report=report,
        )

    print(json.dumps(report.as_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()
