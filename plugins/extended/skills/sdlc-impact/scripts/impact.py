#!/usr/bin/env python3
"""Change-impact analysis over the vault's wikilink graph.

Given a seed note, walk the `[[wikilink]]` graph and report every artifact that
depends on it (or that it depends on). Answers questions like "what breaks if
I deprecate ADR-0007?" (backward) or "what does this spec rely on?" (forward).

This skill is **read-only**: it parses markdown frontmatter and wikilinks,
builds an in-memory directed graph, runs a bounded BFS, and prints a JSON (or
markdown) report. It never writes to disk.

Action:
    analyze --seed <slug-or-stem> [--depth N] [--direction forward|backward|both]
            [--format json|markdown]

The graph reflects only wikilinks. If a note references another by plain text
or by code search, this script cannot see it — always cross-check with grep /
code search before a destructive action.

Emits a single JSON object (or `markdown` field) on stdout. Exit codes:
`0` ok, `1` user error (seed not found, ambiguous seed, not a vault),
`2` fatal (IO / permission).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.regexes import FRONTMATTER_RE, WIKILINK_RE  # noqa: E402

MARKER_REL = ".sdlc-kit/marker.json"

DEFAULT_DEPTH = 3
MAX_DEPTH = 10

VALID_DIRECTIONS: tuple[str, ...] = ("forward", "backward", "both")
VALID_FORMATS: tuple[str, ...] = ("json", "markdown")

# Whitespace bounded to inline chars so we keep the blank line after the fence.


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class Node:
    stem: str
    doc_type: str
    depth: int
    path: str

    def as_dict(self) -> dict:
        return {
            "stem": self.stem,
            "doc_type": self.doc_type,
            "depth": self.depth,
            "path": self.path,
        }


@dataclass
class Edge:
    frm: str
    to: str

    def as_dict(self) -> dict:
        return {"from": self.frm, "to": self.to}


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    seed: str = ""
    seed_path: str = ""
    direction: str = ""
    depth: int = 0
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    markdown: str = ""
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d: dict = {
            "status": self.status,
            "action": self.action,
            "vault_root": self.vault_root,
            "seed": self.seed,
            "seed_path": self.seed_path,
            "direction": self.direction,
            "depth": self.depth,
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [e.as_dict() for e in self.edges],
            "summary": self.summary,
            "errors": self.errors,
        }
        if self.markdown:
            d["markdown"] = self.markdown
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


def rel(vault: Path, path: Path) -> str:
    return str(path.relative_to(vault)).replace("\\", "/")


def should_skip(md_file: Path, vault_root: Path) -> bool:
    rel_parts = md_file.relative_to(vault_root).parts
    if not rel_parts:
        return True
    if ".sdlc-kit" in rel_parts:
        return True
    if "_templates" in rel_parts:
        return True
    # Skip any dot-prefixed directory segment (hidden folders). Never skip the
    # file itself based on name — CLAUDE.md and similar live at the root.
    return any(part.startswith(".") for part in rel_parts[:-1])


def _parse_frontmatter_block(fm_text: str) -> dict:
    fm: dict = {}
    for line in fm_text.split("\n"):
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2 or value.startswith("'") and value.endswith("'") and len(value) >= 2:
            value = value[1:-1]
        fm[key] = value
    return fm


def _body_after_frontmatter(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def extract_wikilinks(text: str) -> list[str]:
    """Return wikilink targets (stems), alias + anchor stripped."""
    results: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        # Defensive: even if the regex drifts, strip anchor and alias here.
        if "#" in target:
            target = target.split("#", 1)[0].strip()
        if "|" in target:
            target = target.split("|", 1)[0].strip()
        if not target:
            continue
        # Obsidian wikilinks may be `folder/name` — keep only the stem.
        if "/" in target:
            target = target.rsplit("/", 1)[-1]
        # Strip a trailing `.md` if the user wrote one.
        if target.lower().endswith(".md"):
            target = target[:-3]
        if target:
            results.append(target)
    return results


# ---------------------------------------------------------------------------
# vault walk
# ---------------------------------------------------------------------------

@dataclass
class VaultNote:
    stem: str
    path: Path
    rel: str
    frontmatter: dict
    wikilinks: list[str]
    doc_type: str
    slug: str
    title: str


def collect_notes(vault: Path) -> list[VaultNote]:
    notes: list[VaultNote] = []
    for md_file in sorted(vault.rglob("*.md")):
        if should_skip(md_file, vault):
            continue
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = FRONTMATTER_RE.match(text)
        fm = _parse_frontmatter_block(m.group(1)) if m else {}
        body = _body_after_frontmatter(text)
        wl = extract_wikilinks(body)
        notes.append(VaultNote(
            stem=md_file.stem,
            path=md_file,
            rel=rel(vault, md_file),
            frontmatter=fm,
            wikilinks=wl,
            doc_type=str(fm.get("type", "")),
            slug=str(fm.get("slug", "")),
            title=str(fm.get("title", "")),
        ))
    return notes


# ---------------------------------------------------------------------------
# seed resolution
# ---------------------------------------------------------------------------

def resolve_seed(seed: str, notes: list[VaultNote]) -> tuple[VaultNote | None, list[str]]:
    """Return (resolved_note, candidates).

    - If resolved_note is not None: unambiguous match.
    - If resolved_note is None and candidates is non-empty: ambiguous;
      candidates lists the relative paths.
    - If both are empty/None: not found.
    """
    # (a) exact stem match
    stem_matches = [n for n in notes if n.stem == seed]
    if len(stem_matches) == 1:
        return stem_matches[0], []
    if len(stem_matches) > 1:
        return None, [n.rel for n in stem_matches]

    # (b) frontmatter slug match
    slug_matches = [n for n in notes if n.slug and n.slug == seed]
    if len(slug_matches) == 1:
        return slug_matches[0], []
    if len(slug_matches) > 1:
        return None, [n.rel for n in slug_matches]

    # (c) frontmatter title match
    title_matches = [n for n in notes if n.title and n.title == seed]
    if len(title_matches) == 1:
        return title_matches[0], []
    if len(title_matches) > 1:
        return None, [n.rel for n in title_matches]

    return None, []


# ---------------------------------------------------------------------------
# graph + BFS
# ---------------------------------------------------------------------------

def build_graph(notes: list[VaultNote]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return (outgoing, incoming) maps. Edges to unknown stems are dropped."""
    known = {n.stem for n in notes}
    outgoing: dict[str, set[str]] = {n.stem: set() for n in notes}
    incoming: dict[str, set[str]] = {n.stem: set() for n in notes}
    for n in notes:
        for target in n.wikilinks:
            if target == n.stem:
                continue  # self-link
            if target in known:
                outgoing[n.stem].add(target)
                incoming[target].add(n.stem)
    return outgoing, incoming


