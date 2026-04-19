#!/usr/bin/env python3
"""Manage Architecture Decision Records (ADRs) under `02-architecture/adr/`.

ADRs follow MADR-ish structure: one decision per file, numbered monotonically.
Filenames are `ADR-NNNN-<slug>.md` (4-digit zero-padded).

Actions:
    list                      Enumerate every ADR with number, status, title.
    new --title T [--slug S] [--owner O]
                              Scaffold the next ADR from
                              `02-architecture/_templates/adr.md.tpl`. Number
                              is chosen automatically (max existing + 1).
                              Refuses to reuse a number.
    transition --id N --to {proposed|accepted|rejected|superseded|deprecated}
                              Flip `status:` and refresh `updated`. Idempotent
                              when already at the target status.

The LLM drives the content interview (context, decision, alternatives,
consequences) via Edit/Write. This script only handles deterministic file ops.

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

from core.frontmatter import read_frontmatter  # noqa: E402
from core.regexes import FRONTMATTER_RE, SLUG_RE, STATUS_LINE, UPDATED_LINE  # noqa: E402

ARCH_DIR = "02-architecture"
ADR_DIR = "adr"
TEMPLATES_DIR = "_templates"
TEMPLATE_NAME = "adr.md.tpl"
MARKER_REL = ".sdlc-kit/marker.json"

VALID_STATUSES: tuple[str, ...] = (
    "proposed", "accepted", "rejected", "superseded", "deprecated",
)

# 4-digit zero-padded number. Matches both ADR-0001 and the template's
# ADR-NNNN placeholder (via literal substitution).
_ADR_FILENAME_RE = re.compile(r"^ADR-(\d{4})-([a-z0-9][a-z0-9-]*)\.md$")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class AdrState:
    id: str          # e.g. "ADR-0003"
    number: int
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
    adr_id: str = ""
    number: int = 0
    slug: str = ""
    adr_path: str = ""
    was_new: bool = False
    previous_status: str = ""
    new_status: str = ""
    adrs: list[AdrState] = field(default_factory=list)
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
            d["adrs"] = [vars(x) for x in self.adrs]
            d["count"] = self.count
        elif self.action == "new":
            d["adr_id"] = self.adr_id
            d["number"] = self.number
            d["slug"] = self.slug
            d["adr_path"] = self.adr_path
            d["was_new"] = self.was_new
        elif self.action == "transition":
            d["adr_id"] = self.adr_id
            d["adr_path"] = self.adr_path
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


def slugify(value: str) -> str:
    """Lowercase ASCII slug. Doesn't transliterate accents — use --slug if you
    need something cleaner than the naive strip."""
    s = value.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


# Bound whitespace matching to inline chars so the blank line after the
# frontmatter fence is preserved across transitions.


def scan_adrs(vault: Path) -> list[tuple[int, str, Path]]:
    """Return [(number, slug, path)] sorted ascending by number."""
    adr_dir = vault / ARCH_DIR / ADR_DIR
    if not adr_dir.exists():
        return []
    results: list[tuple[int, str, Path]] = []
    for path in adr_dir.glob("ADR-*.md"):
        m = _ADR_FILENAME_RE.match(path.name)
        if not m:
            # Ignore files that don't match the canonical pattern. The librarian
            # (sync.py) will flag them as anomalies separately.
            continue
        results.append((int(m.group(1)), m.group(2), path))
    results.sort(key=lambda t: t[0])
    return results


def resolve_id(raw: str) -> int:
    """Accept `3`, `0003`, `ADR-3`, or `ADR-0003` and return the int."""
    s = raw.strip().upper()
    if s.startswith("ADR-"):
        s = s[4:]
    try:
        return int(s)
    except ValueError as exc:
        raise ValueError(f"invalid ADR id `{raw}` (expected number or ADR-NNNN)") from exc


def find_adr_by_number(vault: Path, number: int) -> Path | None:
    for n, _slug, path in scan_adrs(vault):
        if n == number:
            return path
    return None


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, report: Report) -> None:
    report.action = "list"
    for number, slug, path in scan_adrs(vault):
        fm = read_frontmatter(path)
        report.adrs.append(AdrState(
            id=f"ADR-{number:04d}",
            number=number,
            slug=slug,
            path=str(path.relative_to(vault)).replace("\\", "/"),
            title=fm.get("title", ""),
            status=fm.get("status", ""),
            owner=fm.get("owner", ""),
            updated=fm.get("updated", ""),
        ))
    report.count = len(report.adrs)


# ---------------------------------------------------------------------------
# action: new
# ---------------------------------------------------------------------------

def build_replacements(
    vault: Path,
    *,
    title: str,
    slug: str,
    adr_id: str,
    owner: str | None,
    today: str,
) -> dict[str, str]:
    marker = load_marker(vault)
    resolved_owner = owner or marker.get("owner") or "_unassigned_"
    return {
        "{{TITLE}}": title,
        "{{SLUG}}": slug,
        "{{OWNER}}": resolved_owner,
        "{{DATE}}": today,
        # Template has `id: "ADR-NNNN"` and heading `# ADR-NNNN — {{TITLE}}`.
        # The literal `ADR-NNNN` is substituted with the resolved id so we
        # don't need a separate placeholder token.
        "ADR-NNNN": adr_id,
    }


def apply_placeholders(text: str, replacements: dict[str, str]) -> str:
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def action_new(
    vault: Path,
    *,
    title: str,
    slug: str | None,
    owner: str | None,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "new"

    resolved_slug = slug if slug else slugify(title)
    if not SLUG_RE.match(resolved_slug):
        die(report, f"invalid slug `{resolved_slug}`: must match [a-z0-9][a-z0-9-]*", code=1)
    report.slug = resolved_slug

    template = vault / ARCH_DIR / TEMPLATES_DIR / TEMPLATE_NAME
    if not template.exists():
        die(report, f"template not found: {template.relative_to(vault)}", code=2)

    existing = scan_adrs(vault)
    next_number = (existing[-1][0] + 1) if existing else 1
    adr_id = f"ADR-{next_number:04d}"
    filename = f"{adr_id}-{resolved_slug}.md"
    target = vault / ARCH_DIR / ADR_DIR / filename

    report.number = next_number
    report.adr_id = adr_id
    report.adr_path = str(target.relative_to(vault)).replace("\\", "/")

    if target.exists():
        # Shouldn't happen because next_number is chosen from max+1, but guard
        # anyway — helps catch a concurrent writer or a manually-placed file.
        die(report, f"target already exists: {report.adr_path}", code=1)

    today = _dt.date.today().isoformat()
    replacements = build_replacements(
        vault, title=title, slug=resolved_slug, adr_id=adr_id, owner=owner, today=today,
    )
    content = apply_placeholders(template.read_text(encoding="utf-8"), replacements)

    report.was_new = True
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
    raw_id: str,
    target_status: str,
    dry_run: bool,
    report: Report,
) -> None:
    report.action = "transition"

    if target_status not in VALID_STATUSES:
        die(
            report,
            f"invalid status `{target_status}` — allowed: {', '.join(VALID_STATUSES)}",
            code=1,
        )

    try:
        number = resolve_id(raw_id)
    except ValueError as exc:
        die(report, str(exc), code=1)

    report.adr_id = f"ADR-{number:04d}"
    target = find_adr_by_number(vault, number)
    if not target:
        die(report, f"ADR not found: {report.adr_id} (run `new` first)", code=1)

    report.adr_path = str(target.relative_to(vault)).replace("\\", "/")

    text = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        die(report, f"no frontmatter found in {report.adr_path}", code=1)

    fm_text = m.group(1)
    body = text[m.end():]

    status_match = STATUS_LINE.search(fm_text)
    current_status = status_match.group(2) if status_match else ""
    report.previous_status = current_status
    report.new_status = target_status

    if current_status == target_status:
        return

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
    p = argparse.ArgumentParser(description="SDLC Kit ADR manager.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "new", "transition"],
        help="list: enumerate ADRs | new: scaffold next-numbered ADR | transition: change status",
    )
    p.add_argument("--title", help="ADR title (required for new)")
    p.add_argument("--slug", help="override the slug (defaults to slugified title)")
    p.add_argument("--owner", help="owner (falls back to marker.json owner)")
    p.add_argument(
        "--id",
        dest="adr_id",
        help="ADR id for transition (accepts `3`, `0003`, or `ADR-0003`)",
    )
    p.add_argument(
        "--to",
        dest="to_status",
        choices=list(VALID_STATUSES),
        help="target status (required for transition)",
    )
    p.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    if args.action == "new":
        if not args.title:
            die(report, "--title is required for action `new`", code=1)
    if args.action == "transition":
        if not args.adr_id or not args.to_status:
            die(report, "--id and --to are required for action `transition`", code=1)

    try:
        if args.action == "list":
            action_list(vault, report)
        elif args.action == "new":
            action_new(
                vault,
                title=args.title,
                slug=args.slug,
                owner=args.owner,
                dry_run=args.dry_run,
                report=report,
            )
        elif args.action == "transition":
            action_transition(
                vault,
                raw_id=args.adr_id,
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
