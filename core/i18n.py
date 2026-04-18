"""Internationalization helpers for the SDLC Kit plugin.

The librarian (`sdlc-sync`) renders `_INDEX.md` from a template of section
headings and empty-state messages. Historically those strings lived hard-coded
in Portuguese inside `sync.py`. This module centralizes them with a single
`t(locale, key, **kwargs)` resolver so the renderer can swap languages based
on `.sdlc-kit/marker.json:locale`.

Contract:
- `t("pt-br", "index.heading", project="Acme")` → localized string.
- Missing key in target locale → fallback to `"en"`.
- Missing key in `"en"` too → return the key itself (visible marker, not a
  silent empty string).

Primary locale is `pt-br` (matches the 60+ strings already in the plugin).
English is the fallback; missing translations return the key so they're easy
to spot during development.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = ["DEFAULT_LOCALE", "FALLBACK_LOCALE", "MESSAGES", "t", "available_locales", "list_keys"]

DEFAULT_LOCALE = "pt-br"
FALLBACK_LOCALE = "en"


MESSAGES: dict[str, dict[str, str]] = {
    "pt-br": {
        # Heading + disclaimer
        "index.title": "Índice — {project}",
        "index.disclaimer": "> Gerado automaticamente por `/sdlc-kit:sync`. **Não editar manualmente.**",
        "index.last_sync": "> Última sincronização: {timestamp}",
        # Panorama
        "index.panorama.heading": "## Panorama",
        "index.panorama.total": "Total de documentos",
        "index.panorama.epics_active": "Epics ativos",
        "index.panorama.specs_active": "Specs em andamento",
        "index.panorama.tasks_open": "Tasks abertas",
        "index.panorama.tasks_done": "Tasks concluídas",
        "index.panorama.incidents_open": "Incidents abertos",
        "index.panorama.adrs_total": "ADRs registrados",
        # Phase 00 — Steering
        "index.steering.heading": "## Direção (00-steering)",
        "index.steering.product": "Visão de produto",
        "index.steering.tech": "Princípios técnicos",
        "index.steering.standards": "Padrões do time",
        "index.steering.registered": "registrado",
        "index.steering.pending": "pendente",
        # Phase 01 — Planning
        "index.planning.heading": "## Planejamento (01-planning)",
        "index.planning.prd_section": "### PRDs",
        "index.planning.prd_empty": '_Nenhum PRD registrado. Rode `/sdlc-kit:prd new "<iniciativa>"`._',
        "index.planning.epic_section": "### Epics",
        "index.planning.epic_empty": "_Nenhum epic registrado._",
        "index.planning.milestone_section": "### Milestones",
        "index.planning.milestone_empty": "_Nenhum milestone registrado._",
        # Phase 02 — Architecture
        "index.arch.heading": "## Arquitetura (02-architecture)",
        "index.arch.adr_section": "### ADRs",
        "index.arch.adr_empty": '_Nenhum ADR registrado. Rode `/sdlc-kit:adr new "<decisão>"`._',
        "index.arch.c4_section": "### C4",
        "index.arch.c4_level1": "Nível 1 (Contexto)",
        "index.arch.c4_level2": "Nível 2 (Containers)",
        "index.arch.c4_level3": "Nível 3 (Componentes)",
        "index.arch.c4_pending": "pendente",
        "index.arch.trd_section": "### TRDs",
        "index.arch.trd_empty": "_Nenhum TRD registrado._",
        "index.arch.api_section": "### APIs",
        "index.arch.api_empty": "_Nenhum contrato de API registrado._",
        # Phase 03 — Domain
        "index.domain.heading": "## Domínio (03-domain)",
        "index.domain.context_map": "Mapa de bounded contexts",
        "index.domain.ubiquitous": "Glossário",
        "index.domain.pending": "pendente",
        "index.domain.artifacts_empty": "_Nenhum aggregate, evento ou contrato registrado._",
        # Phase 04 — Specs
        "index.specs.heading": "## Specs (04-specs)",
        "index.specs.empty": '_Nenhuma spec criada. Rode `/sdlc-kit:spec new "<feature>"`._',
        # Phase 05 — Development
        "index.dev.heading": "## Desenvolvimento (05-development)",
        "index.dev.worktree_section": "### Worktrees",
        "index.dev.worktree_empty": "_Nenhum worktree ativo._",
        "index.dev.branch_section": "### Branches rastreadas",
        "index.dev.branch_empty": "_Nenhuma branch registrada._",
        # Phase 06 — Design System
        "index.design.heading": "## Design System (06-design-system)",
        "index.design.empty": "_Vazio. Rode `/sdlc-kit:design-system new {token|component|pattern}`._",
        # Phase 07 — Retrospectives
        "index.retro.heading": "## Retrospectivas (07-retrospectives)",
        "index.retro.retros_section": "### Retros",
        "index.retro.retros_empty": "_Nenhuma retro registrada. Rode `/sdlc-kit:retro` para criar a primeira retrospectiva._",
        "index.retro.reviews_section": "### Code Reviews",
        "index.retro.reviews_empty": "_Nenhum code review registrado._",
        "index.retro.incidents_section": "### Incidents",
        "index.retro.incidents_empty": "_Nenhum incidente registrado._",
        # Anomalies
        "index.anomalies.heading": "## Anomalias detectadas",
        "index.anomalies.empty": "_Nenhuma anomalia._",
        "index.anomalies.count": "Total: {count}. Detalhe via `/sdlc-kit:sync`.",
        # Shortcuts
        "index.shortcuts.heading": "## Atalhos úteis",
        "index.shortcuts.doctrine": "doutrina do vault (leitura obrigatória)",
        "index.shortcuts.dashboard": "painel autocontido (abrir no browser)",
    },
    "en": {
        # Heading + disclaimer
        "index.title": "Index — {project}",
        "index.disclaimer": "> Auto-generated by `/sdlc-kit:sync`. **Do not edit manually.**",
        "index.last_sync": "> Last sync: {timestamp}",
        # Panorama
        "index.panorama.heading": "## Overview",
        "index.panorama.total": "Total documents",
        "index.panorama.epics_active": "Active epics",
        "index.panorama.specs_active": "Specs in progress",
        "index.panorama.tasks_open": "Open tasks",
        "index.panorama.tasks_done": "Completed tasks",
        "index.panorama.incidents_open": "Open incidents",
        "index.panorama.adrs_total": "ADRs recorded",
        # Phase 00 — Steering
        "index.steering.heading": "## Steering (00-steering)",
        "index.steering.product": "Product vision",
        "index.steering.tech": "Technical principles",
        "index.steering.standards": "Team standards",
        "index.steering.registered": "registered",
        "index.steering.pending": "pending",
        # Phase 01 — Planning
        "index.planning.heading": "## Planning (01-planning)",
        "index.planning.prd_section": "### PRDs",
        "index.planning.prd_empty": '_No PRDs recorded. Run `/sdlc-kit:prd new "<initiative>"`._',
        "index.planning.epic_section": "### Epics",
        "index.planning.epic_empty": "_No epics recorded._",
        "index.planning.milestone_section": "### Milestones",
        "index.planning.milestone_empty": "_No milestones recorded._",
        # Phase 02 — Architecture
        "index.arch.heading": "## Architecture (02-architecture)",
        "index.arch.adr_section": "### ADRs",
        "index.arch.adr_empty": '_No ADRs recorded. Run `/sdlc-kit:adr new "<decision>"`._',
        "index.arch.c4_section": "### C4",
        "index.arch.c4_level1": "Level 1 (Context)",
        "index.arch.c4_level2": "Level 2 (Containers)",
        "index.arch.c4_level3": "Level 3 (Components)",
        "index.arch.c4_pending": "pending",
        "index.arch.trd_section": "### TRDs",
        "index.arch.trd_empty": "_No TRDs recorded._",
        "index.arch.api_section": "### APIs",
        "index.arch.api_empty": "_No API contracts recorded._",
        # Phase 03 — Domain
        "index.domain.heading": "## Domain (03-domain)",
        "index.domain.context_map": "Bounded contexts map",
        "index.domain.ubiquitous": "Glossary",
        "index.domain.pending": "pending",
        "index.domain.artifacts_empty": "_No aggregates, events or contracts recorded._",
        # Phase 04 — Specs
        "index.specs.heading": "## Specs (04-specs)",
        "index.specs.empty": '_No specs created. Run `/sdlc-kit:spec new "<feature>"`._',
        # Phase 05 — Development
        "index.dev.heading": "## Development (05-development)",
        "index.dev.worktree_section": "### Worktrees",
        "index.dev.worktree_empty": "_No active worktrees._",
        "index.dev.branch_section": "### Tracked branches",
        "index.dev.branch_empty": "_No branches registered._",
        # Phase 06 — Design System
        "index.design.heading": "## Design System (06-design-system)",
        "index.design.empty": "_Empty. Run `/sdlc-kit:design-system new {token|component|pattern}`._",
        # Phase 07 — Retrospectives
        "index.retro.heading": "## Retrospectives (07-retrospectives)",
        "index.retro.retros_section": "### Retros",
        "index.retro.retros_empty": "_No retros recorded. Run `/sdlc-kit:retro` to capture the first retrospective._",
        "index.retro.reviews_section": "### Code Reviews",
        "index.retro.reviews_empty": "_No code reviews recorded._",
        "index.retro.incidents_section": "### Incidents",
        "index.retro.incidents_empty": "_No incidents recorded._",
        # Anomalies
        "index.anomalies.heading": "## Detected anomalies",
        "index.anomalies.empty": "_No anomalies._",
        "index.anomalies.count": "Total: {count}. Detail via `/sdlc-kit:sync`.",
        # Shortcuts
        "index.shortcuts.heading": "## Useful shortcuts",
        "index.shortcuts.doctrine": "vault doctrine (required reading)",
        "index.shortcuts.dashboard": "self-contained dashboard (open in browser)",
    },
}


def available_locales() -> list[str]:
    """Return the locales for which MESSAGES has entries."""
    return sorted(MESSAGES.keys())


def list_keys(locale: str = FALLBACK_LOCALE) -> list[str]:
    """Return all message keys for a locale (sorted)."""
    return sorted(MESSAGES.get(locale, {}).keys())


def t(locale: str, key: str, /, **kwargs: Any) -> str:
    """Translate a key for the given locale, falling back to English then key.

    Supports `{placeholder}` substitution via `str.format(**kwargs)`. Missing
    placeholders in kwargs leave the placeholder literal in the output rather
    than raising.
    """
    table: Mapping[str, str] = MESSAGES.get(locale, {})
    text = table.get(key)
    if text is None and locale != FALLBACK_LOCALE:
        text = MESSAGES.get(FALLBACK_LOCALE, {}).get(key)
    if text is None:
        return key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
