# Cleanup v0.4.0 — handoff para próxima sessão

> **TRANSITÓRIO** — apague este arquivo ao final do cleanup (parte da
> tarefa). Existe só para documentar o estado pendente entre sessões.

## Contexto (em 5 linhas)

`origin/main` está em **commit `f38c9bc`** com a v0.4.0 split + slim quase
inteira aplicada, mas o `git stash` que tentou isolar o PRIVACY.md
reverteu os ajustes nos arquivos de teste. Resultado: o repo **não roda
pytest**, `pip install -e .` ainda falha em CI, e a tag `v0.4.0` não foi
criada. Esta sessão deixou tudo o resto em ordem (audit_registry verde,
PRIVACY.md publicado, hotfix de pyproject já no main, plugins/ com 22
skills + assets/ + hooks/ + core/ duplicado).

## Estado verificado em `f38c9bc`

✅ `plugins/core/` com `assets/`, `hooks/`, `core/`, `skills/` (11)
✅ `plugins/extended/` com `core/`, `skills/` (11)
✅ `core/` na raiz (canonical, pip install)
✅ `pyproject.toml` em `0.4.0` + `packages = ["core"]`
✅ `scripts/audit_registry.py` aponta para `plugins/core/`
✅ `marketplace.json` declara 2 plugins
✅ `PRIVACY.md` no main (URL viva para Anthropic)
❌ `tests/_skill_helpers.py` ainda diz `REPO_ROOT/"skills"` e `REPO_ROOT/"assets"`
❌ `tests/test_init_scaffold.py:21-22` paths antigos
❌ `tests/test_init_detect.py:19` path antigo
❌ `tests/test_hook_post_vault_write.py:12` path antigo
❌ `tests/test_frontmatter.py:237` path antigo
❌ CHANGELOG ainda em `[Unreleased]` — não migrou para `[0.4.0]`
❌ `skills/sdlc-prd/` (vazio, lock liberou) ainda no root
❌ `scripts/split_plugins.py` obsoleto (já cumpriu papel)
⚠️ 4 SKILL.md ainda longos: `sdlc-init` (281), `sdlc-sync` (193), `sdlc-status`
   (132), `sdlc-dash` (225). Opcional para v0.4.1.

## Passo-a-passo (copie e cole em ordem)

```bash
cd C:/workspace/plugin/sdlc-kit
git status --short | head -3                     # esperado: limpo

# 1. Cleanup do skills/sdlc-prd vazio (lock já liberou após sessão anterior)
rm -rf skills

# 2. Atualizar paths nos testes — _skill_helpers.py é o ponto crítico
```

Edite `tests/_skill_helpers.py` (linhas 24-27):

```python
# DE:
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
VAULT_TREE = REPO_ROOT / "assets" / "vault-tree"
TESTS_DIR = Path(__file__).resolve().parent

# PARA:
REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
CORE_PLUGIN = PLUGINS_ROOT / "core"
EXTENDED_PLUGIN = PLUGINS_ROOT / "extended"
# Both plugins expose `skills/`. Helpers below resolve a script path by
# searching both, so existing tests passing `"sdlc-prd/scripts/prd.py"` keep
# working without knowing which plugin owns the skill.
SKILLS_DIRS = (CORE_PLUGIN / "skills", EXTENDED_PLUGIN / "skills")
# Templates and dashboard live with the core plugin (extended doesn't ship them).
VAULT_TREE = CORE_PLUGIN / "assets" / "vault-tree"
TESTS_DIR = Path(__file__).resolve().parent
```

E a função `run_script` (linhas ~86-101):

```python
# Substituir o corpo:
def _resolve_script(script_rel: str) -> Path:
    """Find a skill script in either plugin (core or extended)."""
    for skills_dir in SKILLS_DIRS:
        candidate = skills_dir / script_rel
        if candidate.exists():
            return candidate
    raise AssertionError(f"skill script missing: {script_rel} (searched {SKILLS_DIRS})")


def run_script(script_rel: str, args: list[str]) -> subprocess.CompletedProcess:
    """Invoke a skill script (auto-resolves between core/extended plugins)."""
    script = _resolve_script(script_rel)
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_subprocess_env(),
    )
```

