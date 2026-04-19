"""Canonical regex patterns shared across the SDLC Kit plugin.

Historically, the same regex constants were duplicated in 14–18 skill scripts.
Centralizing them here makes the contract explicit, testable and refactor-safe:
change the pattern in one place and every consumer picks it up.

All patterns are pre-compiled and ready to use. Consumers should import the
names directly rather than re-defining equivalent patterns locally.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Slug
# ---------------------------------------------------------------------------

# The slug convention across the plugin: lowercase alphanumerics, hyphens
# allowed but never as the first character. Used by every scaffold/transition
# action that accepts a --slug flag.
# \Z (not $) to reject trailing newlines — $ in Python also matches before a
# final \n, which would let "trailing\n" pass as a slug.
SLUG_RE: re.Pattern[str] = re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

# Matches a YAML-like frontmatter block at the start of a markdown document.
#
# The [ \t]* boundary on each fence line is intentional: it tolerates trailing
# whitespace (spaces, tabs) without consuming the blank line that immediately
# follows the closing fence. That blank line belongs to the body.
FRONTMATTER_RE: re.Pattern[str] = re.compile(
    r"^---[ \t]*\n(.*?)\n---[ \t]*\n",
    re.DOTALL,
)

# Matches a `status: <value>` line anywhere in a multiline string.
STATUS_LINE: re.Pattern[str] = re.compile(
    r"^(status:\s*)(\S+)\s*$",
    re.MULTILINE,
)

# Matches an `updated: <value>` line anywhere in a multiline string.
UPDATED_LINE: re.Pattern[str] = re.compile(
    r"^(updated:\s*)(\S+)\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Wikilinks
# ---------------------------------------------------------------------------

# Matches an Obsidian-flavored wikilink: [[target]], [[target|alias]],
# [[target#anchor]], [[target#anchor|alias]]. The captured group is always
# the clean target (alias + anchor stripped).
WIKILINK_RE: re.Pattern[str] = re.compile(
    r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]",
)


__all__ = [
    "SLUG_RE",
    "FRONTMATTER_RE",
    "STATUS_LINE",
    "UPDATED_LINE",
    "WIKILINK_RE",
]
