# SDLC Kit — instalador one-liner (Windows PowerShell)
# Uso: irm https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.ps1 | iex
#Requires -Version 5.1
$ErrorActionPreference = "Continue"   # não abortar em erros não-fatais

$Repo       = "https://github.com/vellus-ai/sdlc-kit.git"
$InstallDir = if ($env:SDLC_KIT_DIR) { $env:SDLC_KIT_DIR } else { "$env:USERPROFILE\.claude\plugins\sdlc-kit" }

function Write-Step { Write-Host "[sdlc-kit] $args" -ForegroundColor Cyan }
function Write-Ok   { Write-Host "  + $args" -ForegroundColor Green }
function Write-Warn { Write-Host "  ! $args" -ForegroundColor Yellow }
function Write-Fail { Write-Host "  x $args" -ForegroundColor Red; exit 1 }

# ── Pré-requisitos ──────────────────────────────────────────────────────────
Write-Step "Verificando pré-requisitos..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Fail "Python não encontrado. Instale Python 3.11+: https://python.org"
}
$pyVer = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
& python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if ($LASTEXITCODE -ne 0) { Write-Fail "Python $pyVer encontrado, mas 3.11+ é necessário." }
Write-Ok "Python $pyVer"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fail "git não encontrado. Instale git: https://git-scm.com"
}
Write-Ok "git $(git --version)"

$claudeOk = $null -ne (Get-Command claude -ErrorAction SilentlyContinue)
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
& python -m pip install -e $InstallDir --quiet --no-warn-script-location
& python -m pip install "pyyaml>=6" --quiet --no-warn-script-location 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "pyyaml instalado" } else { Write-Warn "pyyaml não instalado (opcional)" }

# Adicionar o diretório de scripts Python ao PATH desta sessão (evita "não reconhecido")
$pythonScripts = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
if ($pythonScripts -and (Test-Path $pythonScripts)) {
    $env:PATH = "$pythonScripts;$env:PATH"
    Write-Ok "sdlc-kit instalado (scripts em $pythonScripts)"
} else {
    Write-Ok "sdlc-kit instalado"
}

# ── Registrar plugin no Claude Code ─────────────────────────────────────────
$SettingsFile = "$env:USERPROFILE\.claude\settings.json"
Write-Step "Registrando plugin em $SettingsFile..."
if (Test-Path $SettingsFile) {
    $pyScript = @'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    s = json.load(f)
s.setdefault("extraKnownMarketplaces", {})
s["extraKnownMarketplaces"].setdefault("sdlc-kit", {
    "source": {"source": "github", "repo": "vellus-ai/sdlc-kit"}
})
s.setdefault("enabledPlugins", {})
s["enabledPlugins"]["sdlc-kit@sdlc-kit"] = True
with open(path, "w", encoding="utf-8") as f:
    json.dump(s, f, indent=2)
print("ok")
'@
    $result = & python -c $pyScript $SettingsFile 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Ok "Plugin registrado (sdlc-kit@sdlc-kit)" }
    else { Write-Warn "Falha ao atualizar settings.json: $result" }
} else {
    Write-Warn "$SettingsFile não encontrado — abra o Claude Code uma vez e reexecute o instalador."
}

Write-Host ""
Write-Host "SDLC Kit instalado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "  Proximos passos:"
Write-Host "  1. Abra o Claude Code em qualquer projeto Git"
Write-Host "  2. Execute: /sdlc-kit:init"
Write-Host "     (isso cria o vault .sdlc/ e inicializa tudo automaticamente)"
Write-Host ""
