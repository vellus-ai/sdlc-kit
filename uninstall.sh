#!/usr/bin/env bash
# SDLC Kit — desinstalador
# Uso: curl -fsSL https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/uninstall.sh | bash
set -uo pipefail

INSTALL_DIR="${SDLC_KIT_DIR:-$HOME/.claude/plugins/sdlc-kit}"
CACHE_DIR="$HOME/.claude/plugins/cache/sdlc-kit"
SETTINGS_FILE="$HOME/.claude/settings.json"
BOLD="\033[1m"; RESET="\033[0m"; GREEN="\033[32m"; YELLOW="\033[33m"

info()    { echo -e "${BOLD}[sdlc-kit]${RESET} $*"; }
success() { echo -e "  ${GREEN}${BOLD}+${RESET} $*"; }
warn()    { echo -e "  ${YELLOW}${BOLD}!${RESET} $*"; }

info "Desinstalando SDLC Kit..."
echo ""
warn "Os vaults .sdlc/ criados em seus projetos NÃO serão tocados."
echo ""

# ── 1. Remover do settings.json ──────────────────────────────────────────
info "Removendo registro em $SETTINGS_FILE..."
if [[ -f "$SETTINGS_FILE" ]]; then
  python3 - "$SETTINGS_FILE" <<'PY' || true
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as f:
        s = json.load(f)
except Exception:
    sys.exit(0)
changed = False
if s.get("extraKnownMarketplaces", {}).pop("sdlc-kit", None) is not None:
    print("Marketplace 'sdlc-kit' removido")
    changed = True
if s.get("enabledPlugins", {}).pop("sdlc-kit@sdlc-kit", None) is not None:
    print("Plugin 'sdlc-kit@sdlc-kit' desabilitado")
    changed = True
if changed:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
PY
else
  warn "settings.json não encontrado (nada a remover)"
fi

# ── 2. Desinstalar pacote Python ─────────────────────────────────────────
info "Desinstalando pacote Python..."
if python3 -m pip uninstall -y sdlc-kit --quiet 2>/dev/null; then
  success "pacote sdlc-kit removido"
else
  warn "pacote sdlc-kit não estava instalado"
fi

# ── 3. Remover clone do install script ───────────────────────────────────
if [[ -d "$INSTALL_DIR" ]]; then
  info "Removendo $INSTALL_DIR..."
  rm -rf "$INSTALL_DIR"
  [[ ! -d "$INSTALL_DIR" ]] && success "Diretório removido" || warn "Remova manualmente"
fi

# ── 4. Remover cache do Claude Code ──────────────────────────────────────
if [[ -d "$CACHE_DIR" ]]; then
  info "Removendo cache em $CACHE_DIR..."
  rm -rf "$CACHE_DIR"
  [[ ! -d "$CACHE_DIR" ]] && success "Cache removido" || warn "Remova manualmente"
fi

echo ""
echo -e "${GREEN}${BOLD}SDLC Kit desinstalado!${RESET}"
echo ""
echo "  Para aplicar: feche e reabra o Claude Code."
echo "  Seus vaults .sdlc/ nos projetos permanecem intactos."
echo ""