def bfs(
    seed_stem: str,
    adjacency: dict[str, set[str]],
    *,
    depth: int,
    edge_orientation: str,
) -> tuple[list[tuple[str, int]], list[tuple[str, str]]]:
    """Breadth-first walk from `seed_stem` over `adjacency`.

    `edge_orientation` is either "outgoing" (frontier → neighbour) or "incoming"
    (neighbour → frontier). It only affects how edges are recorded.
    """
    visited: dict[str, int] = {seed_stem: 0}
    order: list[tuple[str, int]] = [(seed_stem, 0)]
    edges: list[tuple[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    frontier: list[str] = [seed_stem]
    for d in range(1, depth + 1):
        next_frontier: list[str] = []
        for node in frontier:
            for neighbour in sorted(adjacency.get(node, set())):
                edge = (node, neighbour) if edge_orientation == "outgoing" else (neighbour, node)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    edges.append(edge)
                if neighbour not in visited:
                    visited[neighbour] = d
                    order.append((neighbour, d))
                    next_frontier.append(neighbour)
        if not next_frontier:
            break
        frontier = next_frontier
    return order, edges


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

def action_analyze(
    vault: Path,
    *,
    seed_arg: str,
    depth: int,
    direction: str,
    out_format: str,
    report: Report,
) -> None:
    report.action = "analyze"
    report.seed = seed_arg
    report.direction = direction

    # Clamp depth silently to [0, MAX_DEPTH]. Depth 0 returns seed only.
    if depth < 0:
        depth = 0
    if depth > MAX_DEPTH:
        depth = MAX_DEPTH
    report.depth = depth

    notes = collect_notes(vault)
    if not notes:
        die(report, "vault contains no markdown notes to analyze", code=1)

    resolved, candidates = resolve_seed(seed_arg, notes)
    if resolved is None:
        if candidates:
            die(
                report,
                "ambiguous seed `{seed}` — matches: {paths}".format(
                    seed=seed_arg,
                    paths=", ".join(candidates),
                ),
                code=1,
            )
        die(
            report,
            f"seed `{seed_arg}` not found (no stem, slug, or title match in vault)",
            code=1,
        )
    assert resolved is not None
    report.seed = resolved.stem
    report.seed_path = resolved.rel

    outgoing, incoming = build_graph(notes)
    by_stem: dict[str, VaultNote] = {n.stem: n for n in notes}

    depth_of: dict[str, int] = {resolved.stem: 0}
    edges_set: set[tuple[str, str]] = set()
    order: list[tuple[str, int]] = [(resolved.stem, 0)]

    def merge(walk_order: list[tuple[str, int]], walk_edges: list[tuple[str, str]]) -> None:
        for stem, d in walk_order:
            prev = depth_of.get(stem)
            if prev is None:
                depth_of[stem] = d
                order.append((stem, d))
            elif d < prev:
                depth_of[stem] = d
        for e in walk_edges:
            edges_set.add(e)

    if direction in ("backward", "both"):
        back_order, back_edges = bfs(
            resolved.stem, incoming, depth=depth, edge_orientation="incoming"
        )
        merge([p for p in back_order if p[0] != resolved.stem], back_edges)
    if direction in ("forward", "both"):
        fwd_order, fwd_edges = bfs(
            resolved.stem, outgoing, depth=depth, edge_orientation="outgoing"
        )
        merge([p for p in fwd_order if p[0] != resolved.stem], fwd_edges)

    # Final node list: seed first, then others sorted by (depth asc, stem asc).
    seed_entry = (resolved.stem, 0)
    non_seed = [p for p in order if p[0] != resolved.stem]
    non_seed.sort(key=lambda p: (p[1], p[0]))
    ordered = [seed_entry] + non_seed

    for stem, d in ordered:
        note = by_stem.get(stem)
        if note is None:
            continue
        report.nodes.append(Node(
            stem=stem,
            doc_type=note.doc_type,
            depth=d,
            path=note.rel,
        ))

    for frm, to in sorted(edges_set):
        report.edges.append(Edge(frm=frm, to=to))

    dependents = [n for n in report.nodes if n.stem != resolved.stem]
    by_type: dict[str, int] = {}
    for n in dependents:
        key = n.doc_type or "unknown"
        by_type[key] = by_type.get(key, 0) + 1
    report.summary = {
        "total_dependents": len(dependents),
        "by_type": by_type,
        "unreachable": len(dependents) == 0,
    }

    if out_format == "markdown":
        report.markdown = render_markdown(report)


# ---------------------------------------------------------------------------
# markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(report: Report) -> str:
    lines: list[str] = []
    dir_label = {
        "backward": "dependents (who links to the seed)",
        "forward": "dependencies (what the seed links to)",
        "both": "dependents + dependencies (union)",
    }.get(report.direction, report.direction)

    lines.append(f"# Impact analysis — `{report.seed}`")
    lines.append("")
    lines.append(f"- **Seed path**: `{report.seed_path}`")
    lines.append(f"- **Direction**: {dir_label}")
    lines.append(f"- **Depth**: {report.depth}")
    lines.append(f"- **Total dependents (reached)**: {report.summary.get('total_dependents', 0)}")
    by_type = report.summary.get("by_type", {})
    if by_type:
        pretty = ", ".join(f"{k}: {v}" for k, v in sorted(by_type.items()))
        lines.append(f"- **By type**: {pretty}")
    if report.summary.get("unreachable"):
        lines.append("- **Unreachable**: no dependents within the requested depth.")
    lines.append("")

    # Tree by depth
    lines.append("## Tree (by depth)")
    lines.append("")
    by_depth: dict[int, list[Node]] = {}
    for n in report.nodes:
        by_depth.setdefault(n.depth, []).append(n)
    for d in sorted(by_depth.keys()):
        for n in sorted(by_depth[d], key=lambda x: x.stem):
            indent = "  " * d
            tag = f" _({n.doc_type})_" if n.doc_type else ""
            marker = " **[seed]**" if d == 0 else ""
            lines.append(f"{indent}- `{n.stem}`{tag}{marker} — `{n.path}`")
    lines.append("")

    # Grouped by type
    lines.append("## Grouped by type")
    lines.append("")
    groups: dict[str, list[Node]] = {}
    for n in report.nodes:
        if n.stem == report.seed:
            continue
        groups.setdefault(n.doc_type or "unknown", []).append(n)
    if not groups:
        lines.append("_(no dependents)_")
    else:
        for t in sorted(groups.keys()):
            lines.append(f"### {t}")
            for n in sorted(groups[t], key=lambda x: (x.depth, x.stem)):
                lines.append(f"- depth {n.depth}: `{n.stem}` — `{n.path}`")
            lines.append("")

    # Edges table
    if report.edges:
        lines.append("## Edges")
        lines.append("")
        lines.append("| from | to |")
        lines.append("|---|---|")
        for e in report.edges:
            lines.append(f"| `{e.frm}` | `{e.to}` |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit change-impact analyzer.")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["analyze"],
        help="analyze: walk the wikilink graph from a seed note",
    )
    p.add_argument("--seed", help="seed note stem or frontmatter slug (required for analyze)")
    p.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        help=f"max traversal depth (default {DEFAULT_DEPTH}, capped at {MAX_DEPTH})",
    )
    p.add_argument(
        "--direction",
        choices=list(VALID_DIRECTIONS),
        default="backward",
        help="backward (default): who depends on seed | forward: what seed depends on | both: union",
    )
    p.add_argument(
        "--format",
        dest="out_format",
        choices=list(VALID_FORMATS),
        default="json",
        help="output format (default json); markdown adds a human-readable `markdown` field",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main() -> None:
    args = parse_args()
    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    if args.action == "analyze":
        if not args.seed:
            die(report, "--seed is required for action `analyze`", code=1)
        try:
            action_analyze(
                vault,
                seed_arg=args.seed,
                depth=args.depth,
                direction=args.direction,
                out_format=args.out_format,
                report=report,
            )
        except PermissionError as exc:
            die(report, f"permission denied: {exc}", code=2)
        except OSError as exc:
            die(report, f"filesystem error: {exc}", code=2)

    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