```bash
# 3. Patch dos demais arquivos de teste (sed in-place via Python para evitar dor com sed em Windows)
py -c "
from pathlib import Path
import re

patches = {
    'tests/test_init_scaffold.py': [
        ('REPO_ROOT / \"skills\" / \"sdlc-init\" / \"scripts\" / \"scaffold.py\"',
         'REPO_ROOT / \"plugins\" / \"core\" / \"skills\" / \"sdlc-init\" / \"scripts\" / \"scaffold.py\"'),
        ('REPO_ROOT / \"assets\" / \"vault-tree\"',
         'REPO_ROOT / \"plugins\" / \"core\" / \"assets\" / \"vault-tree\"'),
    ],
    'tests/test_init_detect.py': [
        ('REPO_ROOT / \"skills\" / \"sdlc-init\" / \"scripts\" / \"detect.py\"',
         'REPO_ROOT / \"plugins\" / \"core\" / \"skills\" / \"sdlc-init\" / \"scripts\" / \"detect.py\"'),
    ],
    'tests/test_hook_post_vault_write.py': [
        ('PLUGIN_ROOT / \"hooks\" / \"post-vault-write.py\"',
         'PLUGIN_ROOT / \"plugins\" / \"core\" / \"hooks\" / \"post-vault-write.py\"'),
    ],
    'tests/test_frontmatter.py': [
        ('repo_root / \"assets\" / \"vault-tree\" /',
         'repo_root / \"plugins\" / \"core\" / \"assets\" / \"vault-tree\" /'),
    ],
}
for rel, pairs in patches.items():
    p = Path(rel)
    src = p.read_text(encoding='utf-8')
    for old, new in pairs:
        if old not in src:
            print(f'MISS: {rel}: {old[:60]}...')
            continue
        src = src.replace(old, new, 1)
    p.write_text(src, encoding='utf-8')
    print(f'OK  : {rel}')
"

# 4. Confirmar que core/ root e plugins/{core,extended}/core/ estão em sync
py -c "
import filecmp
from pathlib import Path
root = Path('core')
for plugin in ('plugins/core/core', 'plugins/extended/core'):
    cmp = filecmp.dircmp(root, plugin)
    if cmp.diff_files or cmp.left_only or cmp.right_only:
        print(f'DIVERGE: {plugin}')
        print(f'  diff:      {cmp.diff_files}')
        print(f'  root_only: {cmp.left_only}')
        print(f'  plug_only: {cmp.right_only}')
    else:
        print(f'OK     : {plugin}')
"
# Se DIVERGE: cp -r core/* plugins/core/core/  &&  cp -r core/* plugins/extended/core/

# 5. Suite completa
py -m pytest -q -p no:randomly --tb=short --no-header 2>&1 | tail -10
# Esperado: 506 passed (ou 505 — sem o test_doc_skill que foi deletado em 0.4.0)

# 6. Audit registry
py scripts/audit_registry.py | head -3
# Esperado: "status": "ok", "missing_in_registry": [], "orphans_in_registry": []

# 7. CHANGELOG: trocar [Unreleased] por [0.4.0] — 2026-04-19
# Use Edit tool: trocar `## [Unreleased]\n\n## [0.3.3]` por
# `## [Unreleased]\n\n## [0.4.0] — 2026-04-19\n\n[CONTEÚDO DO 0.4.0 — copiar do plano abaixo]\n\n## [0.3.3]`

# 8. Deletar split_plugins.py (cumpriu o papel)
git rm scripts/split_plugins.py

# 9. Deletar este próprio arquivo de cleanup
git rm docs/_pending-v0.4.0-cleanup.md

# 10. Commit do cleanup
git add -A
git commit -m "$(cat <<EOF
chore(v0.4.0): cleanup tests + CHANGELOG + remove transient files

- tests/_skill_helpers.py: SKILLS_DIRS tuple resolves scripts from
  either plugin (core/extended); VAULT_TREE points to plugins/core/.
- tests/test_init_scaffold.py, test_init_detect.py,
  test_hook_post_vault_write.py, test_frontmatter.py: paths repointed
  to plugins/core/.
- skills/sdlc-prd/ empty leftover removed.
- scripts/split_plugins.py removed (one-shot refactor cumprido).
- CHANGELOG: [Unreleased] migrated to [0.4.0].

Suite: 505+/506 passing locally. Audit registry green.
EOF
)"
git push origin main

# 11. Aguardar CI verde (matriz 9-way)
gh run list --workflow=ci.yml --limit 1 --json conclusion,databaseId
# Espere até conclusion: success

