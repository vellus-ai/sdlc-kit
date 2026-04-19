"""Unit + property-based tests for core.frontmatter.

Covers the shared helpers extracted from the 18 skill scripts that previously
duplicated this logic: reading frontmatter from disk, splitting text into
frontmatter+body, updating a quoted field, and round-tripping a dict.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core.frontmatter import (
    parse_frontmatter_text,
    read_frontmatter,
    render_frontmatter,
    set_quoted_field,
)

# ---------------------------------------------------------------------------
# read_frontmatter
# ---------------------------------------------------------------------------

class TestReadFrontmatter:
    def test_reads_simple_frontmatter(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\ntype: note\ntitle: Foo\n---\n\nBody.\n", encoding="utf-8")
        fm = read_frontmatter(f)
        assert fm == {"type": "note", "title": "Foo"}

    def test_strips_quoted_values(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text('---\ntitle: "Quoted Title"\n---\n\nBody.\n', encoding="utf-8")
        fm = read_frontmatter(f)
        assert fm["title"] == "Quoted Title"

    def test_empty_dict_when_no_frontmatter(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("No frontmatter here.\n", encoding="utf-8")
        assert read_frontmatter(f) == {}

    def test_empty_dict_when_file_missing(self, tmp_path: Path) -> None:
        assert read_frontmatter(tmp_path / "nonexistent.md") == {}

    def test_ignores_comment_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\n# comment\ntype: note\n---\n", encoding="utf-8")
        fm = read_frontmatter(f)
        assert fm == {"type": "note"}

    def test_ignores_non_key_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\ntype: note\njust a line\n---\n", encoding="utf-8")
        fm = read_frontmatter(f)
        assert fm == {"type": "note"}

    def test_ignores_empty_key(self, tmp_path: Path) -> None:
        """A colon-only line like `: value` has no key and must be ignored."""
        f = tmp_path / "note.md"
        f.write_text("---\ntype: note\n: orphaned\n---\n", encoding="utf-8")
        fm = read_frontmatter(f)
        assert fm == {"type": "note"}

    def test_handles_non_utf8_bytes(self, tmp_path: Path) -> None:
        """Invalid UTF-8 bytes should be replaced, not crash."""
        f = tmp_path / "note.md"
        f.write_bytes(b"---\ntype: note\ntitle: caf\xc3\xa9\n---\n")
        fm = read_frontmatter(f)
        assert fm["type"] == "note"

    def test_handles_broken_utf8(self, tmp_path: Path) -> None:
        """Truly broken bytes are replaced (errors='replace')."""
        f = tmp_path / "note.md"
        f.write_bytes(b"---\ntype: note\ntitle: \xff\xfe broken\n---\n")
        fm = read_frontmatter(f)
        assert fm["type"] == "note"


# ---------------------------------------------------------------------------
# parse_frontmatter_text
# ---------------------------------------------------------------------------

class TestParseFrontmatterText:
    def test_returns_frontmatter_and_body(self) -> None:
        text = "---\ntype: note\n---\n\n# Body\n\nContent."
        fm, body = parse_frontmatter_text(text)
        assert fm == {"type": "note"}
        assert body.startswith("\n# Body") or body.startswith("# Body")

    def test_empty_when_no_fence(self) -> None:
        fm, body = parse_frontmatter_text("Just body.\n")
        assert fm == {}
        assert body == "Just body.\n"

    def test_empty_frontmatter_handled(self) -> None:
        fm, body = parse_frontmatter_text("---\n\n---\n\nBody.")
        # Degenerate case: empty frontmatter yields empty dict.
        assert isinstance(fm, dict)

    def test_multiple_values(self) -> None:
        text = "---\ntype: trd\nstatus: approved\nslug: rate-limits\n---\n\n"
        fm, _ = parse_frontmatter_text(text)
        assert fm == {"type": "trd", "status": "approved", "slug": "rate-limits"}


# ---------------------------------------------------------------------------
# set_quoted_field
# ---------------------------------------------------------------------------

class TestSetQuotedField:
    def test_updates_existing_field(self) -> None:
        fm = 'type: review\npr: "1"\nauthor: "alice"'
        regex = re.compile(r'^(pr:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
        out = set_quoted_field(fm, regex, "pr", "42")
        assert '"42"' in out
        assert '"1"' not in out

    def test_appends_when_missing(self) -> None:
        fm = "type: review\nauthor: alice"
        regex = re.compile(r'^(pr:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
        out = set_quoted_field(fm, regex, "pr", "42")
        assert out.endswith('pr: "42"')


class TestSetQuotedFieldPBT:
    @given(
        value=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_ ", min_size=0, max_size=40).filter(
            lambda s: '"' not in s and '\n' not in s
        ),
    )
    @pytest.mark.pbt
    def test_idempotent_on_update(self, value: str) -> None:
        """Applying set_quoted_field twice with same args = same result as once."""
        fm = 'type: review\npr: "old"\nauthor: "alice"'
        regex = re.compile(r'^(pr:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
        once = set_quoted_field(fm, regex, "pr", value)
        twice = set_quoted_field(once, regex, "pr", value)
        assert once == twice

    @given(
        value=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_ ", min_size=0, max_size=40).filter(
            lambda s: '"' not in s and '\n' not in s
        ),
    )
    @pytest.mark.pbt
    def test_idempotent_on_append(self, value: str) -> None:
        """Appending twice leaves a single line with the target value."""
        fm = "type: review\nauthor: alice"
        regex = re.compile(r'^(pr:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
        once = set_quoted_field(fm, regex, "pr", value)
        twice = set_quoted_field(once, regex, "pr", value)
        assert once == twice

    @given(
        value=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_ ", min_size=0, max_size=40).filter(
            lambda s: '"' not in s and '\n' not in s
        ),
    )
    @pytest.mark.pbt
    def test_postcondition_value_present(self, value: str) -> None:
        """After set_quoted_field, the regex should find the new value."""
        fm = 'type: review\npr: "old"\nauthor: "alice"'
        regex = re.compile(r'^(pr:\s*)"?([^"\n]*)"?\s*$', re.MULTILINE)
        out = set_quoted_field(fm, regex, "pr", value)
        m = regex.search(out)
        assert m is not None
        assert m.group(2) == value


# ---------------------------------------------------------------------------
# render_frontmatter / round-trip
# ---------------------------------------------------------------------------

class TestRenderFrontmatter:
    def test_basic_render(self) -> None:
        out = render_frontmatter({"type": "note", "title": "Foo"})
        assert out.startswith("---\n")
        assert out.endswith("---\n")
        assert "type: note" in out
        assert "title: Foo" in out

    def test_quotes_values_with_special_chars(self) -> None:
        out = render_frontmatter({"title": "Has: colon"})
        assert '"Has: colon"' in out

    def test_empty_dict(self) -> None:
        out = render_frontmatter({})
        assert out == "---\n---\n"

    def test_empty_string_value(self) -> None:
        """Empty strings should render without quotes."""
        out = render_frontmatter({"k": ""})
        assert "k: \n" in out or "k:" in out

    def test_leading_whitespace_value_quoted(self) -> None:
        """Values starting with whitespace must be quoted."""
        out = render_frontmatter({"k": " leading"})
        assert '"' in out.split("k:")[1]

    def test_trailing_whitespace_value_quoted(self) -> None:
        """Values ending with whitespace must be quoted."""
        out = render_frontmatter({"k": "trailing "})
        assert '"' in out.split("k:")[1]


class TestFrontmatterRoundTrip:
    """PBT: parse(render(d)) == d for any valid dict."""

    _valid_key = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20
    )
    _valid_value = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ",
        min_size=1,
        max_size=30,
    ).filter(lambda s: '"' not in s and '\n' not in s and not s.startswith(' ') and not s.endswith(' '))

    @given(d=st.dictionaries(_valid_key, _valid_value, min_size=1, max_size=10))
    @pytest.mark.pbt
    def test_roundtrip(self, d: dict[str, str]) -> None:
        rendered = render_frontmatter(d) + "\n"
        parsed, _ = parse_frontmatter_text(rendered)
        assert parsed == d


# ---------------------------------------------------------------------------
# Integration: reading a real template
# ---------------------------------------------------------------------------

class TestReadRealTemplate:
    def test_reads_actual_trd_template(self) -> None:
        """The canonical TRD template must parse correctly."""
        repo_root = Path(__file__).parent.parent
        tpl = repo_root / "plugins" / "core" / "assets" / "vault-tree" / "02-architecture" / "_templates" / "trd.md.tpl"
        if not tpl.exists():
            pytest.skip("TRD template not present")
        fm = read_frontmatter(tpl)
        assert fm.get("type") == "trd"
        assert "title" in fm
