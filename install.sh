#!/usr/bin/env bash
# SDLC Kit — instalador one-liner
# Uso: curl -fsSL https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/vellus-ai/sdlc-kit.git"
INSTALL_DIR="${SDLC_KIT_DIR:-$HOME/.claude/plugins/sdlc-kit}"
BOLD="\033[1m"; RESET="\033[0m"; GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"

info()    { echo -e "${BOLD}[sdlc-kit]${RESET} $*"; }
success() { echo -e "${GREEN}${BOLD}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}${BOLD}!${RESET} $*"; }
error()   { echo -e "${RED}${BOLD}✗${RESET} $*" >&2; exit 1; }

# ── Pré-requisitos ──────────────────────────────────────────────────────────
info "Verificando pré-requisitos..."

command -v python3 >/dev/null || error "Python 3 não encontrado. Instale Python 3.11+: https://python.org"
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" \
  || error "Python $PY_VERSION encontrado, mas 3.11+ é necessário."
success "Python $PY_VERSION"

command -v git >/dev/null || error "git não encontrado. Instale git: https://git-scm.com"
success "git $(git --version | awk '{print $3}')"

command -v claude >/dev/null || warn "claude CLI não encontrado — instale o Claude Code para usar as skills."

# ── Instalar / atualizar ─────────────────────────────────────────────────────
if [[ -d "$INSTALL_DIR/.git" ]]; then
  info "Atualizando instalação existente em $INSTALL_DIR..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  info "Clonando repositório em $INSTALL_DIR..."
  git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi
success "Repositório em $INSTALL_DIR"

# ── Instalar pacote Python ───────────────────────────────────────────────────
info "Instalando pacote Python..."
python3 -m pip install -e "$INSTALL_DIR" --quiet
python3 -m pip install "pyyaml>=6" --quiet 2>/dev/null && success "pyyaml instalado" || warn "pyyaml não instalado (opcional)"

# Adicionar diretório de scripts Python ao PATH desta sessão
PY_SCRIPTS=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || true)
[[ -n "$PY_SCRIPTS" && ":$PATH:" != *":$PY_SCRIPTS:"* ]] && export PATH="$PY_SCRIPTS:$PATH"
success "sdlc-kit instalado"

# ── Inicializar banco de dados ───────────────────────────────────────────────
info "Inicializando banco de dados..."
# Usa python3 -m para contornar problemas de PATH
PYTHONPATH="$INSTALL_DIR" python3 -m core.cli init-db \
  && success "Banco de dados inicializado" \
  || warn "init-db falhou — execute manualmente: python3 -m core.cli init-db"

# ── Registrar plugin no Claude Code ─────────────────────────────────────────
if command -v claude >/dev/null; then
  info "Registrando plugin no Claude Code..."
  claude plugin install "$INSTALL_DIR" && success "Plugin registrado"
else
  warn "Claude Code não encontrado. Quando instalado, execute:"
  echo "    claude plugin install $INSTALL_DIR"
fi

echo ""
echo -e "${GREEN}${BOLD}SDLC Kit instalado com sucesso!${RESET}"
echo ""
echo "  Em qualquer projeto Git, abra o Claude Code e execute:"
echo -e "  ${BOLD}/sdlc-kit:init${RESET}"
echo ""
