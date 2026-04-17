---
title: "Design Patterns — {{PROJECT_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# Padrões de Design: {{PROJECT_NAME}}

> Padrões de composição, layout e interação reutilizáveis no produto.

## Padrões de Layout

### Page Shell

Estrutura padrão de página autenticada:

```
┌─────────────────────────────────────┐
│           Top Navigation            │
├──────────┬──────────────────────────┤
│ Sidebar  │       Main Content       │
│          │                          │
│          │                          │
└──────────┴──────────────────────────┘
```

**Breakpoints:**
- Mobile (<768px): sidebar oculta (drawer)
- Tablet (768-1024px): sidebar colapsada (ícones)
- Desktop (>1024px): sidebar expandida

---

### Dashboard Layout

```
┌──────────┬──────────┬──────────┐
│  Stat 1  │  Stat 2  │  Stat 3  │
├──────────┴──────────┴──────────┤
│         Chart / Table          │
├────────────────┬───────────────┤
│   Activity     │   Quick       │
│   Feed         │   Actions     │
└────────────────┴───────────────┘
```

## Padrões de Interação

### Loading States

1. **Skeleton:** use para listas e cards ao carregar dados iniciais
2. **Spinner:** use para ações do usuário (submit, delete)
3. **Progress bar:** use para uploads e operações longas

### Empty States

Todo estado vazio deve ter:
- Ícone ilustrativo
- Título descritivo
- Mensagem de orientação
- CTA primário (quando aplicável)

### Error Handling

| Tipo de Erro | Componente | Localização |
|-------------|------------|-------------|
| Validação de campo | Inline error text | Abaixo do campo |
| Erro de API (4xx) | Toast warning | Top-right, 5s |
| Erro de servidor (5xx) | Toast error + retry | Top-right, persistente |
| Erro de rede | Banner | Topo da página |

## Padrões de Formulário

### Validação

- Validação em tempo real apenas após primeiro blur
- Mensagens de erro em português, específicas e acionáveis
- Nunca bloquear submit sem mostrar todos os erros

### Multi-step Form

```
Step 1 → Step 2 → Step 3 → Review → Submit
  ✓        ●        ○        ○        ○
```

## Acessibilidade

- Contraste mínimo: 4.5:1 (texto normal), 3:1 (texto grande)
- Todos os inputs com `aria-label` ou `<label for>`
- Modais com focus trap e `role="dialog"`
- Navegação por teclado em todos os componentes interativos

## Referências

- [[tokens]] — Design tokens
- [[components]] — Componentes do catálogo
- [[_INDEX]]
