# SDLC Kit — instalador one-liner (Windows PowerShell)
# Uso: irm https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.ps1 | iex
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Repo        = "https://github.com/vellus-ai/sdlc-kit.git"
$InstallDir  = if ($env:SDLC_KIT_DIR) { $env:SDLC_KIT_DIR } else { "$env:USERPROFILE\.claude\plugins\sdlc-kit" }

function Write-Step  { Write-Host "[sdlc-kit] $args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "  + $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "  ! $args" -ForegroundColor Yellow }
function Write-Fail  { Write-Host "  x $args" -ForegroundColor Red; exit 1 }

# ── Pré-requisitos ──────────────────────────────────────────────────────────
Write-Step "Verificando pré-requisitos..."

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Fail "Python não encontrado. Instale Python 3.11+: https://python.org" }
$pyVer = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$pyOk  = & python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Fail "Python $pyVer encontrado, mas 3.11+ é necessário." }
Write-Ok "Python $pyVer"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fail "git não encontrado. Instale git: https://git-scm.com"
}
Write-Ok "git $(git --version)"

$claudeOk = (Get-Command claude -ErrorAction SilentlyContinue) -ne $null
if (-not $claudeOk) { Write-Warn "claude CLI não encontrado — instale o Claude Code para usar as skills." }

# ── Instalar / atualizar ─────────────────────────────────────────────────────
if (Test-Path "$InstallDir\.git") {
    Write-Step "Atualizando instalação existente em $InstallDir..."
    git -C $InstallDir pull --ff-only
} else {
    Write-Step "Clonando repositório em $InstallDir..."
    New-Item -ItemType Directory -Force -Path (Split-Path $InstallDir) | Out-Null
    git clone --depth 1 $Repo $InstallDir
}
Write-Ok "Repositório em $InstallDir"

# ── Instalar pacote Python ───────────────────────────────────────────────────
Write-Step "Instalando pacote Python..."
& python -m pip install -e $InstallDir --quiet
& python -m pip install "pyyaml>=6" --quiet 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "pyyaml instalado" } else { Write-Warn "pyyaml não instalado (opcional)" }
Write-Ok "sdlc-kit instalado"

# ── Inicializar banco de dados ───────────────────────────────────────────────
Write-Step "Inicializando banco de dados..."
& sdlc-kit init-db 2>$null
if ($LASTEXITCODE -ne 0) { Write-Warn "init-db falhou — execute 'sdlc-kit init-db' manualmente no seu projeto" }

# ── Registrar plugin no Claude Code ─────────────────────────────────────────
if ($claudeOk) {
    Write-Step "Registrando plugin no Claude Code..."
    & claude plugin install $InstallDir
    Write-Ok "Plugin registrado"
} else {
    Write-Warn "Claude Code não encontrado. Quando instalado, execute:"
    Write-Host "    claude plugin install $InstallDir"
}

Write-Host ""
Write-Host "SDLC Kit instalado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "  Em qualquer projeto Git, abra o Claude Code e execute:"
Write-Host "  /sdlc-kit:init"
Write-Host ""
