# Privacy Policy — SDLC Kit

**Effective date:** 2026-04-19
**Maintainer:** Vellus · milton.antonio.jr@gmail.com
**Website:** https://vellus.tech/
**Repository:** https://github.com/vellus-ai/sdlc-kit

> 📖 **Also available in [Português (Brasil)](#política-de-privacidade--português-brasil) below.**

---

## What this plugin does with your data

**Nothing leaves your machine.** SDLC Kit is a local-first plugin:

- Reads and writes Markdown files inside the `.sdlc/` folder of the Git repository where you invoke it.
- Maintains a local SQLite tracker at `.sdlc-kit/db.sqlite` (same repo).
- Renders a dashboard from those local files via the browser's File System Access API. No upload, no remote rendering.

## What this plugin does NOT do

- ❌ No telemetry, analytics, or "phone-home" calls.
- ❌ No HTTP requests to Vellus servers, Anthropic servers, or any third party.
- ❌ No collection of user names, IPs, project contents, or usage data.
- ❌ No background processes, no persistent daemons.

## Third-party data flows

- The PostToolUse hook only emits an `additionalContext` cue back into Claude Code's local process — Claude Code itself decides whether/how to send that to Anthropic per its own privacy policy.
- The optional `gh` CLI integration (used by `/sdlc-kit:worktree` to read PR status) talks to GitHub on your behalf, governed by GitHub's own privacy policy and your local `gh auth` credentials.

## Your data, your responsibility

The `.sdlc/` vault is part of your Git repository. If you push it to a public remote, anyone with access sees it. The plugin makes no effort to mask, redact, or sandbox any content you write into it.

## Contact

Privacy questions or data requests:
**[milton.antonio.jr@gmail.com](mailto:milton.antonio.jr@gmail.com)**

## Changes

This policy is versioned in the repo. Updates appear in the commit log and in the project [`CHANGELOG.md`](./CHANGELOG.md).

---
---

## Política de Privacidade — Português (Brasil)

**Data de vigência:** 2026-04-19
**Mantenedor:** Vellus · milton.antonio.jr@gmail.com
**Site:** https://vellus.tech/
**Repositório:** https://github.com/vellus-ai/sdlc-kit

### O que este plugin faz com seus dados

**Nada sai da sua máquina.** O SDLC Kit é local-first:

- Lê e escreve arquivos Markdown dentro da pasta `.sdlc/` do repositório Git onde você o invoca.
- Mantém um tracker SQLite local em `.sdlc-kit/db.sqlite` (mesmo repo).
- Renderiza um dashboard a partir desses arquivos locais via File System Access API do navegador. Sem upload, sem renderização remota.

### O que este plugin NÃO faz

- ❌ Sem telemetria, analytics ou chamadas "phone-home".
- ❌ Sem requisições HTTP para servidores da Vellus, Anthropic ou qualquer terceiro.
- ❌ Sem coleta de nomes de usuário, IPs, conteúdo de projetos ou dados de uso.
- ❌ Sem processos em background, sem daemons persistentes.

### Fluxos de terceiros

- O hook PostToolUse apenas emite um `additionalContext` para o processo local do Claude Code — o próprio Claude Code decide se/como enviar isso à Anthropic conforme a política de privacidade dele.
- A integração opcional com a CLI `gh` (usada pelo `/sdlc-kit:worktree` para ler status de PRs) conversa com o GitHub em seu nome, regida pela política do GitHub e pelas suas credenciais `gh auth` locais.

### Seus dados, sua responsabilidade

O vault `.sdlc/` faz parte do seu repositório Git. Se você o publicar em um remoto público, qualquer pessoa com acesso vê o conteúdo. O plugin não mascara, redige nem isola o que você escreve ali.

### Contato

Dúvidas de privacidade ou pedidos de dados:
**[milton.antonio.jr@gmail.com](mailto:milton.antonio.jr@gmail.com)**

### Mudanças

Esta política é versionada no repo. Atualizações aparecem no histórico de commits e no [`CHANGELOG.md`](./CHANGELOG.md).

## Compliance / Conformidade

- **LGPD (Lei nº 13.709/2018)** — O plugin não coleta nem processa dados pessoais de usuários. Não se aplica a maior parte da lei; para dados que você escreva no vault, você é o controlador.
- **GDPR** — Same: no personal data collected by the plugin itself; users writing into the vault are the data controllers.
