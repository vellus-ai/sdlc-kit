from pathlib import Path
import pytest
from core.parser import parse


def _md(tmp_path, content: str) -> Path:
    """Helper: create a temporary markdown file with the given content."""
    p = tmp_path / "note.md"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_frontmatter(tmp_path):
    """Test extraction of YAML frontmatter."""
    p = _md(tmp_path, "---\ntitle: Hello\nstatus: draft\n---\nBody text")
    result = parse(p)
    assert result["frontmatter"]["title"] == "Hello"
    assert result["frontmatter"]["status"] == "draft"


def test_parse_no_frontmatter(tmp_path):
    """Test parsing markdown without frontmatter."""
    p = _md(tmp_path, "# Just a heading\nSome text")
    result = parse(p)
    assert result["frontmatter"] == {}
    assert "Just a heading" in result["body"]


def test_parse_wikilinks(tmp_path):
    """Test extraction of [[wikilinks]] from body."""
    p = _md(tmp_path, "---\ntitle: Note\n---\nSee [[Other Note]] and [[Third|alias]]")
    result = parse(p)
    assert "Other Note" in result["wikilinks"]
    assert "Third" in result["wikilinks"]


def test_parse_no_wikilinks(tmp_path):
    """Test parsing when there are no wikilinks."""
    p = _md(tmp_path, "No links here")
    result = parse(p)
    assert result["wikilinks"] == []


def test_parse_body_excludes_frontmatter(tmp_path):
    """Test that body does not contain frontmatter."""
    p = _md(tmp_path, "---\ntitle: T\n---\nActual body")
    result = parse(p)
    assert "title" not in result["body"]
    assert "Actual body" in result["body"]
