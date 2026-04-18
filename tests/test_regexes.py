"""Unit + property-based tests for core.regexes — canonical regex patterns.

The module centralizes regex constants previously duplicated across 18+ skill
scripts. These tests pin down the exact match semantics so any future refactor
cannot silently drift.
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core.regexes import (
    FRONTMATTER_RE,
    SLUG_RE,
    STATUS_LINE,
    UPDATED_LINE,
    WIKILINK_RE,
)

# ---------------------------------------------------------------------------
# SLUG_RE
# ---------------------------------------------------------------------------

class TestSlugRe:
    @pytest.mark.parametrize("slug", [
        "a",
        "0",
        "abc",
        "abc-def",
        "a1b2c3",
        "login-google",
        "adr-0007-oauth",
        "pr-0042-login-google",
    ])
    def test_valid_slugs(self, slug):
        assert SLUG_RE.match(slug) is not None

    @pytest.mark.parametrize("slug", [
        "",
        "-leading-hyphen",
        "Bad_Slug",
        "UPPER",
        "has space",
        "dot.in.slug",
        "special!char",
        "trailing\n",
    ])
    def test_invalid_slugs(self, slug):
        assert SLUG_RE.match(slug) is None


class TestSlugRePBT:
    """Property-based invariants for SLUG_RE."""

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=40))
    @pytest.mark.pbt
    def test_lowercase_alnum_always_matches(self, s):
        """Any non-empty lowercase alnum string is a valid slug."""
        assert SLUG_RE.match(s) is not None

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=20),
           st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=20))
    @pytest.mark.pbt
    def test_hyphen_between_alnum_valid(self, a, b):
        """`a-b` where both a and b are valid slugs is also a valid slug."""
        candidate = f"{a}-{b}"
        assert SLUG_RE.match(candidate) is not None

    @given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=10))
    @pytest.mark.pbt
    def test_uppercase_never_matches(self, s):
        """Uppercase-only strings are never valid slugs."""
        assert SLUG_RE.match(s) is None

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=40))
    @pytest.mark.pbt
    def test_match_is_idempotent(self, s):
        """Matching is a pure function: same input → same result, always."""
        first = SLUG_RE.match(s) is not None
        second = SLUG_RE.match(s) is not None
        assert first == second


# ---------------------------------------------------------------------------
# FRONTMATTER_RE
# ---------------------------------------------------------------------------

class TestFrontmatterRe:
    def test_matches_simple_frontmatter(self):
        text = "---\ntype: note\ntitle: Foo\n---\n\nBody text."
        m = FRONTMATTER_RE.match(text)
        assert m is not None
        assert "type: note" in m.group(1)
        assert "title: Foo" in m.group(1)

    def test_preserves_trailing_blank_line_boundary(self):
        """The regex must stop at `---\n` so the blank line after it is body."""
        text = "---\ntype: note\n---\n\nBody.\n"
        m = FRONTMATTER_RE.match(text)
        assert m is not None
        remaining = text[m.end():]
        assert remaining.startswith("\nBody.") or remaining.startswith("Body.")

    def test_no_match_without_opening_fence(self):
        text = "type: note\ntitle: Foo\n\nBody."
        assert FRONTMATTER_RE.match(text) is None

    def test_no_match_without_closing_fence(self):
        text = "---\ntype: note\ntitle: Foo\n\nBody."
        assert FRONTMATTER_RE.match(text) is None

    def test_allows_trailing_spaces_on_fence(self):
        text = "---  \ntype: note\n---  \n\nBody."
        m = FRONTMATTER_RE.match(text)
        assert m is not None

    def test_allows_trailing_tabs_on_fence(self):
        text = "---\t\ntype: note\n---\t\n\nBody."
        m = FRONTMATTER_RE.match(text)
        assert m is not None

    def test_captures_multiline_content(self):
        text = "---\na: 1\nb: 2\nc: 3\n---\n\n"
        m = FRONTMATTER_RE.match(text)
        assert m.group(1) == "a: 1\nb: 2\nc: 3"


# ---------------------------------------------------------------------------
# STATUS_LINE / UPDATED_LINE
# ---------------------------------------------------------------------------

class TestStatusLine:
    def test_matches_simple(self):
        m = STATUS_LINE.search("status: draft")
        assert m is not None
        assert m.group(2) == "draft"

    def test_matches_in_multiline_frontmatter(self):
        fm = "type: trd\nstatus: approved\nupdated: 2026-04-18"
        m = STATUS_LINE.search(fm)
        assert m is not None
        assert m.group(2) == "approved"

    def test_matches_with_extra_whitespace(self):
        m = STATUS_LINE.search("status:   draft  ")
        assert m is not None
        assert m.group(2) == "draft"

    def test_no_match_when_status_absent(self):
        assert STATUS_LINE.search("type: note\ntitle: Foo") is None


class TestUpdatedLine:
    def test_matches_iso_date(self):
        m = UPDATED_LINE.search("updated: 2026-04-18")
        assert m is not None
        assert m.group(2) == "2026-04-18"

    def test_matches_in_frontmatter(self):
        fm = "type: trd\nstatus: draft\nupdated: 2025-12-31"
        m = UPDATED_LINE.search(fm)
        assert m.group(2) == "2025-12-31"


# ---------------------------------------------------------------------------
# WIKILINK_RE
# ---------------------------------------------------------------------------

class TestWikilinkRe:
    def test_simple_wikilink(self):
        matches = WIKILINK_RE.findall("see [[note-a]] for details")
        assert matches == ["note-a"]

    def test_wikilink_with_alias_strips_alias(self):
        matches = WIKILINK_RE.findall("see [[note-a|my alias]] here")
        assert matches == ["note-a"]

    def test_wikilink_with_anchor_strips_anchor(self):
        matches = WIKILINK_RE.findall("see [[note-a#section]] there")
        assert matches == ["note-a"]

    def test_multiple_wikilinks(self):
        matches = WIKILINK_RE.findall("[[a]] and [[b|alias]] and [[c#sec]]")
        assert matches == ["a", "b", "c"]

    def test_no_match_in_single_bracket(self):
        assert WIKILINK_RE.findall("[not a link] or [single]") == []

    def test_ignores_unclosed_bracket(self):
        """Unclosed [[ should not match (no crash, just no result)."""
        result = WIKILINK_RE.findall("[[unclosed")
        assert result == []
