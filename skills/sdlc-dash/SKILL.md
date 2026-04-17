# sdlc-kit:dash

## Quando invocar

Use `/sdlc-kit:dash` a qualquer momento para abrir o dashboard do vault no browser.

## Fluxo

1. Encontra a raiz do vault pelo marker.json
2. Localiza `dashboard.html` dentro do vault
3. Abre o arquivo no browser padrão do sistema (multiplataforma)
4. Informa o caminho caso a abertura automática não seja possível

## Uso

```
/sdlc-kit:dash
```

Ou com vault explícito:

```
/sdlc-kit:dash --vault-root /caminho/para/.sdlc
```

## Guardrails

- Se o vault não for encontrado, sugere executar `/sdlc-kit:init` primeiro
- Se o browser não abrir automaticamente, exibe o caminho completo do arquivo
- Funciona em Windows (`start`), macOS (`open`) e Linux (`xdg-open`)