# 12. Tag v0.4.0
git tag -a v0.4.0 -m "Release v0.4.0 — split into sdlc-kit + sdlc-kit-extended, SKILL.md slim (-81%)"
git push origin v0.4.0

# 13. Verificar release publicada
gh release view v0.4.0 --repo vellus-ai/sdlc-kit
```

## Conteúdo da seção `[0.4.0]` para o CHANGELOG (passo 7)

```markdown
## [0.4.0] — 2026-04-19

### Mudado — split em dois plugins

O plugin monolítico `sdlc-kit` (v0.3.x, 23 skills) foi dividido em dois
plugins compostos no mesmo marketplace:

- **`sdlc-kit`** (core, **11 skills**): ciclo de entrega diário — `init`,
  `sync`, `status`, `dash`, `prd`, `adr`, `spec`, `task`, `worktree`,
  `review`, `retro`. Carrega o hook PostToolUse, `assets/vault-tree/` e
  a biblioteca `core/`.
- **`sdlc-kit-extended`** (**11 skills opcionais**): governança (`trd`,
  `epic`, `milestone`, `steer`), arquitetura/domínio (`c4`, `api`,
  `domain`, `design-system`), ops/análise (`incident`, `trace`,
  `impact`).

Ambos plugins vivem no mesmo monorepo. Instalação:

```
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit            # core
/plugin install sdlc-kit-extended@sdlc-kit   # opcional
```

### Removido

- **Skill `/sdlc-kit:doc`** deletada (fallback genérico que não
  implementava o contrato canônico).
- **23 → 22 skills** (11 core + 11 extended).

### Adicionado

- `plugins/core/` e `plugins/extended/` com `.claude-plugin/plugin.json`
  próprios.
- `marketplace.json` declara os 2 plugins.
- `PRIVACY.md` no root para a submissão do marketplace oficial Anthropic.
- READMEs caprichados em raiz, `plugins/core/` e `plugins/extended/`.
- 18 `references/flow.md` carregados sob demanda — Flow / Pre-approval
  checklist / Examples / Output contract movidos pra lá.

### Melhorado — custo cognitivo do plugin

- **SKILL.md total: ~5818 → ~1090 linhas (-81%).** Cada skill agora tem
  ≤ 72 linhas (descrição + when-to-invoke + pointer). Triggers pt-BR
  duplicados removidos das `description:`. Reduz o token budget do
  Claude Code ao carregar o plugin.

### Corrigido

- `pyproject.toml` em `0.4.0` + `packages = ["core"]` (era stale).
- `scripts/audit_registry.py` aponta para `plugins/core/...`.
- `tests/_skill_helpers.SKILLS_DIRS` resolve scripts dinamicamente em
  ambos os plugins (transparente para os tests existentes).
- 5 referências mortas a `/sdlc-kit:doc` limpas em README/CLAUDE.md.tpl.

### Pendente (follow-ups para v0.4.1+)

- 4 SKILL.md de utilitários ainda longos (`sdlc-init` 281, `sdlc-sync`
  193, `sdlc-status` 132, `sdlc-dash` 225) — slim opcional em PR
  separada.
- `core/` duplicada em 3 lugares (root canonical + 2 plugins) — extrair
  para PyPI numa próxima major.
- Namespaces `/sdlc-kit:util:*` (sugestão Boris) ficam para v0.5.0.
```

## Critérios de aceitação

- [ ] `py -m pytest -q -p no:randomly` passa (≥ 505 testes verdes)
- [ ] `py scripts/audit_registry.py` retorna `status: ok`
- [ ] `git status` limpo
- [ ] CI matriz 9-way verde no `main`
- [ ] Tag `v0.4.0` publicada no GitHub
- [ ] Release notes extraídas automaticamente da seção `[0.4.0]`
- [ ] Este arquivo (`docs/_pending-v0.4.0-cleanup.md`) deletado no commit

## Plano-B se algo quebrar

- **`pip install -e .` falha**: confirmar `core/` na raiz (cp de
  `plugins/core/core/` se necessário). Validar `[tool.setuptools].packages`.
- **Tests falham com "module not found 'core'"**: idem ao acima.
- **CI 1+ jobs vermelhos**: aplicar a mesma estratégia incremental
  v0.3.1/0.3.2/0.3.3 — hotfix focado, push, monitor, repeat até verde.
- **Audit registry quebra**: reverter `audit_registry.py` para pegar de
  `plugins/core/...` (já está). Se `assets/` estiver no root também,
  remover (foi movido).
