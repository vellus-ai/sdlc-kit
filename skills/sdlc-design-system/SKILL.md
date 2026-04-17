---
name: sdlc-design-system
description: Esta skill deve ser usada para documentar tokens de design, componentes e padrões, ou quando o usuário invoca /sdlc-kit:design-system. Mantém 06-design-system/ com specs de tokens (cores, tipografia, espaçamento), biblioteca de componentes e padrões de interação.
---

# sdlc-kit:design-system

Manages design system documentation under `06-design-system/`, including design tokens, components, and patterns.

## When to invoke

When initializing design system docs, adding a new design token (color, spacing, typography), or documenting a new UI component.

## Flow

### init
1. Create `06-design-system/tokens.md`, `components.md`, `patterns.md` (skips if already exist)
2. Run `/sdlc-kit:sync`

### add-token
1. Ask: token name (e.g. "primary-color")
2. Ask: token category (e.g. "color", "spacing", "typography")
3. Ask: token value (e.g. "#1A73E8", "16px", "Inter")
4. Append row to `06-design-system/tokens.md`
5. Run `/sdlc-kit:sync`

### add-component
1. Ask: component name (e.g. "Button", "Card")
2. Append entry to `06-design-system/components.md`
3. Run `/sdlc-kit:sync`

## Guardrails

- `init` is idempotent — never overwrites existing files
- Token values should be raw values, not references to other tokens
- Component entries start as "draft" — promote to "stable" after design review
