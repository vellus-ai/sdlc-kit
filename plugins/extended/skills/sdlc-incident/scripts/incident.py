#!/usr/bin/env python3
"""Manage incident / post-mortem records under `07-retrospectives/incidents/`.

An incident captures a real production event — detection, mitigation timeline,
impact, root cause (when known) and the post-mortem lessons doc. One file per
incident, identified by slug (usually `inc-YYYY-MM-DD-<short-topic>`), because
the slug is the stable reference responders and stakeholders can recognize.

Files live at:

    07-retrospectives/incidents/<slug>.md

Lifecycle:

    open  →  mitigated  →  resolved  →  post-mortem

- `open`        — the incident is active. Timer started at `detected_at`.
- `mitigated`   — bleeding stopped, customers unblocked; root cause may still
                  be unknown. Fills `mitigated_at` if empty.
- `resolved`    — fix deployed, no customer impact, monitoring clean. Fills
                  `resolved_at` if empty.
- `post-mortem` — terminal. Lessons doc attached at
                  `07-retrospectives/incidents/<slug>-lessons.md`, action items
                  tracked. This state does NOT auto-fill timestamps — they
                  must already be set (enforced upstream by the LLM checklist).

Rewinding to `open` after the fact does NOT clear the timestamps — they are
historical and must remain auditable.

Severity enum: SEV1 | SEV2 | SEV3 | SEV4 (enforced by argparse).

Actions:
    list
        Enumerate every incident with slug, status, severity, title, owner,
        updated.
    scaffold --slug S --title T [--owner O] [--severity SEV1|SEV2|SEV3|SEV4]
             [--detected-at YYYY-MM-DD] [--force]
        Copy `07-retrospectives/_templates/incident.md.tpl` to
        `07-retrospectives/incidents/<slug>.md`, applying placeholders. Pre-
        fills `severity` (default SEV3) and `detected_at` (default today).
        Refuses to overwrite unless --force.
    transition --slug S --to {open|mitigated|resolved|post-mortem}
        Flip `status:`, refresh `updated`, and auto-fill matching timestamps
        (mitigated_at, resolved_at) when flipping into those states. Idempotent
        when already at the target status.

Companion doc: when the incident reaches `post-mortem`, the LLM is expected to
have authored `07-retrospectives/incidents/<slug>-lessons.md` separately via
Write. This script does NOT scaffold the lessons file.

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

from core.frontmatter import read_frontmatter, set_quoted_field  # noqa: E402
from core.regexes import FRONTMATTER_RE, SLUG_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402

RETRO_DIR = "07-retrospectives"
INCIDENTS_DIR = "incidents"
TEMPLATES_DIR = "_templates"
TEMPLATE_NAME = "incident.md.tpl"
MARKER_REL = ".sdlc-kit/marker.json"

VALID_STATUSES: tuple[str, ...] = ("open", "mitigated", "resolved", "post-mortem")
VALID_SEVERITIES: tuple[str, ...] = ("SEV1", "SEV2", "SEV3", "SEV4")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class IncidentState:
    slug: str
    path: str
    title: str = ""
    status: str = ""
    severity: str = ""
    owner: str = ""
    detected_at: str = ""
    mitigated_at: str = ""
    resolved_at: str = ""
    updated: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    slug: str = ""
    incident_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    timestamps_updated: list[str] = field(default_factory=list)
    incidents: list[IncidentState] = field(default_factory=list)
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
            d["incidents"] = [vars(x) for x in self.incidents]
            d["count"] = self.count
        elif self.action == "scaffold":
            d["slug"] = self.slug
            d["incident_path"] = self.incident_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["slug"] = self.slug
            d["incident_path"] = self.incident_path
            d["previous_status"] = self.previous_status
            d["new_status"] = self.new_status
            d["timestamps_updated"] = self.timestamps_updated
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


_SEVERITY_LINE = re.compile(r'^(severity:\s*)"?([A-Za-z0-9-]+)"?\s*$', re.MULTILINE)
_DETECTED_AT_LINE = re.compile(r'^(detected_at:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
_MITIGATED_AT_LINE = re.compile(r'^(mitigated_at:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
_RESOLVED_AT_LINE = re.compile(r'^(resolved_at:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)


def incidents_folder(vault: Path) -> Path:
    return vault / RETRO_DIR / INCIDENTS_DIR


def _field_is_empty(fm_text: str, regex: re.Pattern[str]) -> bool:
    """True when the field is absent OR present with an empty/blank value."""
    m = regex.search(fm_text)
    if not m:
        return True
    return not m.group(2).strip()


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, report: Report) -> None:
    report.action = "list"
    folder = incidents_folder(vault)
    if not folder.exists():
        return
    for path in sorted(p for p in folder.glob("*.md") if not p.name.startswith("_")):
        # Skip lessons companion docs — they are auxiliary artifacts, not
        # incidents. They share the incidents/ folder but have a distinct
        # naming convention (<slug>-lessons.md) and a different frontmatter
        # `type`. We filter by frontmatter type to be safe.
        fm = read_frontmatter(path)
        if fm.get("type") and fm.get("type") != "incident":
            continue
        report.incidents.append(IncidentState(
            slug=path.stem,
            path=rel(vault, path),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            severity=fm.get("severity", ""),
            owner=fm.get("owner", ""),
            detected_at=fm.get("detected_at", ""),
            mitigated_at=fm.get("mitigated_at", ""),
            resolved_at=fm.get("resolved_at", ""),
            updated=fm.get("updated", ""),
        ))
    report.count = len(report.incidents)


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
    severity: str,
    detected_at: str,
    force: bool,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "scaffold"
    report.slug = slug

    if not SLUG_RE.match(slug):
        die(report, f"invalid slug `{slug}`: must match [a-z0-9][a-z0-9-]*", code=1)

    if severity not in VALID_SEVERITIES:
        die(
            report,
            f"invalid severity `{severity}` — allowed: {', '.join(VALID_SEVERITIES)}",
            code=1,
        )

    template = vault / RETRO_DIR / TEMPLATES_DIR / TEMPLATE_NAME
    if not template.exists():
        die(report, f"template not found: {rel(vault, template)}", code=2)

    target = incidents_folder(vault) / f"{slug}.md"
    report.incident_path = rel(vault, target)

    if target.exists() and not force:
        die(
            report,
            f"incident already exists: {report.incident_path} (use --force to overwrite)",
            code=1,
        )

    today = _dt.date.today().isoformat()
    replacements = build_replacements(vault, title=title, slug=slug, owner=owner, today=today)
    content = apply_placeholders(template.read_text(encoding="utf-8"), replacements)

    # Inject scaffold-time metadata (severity override + detected_at pre-fill)
    # so the note carries actionable context from the first save — no need for
    # a manual edit pass to correct the SEV3 default.
    m = FRONTMATTER_RE.match(content)
    if m:
        fm_text = m.group(1)
        body = content[m.end():]
        fm_text = set_quoted_field(fm_text, _SEVERITY_LINE, "severity", severity)
        fm_text = set_quoted_field(fm_text, _DETECTED_AT_LINE, "detected_at", detected_at)
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

# Map target status → frontmatter field that should be auto-filled on entry.
# `open` and `post-mortem` intentionally have no side-effect:
#   - `open` is the initial state; rewinding to it should not destroy history.
#   - `post-mortem` is terminal; mitigated_at/resolved_at must already be set
#     upstream (the LLM pre-post-mortem checklist enforces this).
_TIMESTAMP_ON_ENTRY: dict[str, tuple[re.Pattern[str], str]] = {
    "mitigated": (_MITIGATED_AT_LINE, "mitigated_at"),
    "resolved":  (_RESOLVED_AT_LINE,  "resolved_at"),
}


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

    target = incidents_folder(vault) / f"{slug}.md"
    report.incident_path = rel(vault, target)

    if not target.exists():
        die(report, f"incident not found: {report.incident_path} (run scaffold first)", code=1)

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.incident_path}", code=1)

    fm_text = m.group(1)
    body = text[m.end():]

    status_match = STATUS_LINE.search(fm_text)
    current_status = status_match.group(2) if status_match else ""
    report.previous_status = current_status
    report.new_status = target_status

    if current_status == target_status:
        return  # idempotent — no status flip, no timestamp fill

    new_fm = (
        STATUS_LINE.sub(rf"\g<1>{target_status}", fm_text, count=1)
        if status_match
        else fm_text + f"\nstatus: {target_status}"
    )

    today = _dt.date.today().isoformat()

    # Auto-fill the matching timestamp on entering `mitigated` or `resolved`,
    # but only when the field is currently empty — we never overwrite a value
    # the user (or a previous transition) already recorded.
    side_effect = _TIMESTAMP_ON_ENTRY.get(target_status)
    if side_effect is not None:
        regex, key = side_effect
        if _field_is_empty(new_fm, regex):
            new_fm = set_quoted_field(new_fm, regex, key, today)
            report.timestamps_updated.append(key)

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
    p = argparse.ArgumentParser(description="SDLC Kit incident manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "scaffold", "transition"],
        help="list: enumerate incidents | scaffold: materialize from template | transition: change status",
    )
    p.add_argument("--slug", help="incident slug (required for scaffold/transition)")
    p.add_argument("--title", help="human-readable title (required for scaffold)")
    p.add_argument("--owner", help="incident owner / IC (falls back to marker.json owner)")
    p.add_argument(
        "--severity",
        choices=list(VALID_SEVERITIES),
        default="SEV3",
        help="incident severity (scaffold only, default SEV3)",
    )
    p.add_argument(
        "--detected-at",
        dest="detected_at",
        help="detection date in YYYY-MM-DD (scaffold only, default today)",
    )
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
            detected_at = args.detected_at or _dt.date.today().isoformat()
            action_scaffold(
                vault,
                slug=args.slug,
                title=args.title,
                owner=args.owner,
                severity=args.severity,
                detected_at=detected_at,
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
