#!/usr/bin/env python3
"""Manage worktree and branch records under `05-development/`.

Two kinds are supported, both **collections** (one file per slug):

    Kind        Type slug (frontmatter)   Path                                   Template
    ---------   -----------------------   ------------------------------------   ---------------------------
    worktree    worktree                  05-development/worktrees/<slug>.md     _templates/worktree.md.tpl
    branch      branch                    05-development/branches/<slug>.md      _templates/branch.md.tpl

Lifecycles differ per kind:

    worktree :  active  →  merged | abandoned    (merged/abandoned are terminal)
    branch   :  <no formal status enum — branches track ci_status/pr, not lifecycle>

Semantic split:
    * A **worktree** is a physical filesystem directory created via
      `git worktree add`. It exists until the branch is merged or abandoned.
      Tracks: `branch`, `base`, `path`, `pr`, `agent_active`.
    * A **branch** is the git branch concept. Appears in the backlog as a
      record regardless of whether a worktree was materialized. Tracks:
      `branch_type`, `base`, `pr`, `ci_status`.

Actions:
    list [--kind K]
        Enumerate development records with kind, slug, title, status, owner,
        updated. Optional `--kind` narrows the result.
    scaffold --kind K --slug S --title T [--owner O] [--force]
        Copy the matching template into the right target. `--slug` and
        `--title` are required for both kinds. Refuses to overwrite unless
        `--force`.
    transition --kind worktree --slug S --to {active|merged|abandoned}
        Flip `status:` and refresh `updated`. Idempotent when already at the
        target status. **Only `worktree` supports transition** — `branch` has
        no formal status enum; calling transition on a branch is refused.

The LLM drives any content interview (branch name, base, PR link, CI gate,
closure checklist) via Edit/Write. This script only handles deterministic
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


DEV_DIR = "05-development"
TEMPLATES_DIR = "_templates"
MARKER_REL = ".sdlc-kit/marker.json"

# Only `worktree` has a formal lifecycle enum.
VALID_WORKTREE_STATUSES: tuple[str, ...] = ("active", "merged", "abandoned")


# ---------------------------------------------------------------------------
# kind registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KindSpec:
    kind: str
    folder: str           # relative to 05-development
    template: str         # filename under 05-development/_templates
    supports_transition: bool


_KINDS: dict[str, KindSpec] = {
    "worktree": KindSpec("worktree", "worktrees", "worktree.md.tpl", True),
    "branch":   KindSpec("branch",   "branches",  "branch.md.tpl",   False),
}

VALID_KINDS: tuple[str, ...] = tuple(_KINDS.keys())


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

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


def artifact_path(vault: Path, spec: KindSpec, slug: str) -> Path:
    return vault / DEV_DIR / spec.folder / f"{slug}.md"


def template_path(vault: Path, spec: KindSpec) -> Path:
    return vault / DEV_DIR / TEMPLATES_DIR / spec.template


def validate_kind_slug(report: Report, kind: str, slug: str | None) -> tuple[KindSpec, str]:
    spec = _KINDS.get(kind)
    if spec is None:
        die(report, f"invalid kind `{kind}` — allowed: {', '.join(VALID_KINDS)}", code=1)
    if not slug:
        die(report, f"kind `{kind}` requires --slug", code=1)
    if not SLUG_RE.match(slug):
        die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)
    return spec, slug


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def _list_collection(vault: Path, spec: KindSpec, report: Report) -> None:
    folder = vault / DEV_DIR / spec.folder
    if not folder.exists():
        return
    for path in sorted(p for p in folder.glob("*.md") if not p.name.startswith("_")):
        fm = read_frontmatter(path)
        report.artifacts.append(ArtifactState(
            kind=spec.kind,
            slug=path.stem,
            path=rel(vault, path),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            owner=fm.get("owner", ""),
            updated=fm.get("updated", ""),
        ))


def action_list(vault: Path, kind_filter: str | None, report: Report) -> None:
    report.action = "list"
    kinds = [kind_filter] if kind_filter else list(VALID_KINDS)
    for k in kinds:
        spec = _KINDS.get(k)
        if spec is None:
            die(report, f"invalid kind `{k}` — allowed: {', '.join(VALID_KINDS)}", code=1)
        _list_collection(vault, spec, report)
    report.count = len(report.artifacts)


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
    slug: str | None,
    title: str,
    owner: str | None,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.kind = kind
    spec, effective_slug = validate_kind_slug(report, kind, slug)
    report.slug = effective_slug

    template = template_path(vault, spec)
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target = artifact_path(vault, spec, effective_slug)
    report.artifact_path = rel(vault, target)

    if target.exists() and not force:
        die(
            report,
            f"{kind} already exists: {report.artifact_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    replacements = build_replacements(
        vault, title=title, slug=effective_slug, owner=owner, today=today
    )
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
    slug: str | None,
    target_status: str,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "transition"
    report.kind = kind
    spec, effective_slug = validate_kind_slug(report, kind, slug)
    report.slug = effective_slug

    if not spec.supports_transition:
        die(
            report,
            (
                f"kind `{kind}` has no formal status enum — transition is not "
                f"supported. Branches track `ci_status` and `pr`, not a "
                f"lifecycle; edit the body directly. Transition is only "
                f"available for kind `worktree`."
            ),
            code=1,
        )

    if target_status not in VALID_WORKTREE_STATUSES:
        die(
            report,
            (
                f"invalid status `{target_status}` for kind `{kind}` — "
                f"allowed: {', '.join(VALID_WORKTREE_STATUSES)}"
            ),
            code=1,
        )

    target = artifact_path(vault, spec, effective_slug)
    report.artifact_path = rel(vault, target)

    if not target.exists():
        die(report, f"{kind} not found: {report.artifact_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.artifact_path}", code=1)

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
    p = argparse.ArgumentParser(description="SDLC Kit worktree/branch manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate records | scaffold: materialize from template | transition: change status (worktree only)",
    )
    p.add_argument(
        "--kind",
        choices=list(VALID_KINDS),
        help="record kind (required for scaffold/transition; optional filter for list)",
    )
    p.add_argument("--slug", help="record slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="record owner (falls back to marker.json owner)")
    p.add_argument(
        "--to",
        dest="to_status",
        choices=list(VALID_WORKTREE_STATUSES),
        help="target status (required for transition; worktree only)",
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
        if not args.kind:
            die(report, "--kind is required for action `scaffold`", code=1)
        if not args.slug or not args.title:
            die(report, f"--slug and --title are required for scaffold of kind `{args.kind}`", code=1)
    if args.action == "transition":
        if not args.kind or not args.to_status:
            die(report, "--kind and --to are required for action `transition`", code=1)
        if not args.slug:
            die(report, f"--slug is required for transition of kind `{args.kind}`", code=1)

    try:
        if args.action == "list":
            action_list(vault, args.kind, report)
        elif args.action == "scaffold":
            action_scaffold(
                vault,
                kind=args.kind,
                slug=args.slug,
                title=args.title or "",
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
