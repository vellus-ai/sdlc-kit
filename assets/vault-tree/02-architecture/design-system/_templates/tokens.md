---
title: "Design Tokens — {{PROJECT_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# Design Tokens: {{PROJECT_NAME}}

> Variáveis de design que definem a identidade visual do produto.
> Fonte de verdade para cores, tipografia, espaçamento e elevação.

## Cores

### Brand

| Token | Valor | Uso |
|-------|-------|-----|
| `--color-brand-primary` | `#0066CC` | CTAs, links ativos |
| `--color-brand-secondary` | `#004499` | Hover states |
| `--color-brand-accent` | `#FF6B00` | Destaques, badges |

### Semantic

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--color-bg-surface` | `#FFFFFF` | `#1A1A1A` | Fundo de cards |
| `--color-bg-page` | `#F5F5F5` | `#0D0D0D` | Fundo de página |
| `--color-text-primary` | `#1A1A1A` | `#F0F0F0` | Texto principal |
| `--color-text-secondary` | `#666666` | `#AAAAAA` | Texto secundário |
| `--color-border` | `#E0E0E0` | `#333333` | Bordas |

### Feedback

| Token | Valor | Uso |
|-------|-------|-----|
| `--color-success` | `#28A745` | Confirmações |
| `--color-warning` | `#FFC107` | Alertas |
| `--color-error` | `#DC3545` | Erros |
| `--color-info` | `#17A2B8` | Informações |

## Tipografia

| Token | Valor |
|-------|-------|
| `--font-family-base` | `'Inter', sans-serif` |
| `--font-family-mono` | `'JetBrains Mono', monospace` |
| `--font-size-xs` | `0.75rem (12px)` |
| `--font-size-sm` | `0.875rem (14px)` |
| `--font-size-base` | `1rem (16px)` |
| `--font-size-lg` | `1.125rem (18px)` |
| `--font-size-xl` | `1.25rem (20px)` |
| `--font-size-2xl` | `1.5rem (24px)` |
| `--font-weight-normal` | `400` |
| `--font-weight-medium` | `500` |
| `--font-weight-semibold` | `600` |
| `--font-weight-bold` | `700` |

## Espaçamento

| Token | Valor | Uso |
|-------|-------|-----|
| `--space-1` | `0.25rem (4px)` | Micro gaps |
| `--space-2` | `0.5rem (8px)` | Compact |
| `--space-3` | `0.75rem (12px)` | Tight |
| `--space-4` | `1rem (16px)` | Base |
| `--space-6` | `1.5rem (24px)` | Medium |
| `--space-8` | `2rem (32px)` | Large |
| `--space-12` | `3rem (48px)` | XL |
| `--space-16` | `4rem (64px)` | Section |

## Bordas e Raios

| Token | Valor |
|-------|-------|
| `--radius-sm` | `4px` |
| `--radius-md` | `8px` |
| `--radius-lg` | `12px` |
| `--radius-full` | `9999px` |
| `--border-width` | `1px` |

## Sombras

| Token | Valor |
|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.10)` |

## Referências

- [[components]] — Componentes que usam estes tokens
- [[patterns]] — Padrões de composição
- [[_INDEX]]
