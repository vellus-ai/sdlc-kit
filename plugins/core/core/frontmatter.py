"""Frontmatter helpers shared across skill scripts.

This module consolidates logic that was previously duplicated 3+ times across
`sdlc-review`, `sdlc-incident`, `sdlc-retro` and the test helper module. It
also provides the canonical round-trippable `render_frontmatter` so that
property-based tests can exercise parse ↔ render equivalence.

The implementation is stdlib-only by design (no pyyaml dependency). It is a
*best-effort* scalar parser: it handles `key: value` lines and quoted values,
ignores comments and blank lines, and silently drops anything it doesn't
understand. For richer YAML (lists, nested maps, block scalars), rely on
`core.parser.parse()` which imports pyyaml when available.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from core.regexes import FRONTMATTER_RE

__all__ = [
    "read_frontmatter",
    "parse_frontmatter_text",
    "set_quoted_field",
    "render_frontmatter",
]


def _parse_scalar_line(line: str) -> tuple[str, str] | None:
    """Parse a single `key: value` line into a (key, value) tuple or None."""
    if ":" not in line or line.lstrip().startswith("#"):
        return None
    key, _, value = line.partition(":")
    key = key.strip()
    value = value.strip()
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        value = value[1:-1]
    if not key:
        return None
    return key, value


def parse_frontmatter_text(text: str) -> tuple[dict[str, str], str]:
    """Split a string into (frontmatter_dict, body_text).

    Returns ({}, text) when no valid frontmatter fence is present.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        parsed = _parse_scalar_line(line)
        if parsed is not None:
            fm[parsed[0]] = parsed[1]
    body = text[m.end():]
    return fm, body


def read_frontmatter(path: Path) -> dict[str, str]:
    """Read a markdown file's frontmatter as a flat dict of scalars.

    Returns an empty dict if:
      * the file does not exist
      * the file has no frontmatter fence
      * the frontmatter is malformed

    Non-UTF-8 bytes in the file are replaced (lossy but safe).
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, _ = parse_frontmatter_text(text)
    return fm


def set_quoted_field(
    fm_text: str,
    regex: re.Pattern[str],
    key: str,
    value: str,
) -> str:
    """Set a frontmatter field to a quoted value idempotently.

    If `regex` finds the key in `fm_text`, replace its value. Otherwise
    append a new `key: "value"` line at the end of `fm_text`.

    The regex must capture two groups: group(1) is the `key: ` prefix (with
    colon + whitespace), group(2) is the previous value. See the matching
    regexes in `core.regexes` for examples.
    """
    m = regex.search(fm_text)
    if m:
        return regex.sub(rf'\g<1>"{value}"', fm_text, count=1)
    return fm_text + f'\n{key}: "{value}"'


def _needs_quoting(value: str) -> bool:
    """Return True if a scalar value should be rendered with double quotes.

    Values containing YAML-significant characters (colon, hash, brackets,
    braces, comma, ampersand, asterisk, bang, pipe, greater-than, percent,
    at-sign, backtick, double-quote) or leading/trailing whitespace need
    quoting so the scalar parser can read them back unambiguously.
    """
    if value == "":
        return False
    if value[0] in " \t" or value[-1] in " \t":
        return True
    for ch in (":", "#", "[", "]", "{", "}", ",", "&", "*", "!", "|", ">", "%", "@", "`", "\""):
        if ch in value:
            return True
    return False


def render_frontmatter(fm: Mapping[str, str]) -> str:
    """Render a mapping of scalars as a frontmatter block (inclusive of fences).

    Produces output in insertion order. Values are quoted when needed so that
    `parse_frontmatter_text(render_frontmatter(d))[0] == d` for any dict of
    unquoted scalar strings without embedded newlines.
    """
    lines = ["---"]
    for key, value in fm.items():
        sval = str(value)
        if _needs_quoting(sval):
            lines.append(f'{key}: "{sval}"')
        else:
            lines.append(f"{key}: {sval}")
    lines.append("---")
    return "\n".join(lines) + "\n"
