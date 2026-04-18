#!/usr/bin/env python3
"""Manage the three canonical steering documents inside `00-steering/`.

Never touches `CLAUDE.md` — that file is sovereign, user-owned. The LLM is
responsible for interviewing the user and editing doc content via Edit/Write;
this script only handles deterministic file operations so it stays predictable.

Actions:
    status              Report presence + status of product.md, tech.md, standards.md.
    scaffold --doc X    Copy `00-steering/_templates/X.md.tpl` → `00-steering/X.md`,
                        applying placeholders from `.sdlc-kit/marker.json`. Refuses
                        to overwrite unless `--force`.
    promote --doc X     Flip `status: draft` → `status: active` in the frontmatter
                        and refresh `updated`. No-op if already active.

Emits a single JSON object on stdout. Exit codes: 0 ok/dry-run, 1 user error, 2 fatal.
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

from core.regexes import FRONTMATTER_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402
from core.frontmatter import read_frontmatter  # noqa: E402


STEERING_DOCS: tuple[str, ...] = ("product", "tech", "standards")
STEERING_DIR = "00-steering"
TEMPLATES_DIR = "_templates"
MARKER_REL = ".sdlc-kit/marker.json"


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class DocState:
    name: str
    exists: bool
    path: str
    status: str = ""
    updated: str = ""
    title: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    doc: str = ""
    doc_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    docs: list[DocState] = field(default_factory=list)
    next_suggested: str = ""
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d: dict = {
            "status": self.status,
            "action": self.action,
            "vault_root": self.vault_root,
            "errors": self.errors,
        }
        if self.action == "status":
            d["docs"] = [vars(x) for x in self.docs]
            d["next_suggested"] = self.next_suggested
        elif self.action == "scaffold":
            d["doc"] = self.doc
            d["doc_path"] = self.doc_path
            d["was_new"] = self.was_new
        elif self.action == "promote":
            d["doc"] = self.doc
            d["doc_path"] = self.doc_path
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


# that usually follows the closing frontmatter fence.


def read_frontmatter(path: Path) -> dict:
    """Minimal frontmatter parser — line-oriented, no YAML dependency.

    Returns a flat dict of top-level scalar key/value pairs. Anything nested or
    multi-line YAML is skipped (good enough for our needs — we only read
    status, updated, title)."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).split("\n"):
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        fm[key] = value
    return fm


# ---------------------------------------------------------------------------
# action: status
# ---------------------------------------------------------------------------

def action_status(vault: Path, report: Report) -> None:
    report.action = "status"
    for name in STEERING_DOCS:
        doc_path = vault / STEERING_DIR / f"{name}.md"
        fm = read_frontmatter(doc_path)
        report.docs.append(DocState(
            name=name,
            exists=doc_path.exists(),
            path=str(doc_path.relative_to(vault)).replace("\\", "/"),
            status=fm.get("status", ""),
            updated=fm.get("updated", ""),
            title=fm.get("title", ""),
        ))
    # Suggest the next doc to work on (first missing, else first still in draft)
    for d in report.docs:
        if not d.exists:
            report.next_suggested = d.name
            break
    else:
        for d in report.docs:
            if d.status == "draft":
                report.next_suggested = d.name
                break


# ---------------------------------------------------------------------------
# action: scaffold
# ---------------------------------------------------------------------------

def build_replacements(vault: Path, today: str) -> dict[str, str]:
    marker = load_marker(vault)
    project_name = marker.get("project_name") or "Meu Projeto"
    owner = marker.get("owner") or "_a definir_"
    repo_url = marker.get("repo_url") or ""
    stack_default = "_a definir — registre via ADR ou edite esta seção_"
    stack_details_default = (
        "_Stack ainda não definida. Preencha a tabela abaixo e registre cada "
        "decisão de tecnologia com `/sdlc-kit:adr new`._"
    )
    return {
        "{{PROJECT_NAME}}": project_name,
        "{{OWNER}}": owner,
        "{{STACK}}": stack_default,
        "{{STACK_DETAILS}}": stack_details_default,
        "{{REPO_URL}}": repo_url or "_sem remote configurado_",
        "{{DATE}}": today,
        "{{SYNC_TS}}": today,
        "{{TITLE}}": project_name,
        "{{SLUG}}": "",
    }


def apply_placeholders(text: str, replacements: dict[str, str]) -> str:
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def action_scaffold(
    vault: Path,
    doc: str,
    *,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.doc = doc

    template = vault / STEERING_DIR / TEMPLATES_DIR / f"{doc}.md.tpl"
    if not template.exists():
        die(report, f"template not found: {template.relative_to(vault)}", code=2)

    target = vault / STEERING_DIR / f"{doc}.md"
    report.doc_path = str(target.relative_to(vault)).replace("\\", "/")

    if target.exists() and not force:
        die(
            report,
            f"target already exists: {report.doc_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    replacements = build_replacements(vault, today)
    content = apply_placeholders(template.read_text(encoding="utf-8"), replacements)

    report.was_new = not target.exists()
    if dry_run:
        report.status = "dry-run"
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# action: promote
# ---------------------------------------------------------------------------


def action_promote(
    vault: Path,
    doc: str,
    *,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "promote"
    report.doc = doc

    target = vault / STEERING_DIR / f"{doc}.md"
    report.doc_path = str(target.relative_to(vault)).replace("\\", "/")

    if not target.exists():
        die(report, f"doc not found: {report.doc_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.doc_path}", code=1)

    fm_text = m.group(1)
    body = text[m.end():]

    status_match = STATUS_LINE.search(fm_text)
    current_status = status_match.group(2) if status_match else ""
    report.previous_status = current_status

    if current_status == "active":
        report.new_status = "active"
        report.status = "ok"
        return

    new_fm = STATUS_LINE.sub(r"\1active", fm_text, count=1) if status_match else fm_text + "\nstatus: active"
    today = _dt.date.today().isoformat()
    if UPDATED_LINE.search(new_fm):
        new_fm = UPDATED_LINE.sub(rf"\g<1>{today}", new_fm, count=1)
    else:
        new_fm = new_fm + f"\nupdated: {today}"

    new_text = f"---\n{new_fm}\n---\n{body}"
    report.new_status = "active"

    if dry_run:
        report.status = "dry-run"
        return
    target.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit steering document manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["status", "scaffold", "promote"],
        help="status: report doc state | scaffold: materialize from template | promote: draft→active",
    )
    p.add_argument(
        "--doc",
        choices=list(STEERING_DOCS),
        help="which steering doc (required for scaffold/promote)",
    )
    p.add_argument("--force", action="store_true", help="overwrite existing target (scaffold only)")
    p.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    if args.action in ("scaffold", "promote") and not args.doc:
        die(report, f"--doc is required for action `{args.action}`", code=1)

    try:
        if args.action == "status":
            action_status(vault, report)
        elif args.action == "scaffold":
            action_scaffold(vault, args.doc, force=args.force, dry_run=args.dry_run, report=report)
        elif args.action == "promote":
            action_promote(vault, args.doc, dry_run=args.dry_run, report=report)
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
