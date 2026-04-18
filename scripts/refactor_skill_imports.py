#!/usr/bin/env python3
"""One-shot refactor: replace local regex/helper duplicates with imports from
`core.regexes` and `core.frontmatter` across the 18 skill scripts.

Runs in --dry-run by default; pass --apply to rewrite files on disk.

Strategy: literal string removal (more robust than regex fit) + rename via
word-boundary regex + conditional import injection based on post-removal usage.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

TARGET_SCRIPTS = [
    "sdlc-adr/scripts/adr.py",
    "sdlc-api/scripts/api.py",
    "sdlc-c4/scripts/c4.py",
    "sdlc-design-system/scripts/design_system.py",
    "sdlc-domain/scripts/domain.py",
    "sdlc-epic/scripts/epic.py",
    "sdlc-impact/scripts/impact.py",
    "sdlc-incident/scripts/incident.py",
    "sdlc-milestone/scripts/milestone.py",
    "sdlc-prd/scripts/prd.py",
    "sdlc-retro/scripts/retro.py",
    "sdlc-review/scripts/review.py",
    "sdlc-spec/scripts/spec.py",
    "sdlc-steer/scripts/steer.py",
    "sdlc-task/scripts/task.py",
    "sdlc-trace/scripts/trace.py",
    "sdlc-trd/scripts/trd.py",
    "sdlc-worktree/scripts/worktree.py",
]

# Literal lines to delete (full line including trailing newline).
LITERAL_REMOVALS = [
    '# Bound whitespace to inline chars so we keep the blank line after the fence.\n',
    "# Bound whitespace matching to inline chars so we don't eat the blank line\n",
    "# after the closing fence (the `\\n` after `---` belongs to the body).\n",
    '_FRONTMATTER_RE = re.compile(r"^---[ \\t]*\\n(.*?)\\n---[ \\t]*\\n", re.DOTALL)\n',
    '_STATUS_LINE = re.compile(r"^(status:\\s*)(\\S+)\\s*$", re.MULTILINE)\n',
    '_UPDATED_LINE = re.compile(r"^(updated:\\s*)(\\S+)\\s*$", re.MULTILINE)\n',
    '_DECISION_LINE = re.compile(r\'^(decision:\\s*)"?([A-Za-z0-9-]+)"?\\s*$\', re.MULTILINE)\n',
    '_PR_LINE = re.compile(r\'^(pr:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_PR_URL_LINE = re.compile(r\'^(pr_url:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_AUTHOR_LINE = re.compile(r\'^(author:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_SEVERITY_LINE = re.compile(r\'^(severity:\\s*)"?([A-Za-z0-9]+)"?\\s*$\', re.MULTILINE)\n',
    '_DETECTED_LINE = re.compile(r\'^(detected_at:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_MITIGATED_LINE = re.compile(r\'^(mitigated_at:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_RESOLVED_LINE = re.compile(r\'^(resolved_at:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_SPRINT_LINE = re.compile(r\'^(sprint:\\s*)"?([^"\\n]*)"?\\s*$\', re.MULTILINE)\n',
    '_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")\n',
    '_WIKILINK_RE = re.compile(r"\\[\\[([^\\]|#]+)(?:#[^\\]|]+)?(?:\\|[^\\]]+)?\\]\\]")\n',
]

# Regex for multi-line function removals (read_frontmatter + _set_quoted_field).
READ_FRONTMATTER_FN = re.compile(
    r'def read_frontmatter\(path: Path\) -> dict:\n'
    r'(?:    .*\n)+?'
    r'    return fm\n',
)

SET_QUOTED_FIELD_FN = re.compile(
    r'def _set_quoted_field\([^)]*\) -> str:\n'
    r'(?:    .*\n)+?'
    r'    return fm_text \+ f[\'"]\\n\{key\}: "\{value\}"[\'"]\n',
)

# Multi-line set_quoted_field that may include a docstring / different return style.
SET_QUOTED_FIELD_FN_DOCSTRING = re.compile(
    r'def _set_quoted_field\([^)]*\) -> str:\n'
    r'    """[^"]*"""\n'
    r'    m = regex\.search\(fm_text\)\n'
    r'    if m:\n'
    r'        return regex\.sub\(rf\'\\g<1>"\{value\}"\', fm_text, count=1\)\n'
    r'    return fm_text \+ f\'\\n\{key\}: "\{value\}"\'\n',
)

