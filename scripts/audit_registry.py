#!/usr/bin/env python3
"""Audit template ↔ registry integrity.

Scans every `*.md.tpl` under `assets/vault-tree/**/_templates/`, extracts the
`type:` field from its frontmatter, and checks:

  1. Every emitted `type` exists in `REQUIRED_FIELDS_BY_TYPE` (`sync.py`).
  2. Every registry entry in `REQUIRED_FIELDS_BY_TYPE` is either:
     a. emitted by at least one template, OR
     b. in the allowlist of types generated programmatically by the librarian
        (e.g., `moc`, `index`, `note` — virtual/fallback types).

Emits a single JSON object on stdout. Exit codes:
  0 — registry is coherent (no drift).
  1 — drift detected.
  2 — internal failure (registry not found, malformed templates).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_GLOB = "assets/vault-tree/**/_templates/**/*.md.tpl"
SYNC_SCRIPT = PLUGIN_ROOT / "skills" / "sdlc-sync" / "scripts" / "sync.py"

# Types that exist in the registry even though no template emits them, because
# they're generated programmatically by the librarian itself.
VIRTUAL_TYPES = {"moc", "index", "note"}

_TYPE_LINE_RE = re.compile(r"^type:\s*(.+)\s*$", re.MULTILINE)


def extract_template_type(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = _TYPE_LINE_RE.search(text)
    if not m:
        return None
    val = m.group(1).strip()
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val


def load_registry() -> tuple[set[str], set[str]]:
    """Parse REQUIRED_FIELDS_BY_TYPE and VALID_STATUS_BY_TYPE keys from sync.py."""
    src = SYNC_SCRIPT.read_text(encoding="utf-8")
    required_types = set(
        re.findall(r'^\s*"([a-z0-9][a-z0-9-]*)":\s*\{[^}]*"type"[^}]*\}', src, re.MULTILINE)
    )
    status_types = set(
        re.findall(r'^\s*"([a-z0-9][a-z0-9-]*)":\s*\{"(?:[^"]+"(?:,\s*)?)+\},?\s*$', src, re.MULTILINE)
    )
    return required_types, status_types


def main() -> int:
    report: dict = {
        "status": "ok",
        "template_types": [],
        "registry_types": [],
        "missing_in_registry": [],
        "orphans_in_registry": [],
        "errors": [],
    }

    tpls = sorted(PLUGIN_ROOT.glob(TEMPLATES_GLOB))
    template_types: set[str] = set()
    for tpl in tpls:
        t = extract_template_type(tpl)
        if t:
            template_types.add(t)

    try:
        required_types, _status_types = load_registry()
    except Exception as exc:
        report["status"] = "error"
        report["errors"].append(f"could not load registry from sync.py: {exc}")
        print(json.dumps(report))
        return 2

    missing = sorted(template_types - required_types)
    orphans = sorted(required_types - template_types - VIRTUAL_TYPES)

    report["template_types"] = sorted(template_types)
    report["registry_types"] = sorted(required_types)
    report["missing_in_registry"] = missing
    report["orphans_in_registry"] = orphans

    if missing or orphans:
        report["status"] = "drift"
        print(json.dumps(report, indent=2))
        return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
