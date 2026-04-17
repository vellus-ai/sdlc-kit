---
name: sdlc-domain
description: Esta skill deve ser usada para criar documentação DDD de um bounded context, ou quando o usuário invoca /sdlc-kit:domain. Gera context-map.md (Mermaid), ubiquitous-language.md e domain-events.md em 04-domain/. Use ao modelar novos contextos ou refinar ubiquitous language.
---

# sdlc-kit:domain

Creates and manages Domain-Driven Design (DDD) documentation for bounded contexts under `04-domain/`.

## When to invoke

When defining a new bounded context, adding domain events, or listing existing contexts.

## Flow

### create-context
1. Ask: bounded context name
2. Generate `04-domain/<slug>/context-map.md` (defines relationships with other contexts)
3. Generate `04-domain/<slug>/ubiquitous-language.md` (shared vocabulary)
4. Run `/sdlc-kit:sync`

### add-event
1. Ask: bounded context name and domain event name
2. Append event entry to `04-domain/<slug>/domain-events.md` (creates file if absent)
3. Run `/sdlc-kit:sync`

### list-contexts
1. Return all bounded context directories in `04-domain/` (excluding `_templates`)

## Guardrails

- Never overwrite existing context files — skip if already present
- Status always starts as "draft"
- Ubiquitous language entries must be added manually by the team
- Domain events are append-only; never delete existing events
