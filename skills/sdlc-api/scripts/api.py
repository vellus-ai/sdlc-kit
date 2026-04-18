#!/usr/bin/env python3
"""Manage API-design artifacts under `02-architecture/api/`.

Four interface styles are supported. Each kind is a **collection** — one
file per slug — and lives in its own subfolder under `02-architecture/api/`:

    Kind       Path                                         Template
    --------   ------------------------------------------   ---------------------------
    rest       02-architecture/api/rest/<slug>.md           _templates/api/rest.md.tpl
    async      02-architecture/api/async/<slug>.md          _templates/api/async.md.tpl
    grpc       02-architecture/api/grpc/<slug>.md           _templates/api/grpc.md.tpl
    webhook    02-architecture/api/webhook/<slug>.md        _templates/api/webhook.md.tpl

Lifecycle (all kinds):

    draft  →  approved  →  deprecated

`draft` is the scaffolded state; `approved` means the API Designer (platform
side) and the Senior Software Engineer (consumer side) both signed off and
producers/consumers may rely on the contract; `deprecated` is kept for
consumer coordination and must not be cited by new integrations.

Actions:
    list [--kind K]
        Enumerate API records with kind, slug, title, status, owner, updated.
        Optional `--kind` narrows the result.
    scaffold --kind K --slug S --title T [--owner O] [--force]
        Copy the matching template into the target. `--slug` is always
        required (all kinds are collections). The script refuses to overwrite
        unless `--force` is passed.
    transition --kind K --slug S --to {draft|approved|deprecated}
        Flip `status:` and refresh `updated`. Idempotent when already at the
        target status.

The LLM drives the content interview (endpoints, schemas, error model, auth,
rate limits, versioning, HMAC signatures, proto contracts, etc.) via
Edit/Write. This script only handles deterministic file operations.

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


ARCH_DIR = "02-architecture"
API_DIR = "api"
TEMPLATES_DIR = "_templates"
MARKER_REL = ".sdlc-kit/marker.json"

VALID_STATUSES: tuple[str, ...] = ("draft", "approved", "deprecated")


# ---------------------------------------------------------------------------
# kind registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KindSpec:
    kind: str
    folder: str     # relative to 02-architecture/api/ — one subfolder per kind
    template: str   # filename under 02-architecture/_templates/api/


_KINDS: dict[str, KindSpec] = {
    "rest":    KindSpec("rest",    "rest",    "rest.md.tpl"),
    "async":   KindSpec("async",   "async",   "async.md.tpl"),
    "grpc":    KindSpec("grpc",    "grpc",    "grpc.md.tpl"),
    "webhook": KindSpec("webhook", "webhook", "webhook.md.tpl"),
}

VALID_KINDS: tuple[str, ...] = tuple(_KINDS.keys())


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class ApiState:
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
    artifacts: list[ApiState] = field(default_factory=list)
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
    return vault / ARCH_DIR / API_DIR / spec.folder / f"{slug}.md"


def template_path(vault: Path, spec: KindSpec) -> Path:
    # Templates live in 02-architecture/_templates/api/<template>
    return vault / ARCH_DIR / TEMPLATES_DIR / API_DIR / spec.template


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
    folder = vault / ARCH_DIR / API_DIR / spec.folder
    if not folder.exists():
        return
    for path in sorted(p for p in folder.glob("*.md") if not p.name.startswith("_")):
        fm = read_frontmatter(path)
        report.artifacts.append(ApiState(
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
            f"{kind} API already exists: {report.artifact_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    effective_title = title or effective_slug
    replacements = build_replacements(
        vault, title=effective_title, slug=effective_slug, owner=owner, today=today
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

    if target_status not in VALID_STATUSES:
        die(
            report,
            f"invalid status `{target_status}` — allowed: {', '.join(VALID_STATUSES)}",
            code=1,
        )

    target = artifact_path(vault, spec, effective_slug)
    report.artifact_path = rel(vault, target)

    if not target.exists():
        die(report, f"{kind} API not found: {report.artifact_path} (run scaffold first)", code=1)

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
    p = argparse.ArgumentParser(description="SDLC Kit API-design artifact manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate APIs | scaffold: materialize from template | transition: change status",
    )
    p.add_argument(
        "--kind",
        choices=list(VALID_KINDS),
        help="API style (required for scaffold/transition; optional filter for list)",
    )
    p.add_argument("--slug", help="API slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="API owner (falls back to marker.json owner)")
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
        if not args.kind:
            die(report, "--kind is required for action `scaffold`", code=1)
        if not args.title:
            die(report, f"--title is required for scaffold of kind `{args.kind}`", code=1)
    if args.action == "transition":
        if not args.kind or not args.to_status:
            die(report, "--kind and --to are required for action `transition`", code=1)

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
