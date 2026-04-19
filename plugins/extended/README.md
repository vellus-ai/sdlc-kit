<div align="center">

# 🏗 sdlc-kit-extended

### *Governance · Architecture · Domain · Post-delivery analysis*

11 additional Claude Code skills that **layer on top of `sdlc-kit` core** to cover everything beyond the daily PR loop: TRDs, epics, milestones, C4 diagrams, API contracts, DDD aggregates, design system, incidents, traceability matrices and impact analysis.

<p>
  <a href="https://claude.ai/code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?logo=anthropic"></a>
  <img alt="Skills" src="https://img.shields.io/badge/skills-11-blueviolet">
  <img alt="Requires" src="https://img.shields.io/badge/requires-sdlc--kit%20core-orange">
  <img alt="Version" src="https://img.shields.io/badge/version-0.4.0-orange">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

</div>

> 📖 **Também disponível em [Português (Brasil)](#português-brasil).**

---

## ⚠️ Prerequisite

`sdlc-kit-extended` is a **layered plugin**. You must install the **core** first (it owns the vault marker, the SQLite tracker and the PostToolUse hook). Without the core, none of these skills can act on a vault.

```text
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit            # required first
/plugin install sdlc-kit-extended@sdlc-kit   # then this
/reload-plugins
```

---

## 🎯 The 11 skills

### 📐 Governance

| Skill | Scope |
|---|---|
| `/sdlc-kit:trd` | Cross-cutting Technical Requirements (performance, scalability, security, LGPD, observability, a11y, i18n, cost). Lifecycle `draft → approved → deprecated`. |
| `/sdlc-kit:epic` | Large deliverables grouping stories/specs. Lifecycle `planned → in-progress → done` + `cancelled`. |
| `/sdlc-kit:milestone` | Delivery windows with RAG status (`planned → on-track → at-risk → slipped → done` + `cancelled`). Supports `--target-date`. |
| `/sdlc-kit:steer` | Updates the three steering docs in `00-steering/`: product vision, technical principles, team standards. Transitions `draft → active`. |

### 🏛 Architecture & Domain

| Skill | Scope |
|---|---|
| `/sdlc-kit:c4` | C4 model diagrams in Mermaid — 3 levels: `context`/`container` (singletons) + `component` (collection). |
| `/sdlc-kit:api` | API contracts in 4 styles: `rest`, `async`, `grpc`, `webhook`. Each with `draft → approved → deprecated` lifecycle. |
| `/sdlc-kit:domain` | DDD artifacts — 5 kinds: `aggregate`, `event`, `contract` (collections) + `context-map`, `ubiquitous-language` (singletons). |
| `/sdlc-kit:design-system` | 3 kinds: `token`, `component`, `pattern`. Lifecycle `draft → stable → deprecated`. |

### 🚨 Operations & Analysis

| Skill | Scope |
|---|---|
| `/sdlc-kit:incident` | Post-mortem records. 4-state lifecycle `open → mitigated → resolved → post-mortem` with auto-populated timestamps. Severity enum `SEV1..SEV4`. |
| `/sdlc-kit:trace` | **Read-only** traceability matrix: walks the wikilink graph and reports PRD → spec-requirements → spec-design → spec-tasks → review. Flags orphan ADRs/TRDs, unimplemented PRDs, dangling designs. Formats `json` / `markdown`. |
| `/sdlc-kit:impact` | **Read-only** BFS over the wikilink graph. Given a seed note, reports what depends on it (`backward`), what it depends on (`forward`), or both. Depth clamped to 10. Use before deprecating an ADR, a TRD, a design-system token or an aggregate. |

---

## 🔬 Compatibility with the core

Extended skills follow the same canonical contract:

- `list / scaffold / transition` (with `decide` as an extra axis only on `sdlc-kit:review` — a core skill).
- Single JSON object on stdout, exit codes `0/1/2`.
- Every artifact type is registered in the same `sdlc-sync` schema — `scripts/audit_registry.py` enforces zero drift across both plugins.
- `.sdlc-kit/marker.json:locale` determines the language of generated indexes (`pt-br` default, `en` alternative).

---

## 🧭 When to install

✅ **Install if** you:
- adopt DDD / Clean Architecture seriously
- care about SLOs, SLIs, non-functional requirements as versioned artifacts
- need traceability matrices for audit / compliance (LGPD, SOC2)
- want post-mortems with auto-populated timelines
- need to assess blast radius before refactors

❌ **Skip if** you just need PRDs, specs and code reviews — the core plugin covers that alone.

---

## 🔗 Links

- Core plugin (required): [`sdlc-kit@sdlc-kit`](../core/README.md)
- Parent repo & full docs: [`vellus-ai/sdlc-kit`](https://github.com/vellus-ai/sdlc-kit)

[MIT](../../LICENSE) © 2026 [Vellus](https://vellus.tech/)

---
---

## Português (Brasil)

### *Governança · Arquitetura · Domínio · Análise pós-entrega*

11 skills Claude Code adicionais que **se sobrepõem ao `sdlc-kit` core** para cobrir tudo além do ciclo de PR diário: TRDs, épicos, milestones, diagramas C4, contratos de API, aggregates DDD, design system, incidentes, matrizes de rastreabilidade e análise de impacto.

### Pré-requisito

`sdlc-kit-extended` é um **plugin em camada**. Você precisa instalar o **core** primeiro (ele é dono do marker do vault, do SQLite tracker e do hook PostToolUse). Sem o core, nenhuma destas skills atua no vault.

```text
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit            # obrigatório primeiro
/plugin install sdlc-kit-extended@sdlc-kit   # depois este
/reload-plugins
```

### As 11 skills

#### 📐 Governança

| Skill | Escopo |
|---|---|
| `/sdlc-kit:trd` | Technical Requirements Document cross-cutting (perf, scalability, security, LGPD, observability, a11y, i18n, cost). Lifecycle `draft → approved → deprecated`. |
| `/sdlc-kit:epic` | Grandes entregas agrupando stories/specs. Lifecycle `planned → in-progress → done` + `cancelled`. |
| `/sdlc-kit:milestone` | Janelas de entrega com RAG status. Suporta `--target-date`. |
| `/sdlc-kit:steer` | Atualiza os 3 docs de steering em `00-steering/`: visão de produto, princípios técnicos, standards do time. |

#### 🏛 Arquitetura & Domínio

| Skill | Escopo |
|---|---|
| `/sdlc-kit:c4` | Diagramas C4 em Mermaid — 3 níveis. |
| `/sdlc-kit:api` | Contratos de API em 4 estilos: `rest`, `async`, `grpc`, `webhook`. |
| `/sdlc-kit:domain` | Artefatos DDD — 5 kinds. |
| `/sdlc-kit:design-system` | 3 kinds: `token`, `component`, `pattern`. |

#### 🚨 Operações & Análise

| Skill | Escopo |
|---|---|
| `/sdlc-kit:incident` | Post-mortem. 4 estados com timestamps auto-preenchidos. Severidade `SEV1..SEV4`. |
| `/sdlc-kit:trace` | **Read-only** — matriz de rastreabilidade PRD → spec → review. |
| `/sdlc-kit:impact` | **Read-only** — BFS sobre wikilinks. Use antes de deprecar algo. |

### Quando instalar

✅ **Instale se** você:
- adota DDD / Clean Architecture a sério
- se importa com SLOs, SLIs, requisitos não-funcionais como artefatos versionados
- precisa de matrizes de rastreabilidade para auditoria / compliance (LGPD, SOC2)
- quer post-mortems com timeline auto-preenchido
- precisa avaliar raio de impacto antes de refatorações

❌ **Pule se** você só precisa de PRDs, specs e code reviews — o core cobre isso sozinho.

### Links

- Plugin core (obrigatório): [`sdlc-kit@sdlc-kit`](../core/README.md)
- Repo principal: [`vellus-ai/sdlc-kit`](https://github.com/vellus-ai/sdlc-kit)

[MIT](../../LICENSE) © 2026 [Vellus](https://vellus.tech/)
