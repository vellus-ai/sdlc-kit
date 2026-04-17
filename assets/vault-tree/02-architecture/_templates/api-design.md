---
title: "API Design — {{API_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# API Design: {{API_NAME}}

## Visão Geral

- **Base URL:** `https://api.example.com/v1`
- **Autenticação:** Bearer token (JWT)
- **Formato:** JSON (application/json)
- **Versionamento:** URL path (`/v1/`, `/v2/`)

## Recursos

### `GET /{{resource}}`

**Descrição:** Lista recursos paginados.

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `page` | integer | não | Número da página (padrão: 1) |
| `limit` | integer | não | Itens por página (padrão: 20, máx: 100) |

**Response 200:**

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 0
  }
}
```

### `POST /{{resource}}`

**Descrição:** Cria novo recurso.

**Request Body:**

```json
{
  "field": "value"
}
```

**Response 201:**

```json
{
  "id": "uuid",
  "field": "value",
  "created_at": "ISO8601"
}
```

### `GET /{{resource}}/{id}`

**Response 200:** Objeto completo.
**Response 404:** `{"error": "not_found", "message": "Resource not found"}`

### `PATCH /{{resource}}/{id}`

**Descrição:** Atualização parcial (campos enviados sobrescrevem).

### `DELETE /{{resource}}/{id}`

**Response 204:** Sem corpo.

## Erros

| Código HTTP | Código de Erro | Descrição |
|-------------|---------------|-----------|
| 400 | `validation_error` | Payload inválido |
| 401 | `unauthorized` | Token ausente ou inválido |
| 403 | `forbidden` | Sem permissão para o recurso |
| 404 | `not_found` | Recurso não encontrado |
| 409 | `conflict` | Conflito de estado |
| 422 | `unprocessable` | Regra de negócio violada |
| 429 | `rate_limited` | Limite de requisições excedido |
| 500 | `internal_error` | Erro interno do servidor |

## Rate Limiting

- Limite: 1000 req/hora por token
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Referências

- [[tech-design]] — Technical Design relacionado
- [[_INDEX]]