# Rename local-ref usages.
RENAMES = [
    (re.compile(r"\b_FRONTMATTER_RE\b"), "FRONTMATTER_RE"),
    (re.compile(r"\b_SLUG_RE\b"), "SLUG_RE"),
    (re.compile(r"\b_STATUS_LINE\b"), "STATUS_LINE"),
    (re.compile(r"\b_UPDATED_LINE\b"), "UPDATED_LINE"),
    (re.compile(r"\b_WIKILINK_RE\b"), "WIKILINK_RE"),
    (re.compile(r"\b_set_quoted_field\b"), "set_quoted_field"),
]


def _needed_imports(text: str) -> tuple[set[str], set[str]]:
    regex_names = set()
    for name in ("FRONTMATTER_RE", "SLUG_RE", "STATUS_LINE", "UPDATED_LINE", "WIKILINK_RE"):
        if re.search(rf"\b{name}\b", text):
            regex_names.add(name)
    fm_names = set()
    if re.search(r"\bread_frontmatter\b", text):
        fm_names.add("read_frontmatter")
    if re.search(r"\bset_quoted_field\b", text):
        fm_names.add("set_quoted_field")
    return regex_names, fm_names


def refactor_file(path: Path, apply: bool) -> dict:
    original = path.read_text(encoding="utf-8")
    text = original

    # 1. Literal-string removals.
    for needle in LITERAL_REMOVALS:
        while needle in text:
            text = text.replace(needle, "", 1)

    # 2. Multi-line function removals.
    text = READ_FRONTMATTER_FN.sub("", text)
    text = SET_QUOTED_FIELD_FN.sub("", text)
    text = SET_QUOTED_FIELD_FN_DOCSTRING.sub("", text)

    # 3. Rename references.
    for pat, repl in RENAMES:
        text = pat.sub(repl, text)

    # 4. Figure out which imports are actually needed after cleanup.
    regex_names, fm_names = _needed_imports(text)

    import_lines: list[str] = []
    if regex_names:
        import_lines.append(
            f"from core.regexes import {', '.join(sorted(regex_names))}  # noqa: E402"
        )
    if fm_names:
        import_lines.append(
            f"from core.frontmatter import {', '.join(sorted(fm_names))}  # noqa: E402"
        )

    # 5. Inject the sys.path + from core imports block right after the last import.
    if import_lines and "from core.regexes" not in text and "from core.frontmatter" not in text:
        lines = text.split("\n")
        last_import_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i
        if last_import_idx >= 0:
            block = [
                "",
                "_PLUGIN_ROOT = Path(__file__).resolve().parents[3]",
                "if str(_PLUGIN_ROOT) not in sys.path:",
                "    sys.path.insert(0, str(_PLUGIN_ROOT))",
                "",
                *import_lines,
            ]
            lines[last_import_idx + 1:last_import_idx + 1] = block
            text = "\n".join(lines)

    # 6. Collapse 3+ blank lines to 2 (canonical between top-level).
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    report = {
        "path": str(path.relative_to(PLUGIN_ROOT)),
        "bytes_before": len(original),
        "bytes_after": len(text),
        "bytes_delta": len(text) - len(original),
        "regex_imports": sorted(regex_names),
        "fm_imports": sorted(fm_names),
    }

    if apply and text != original:
        path.write_text(text, encoding="utf-8")

    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="rewrite files (default: dry-run)")
    args = ap.parse_args()

    reports = []
    for rel in TARGET_SCRIPTS:
        path = SKILLS_ROOT / rel
        if not path.exists():
            print(f"SKIP (not found): {rel}")
            continue
        r = refactor_file(path, apply=args.apply)
        reports.append(r)
        delta_str = f"{r['bytes_delta']:+d}b"
        print(f"{'APPLY' if args.apply else 'DRY '} {r['path']}: {delta_str}  "
              f"regex={r['regex_imports']}  fm={r['fm_imports']}")

    total_delta = sum(r["bytes_delta"] for r in reports)
    print(f"\nTotal: {len(reports)} files, {total_delta:+d} bytes")


if __name__ == "__main__":
    main()
