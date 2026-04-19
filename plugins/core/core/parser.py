"""Markdown parser for extracting frontmatter and metadata."""
import re
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# Regex para detectar frontmatter YAML (---\n...YAML...\n---)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Regex para extrair wikilinks: [[title]] ou [[title|alias]]
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def parse(path: Path) -> dict[str, Any]:
    """
    Parse a markdown file and extract frontmatter, body, and wikilinks.

    Args:
        path: Path to the markdown file.

    Returns:
        A dict with keys:
        - 'frontmatter': dict of YAML metadata (empty dict if no YAML or invalid)
        - 'body': str of markdown content (excluding frontmatter)
        - 'wikilinks': list of wikilink targets (titles only, aliases stripped)
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    fm: dict = {}
    body = text

    # Try to match frontmatter at the start of the file
    m = _FRONTMATTER_RE.match(text)
    if m:
        raw = m.group(1)
        if _HAS_YAML:
            try:
                fm = _yaml.safe_load(raw) or {}
            except Exception:
                # If YAML parsing fails, leave frontmatter empty
                fm = {}
        # Remove frontmatter from body
        body = text[m.end() :]

    return {
        "frontmatter": fm,
        "body": body,
        "wikilinks": _WIKILINK_RE.findall(body),
    }
