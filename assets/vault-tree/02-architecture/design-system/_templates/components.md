---
title: "Component Library — {{PROJECT_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# Biblioteca de Componentes: {{PROJECT_NAME}}

> Catálogo de componentes UI reutilizáveis do projeto.
> Cada componente referencia seus tokens e variantes.

## Fundamentos

### Button

**Variantes:** `primary` | `secondary` | `ghost` | `destructive`
**Tamanhos:** `sm` | `md` | `lg`
**Estados:** default | hover | focus | disabled | loading

```tsx
<Button variant="primary" size="md" onClick={handler}>
  Confirmar
</Button>
```

**Tokens utilizados:**
- `--color-brand-primary`, `--space-4`, `--radius-md`, `--font-size-base`

---

### Input

**Variantes:** `text` | `email` | `password` | `number` | `search`
**Estados:** default | focus | error | disabled

```tsx
<Input
  label="Email"
  type="email"
  error="Email inválido"
  value={value}
  onChange={handler}
/>
```

---

### Badge

**Variantes:** `default` | `success` | `warning` | `error` | `info`

```tsx
<Badge variant="success">Ativo</Badge>
```

---

## Layout

### Card

```tsx
<Card>
  <Card.Header title="Título" />
  <Card.Body>Conteúdo</Card.Body>
  <Card.Footer>Ações</Card.Footer>
</Card>
```

### Modal

**Props:** `isOpen`, `onClose`, `title`, `size` (`sm` | `md` | `lg` | `full`)

---

## Feedback

### Toast / Notification

**Posições:** `top-right` | `top-center` | `bottom-right`
**Durações:** `auto (3s)` | `persistent`

---

### Skeleton Loader

```tsx
<Skeleton width="100%" height={20} borderRadius={4} />
```

---

## Formulários

### Form

Wrapper com validação integrada (React Hook Form / Zod).

```tsx
<Form schema={schema} onSubmit={handler}>
  <Form.Field name="email" />
  <Form.Submit>Salvar</Form.Submit>
</Form>
```

## Referências

- [[tokens]] — Design tokens utilizados
- [[patterns]] — Padrões de composição de componentes
- [[_INDEX]]
