# SDLC Kit — instalador one-liner (Windows PowerShell)
# Uso: irm https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.ps1 | iex
#Requires -Version 5.1

# IMPORTANTE: todo o corpo é envolto em um script block invocado com & {}.
# Isso garante que `return` encerre apenas esse bloco — nunca o terminal do
# usuário quando executado via `irm | iex`.
& {
    $ErrorActionPreference = "Continue"

    $Repo       = "https://github.com/vellus-ai/sdlc-kit.git"
    $InstallDir = if ($env:SDLC_KIT_DIR) { $env:SDLC_KIT_DIR } else { "$env:USERPROFILE\.claude\plugins\sdlc-kit" }

    function Write-Step { param([string]$Msg) Write-Host "[sdlc-kit] $Msg" -ForegroundColor Cyan }
    function Write-Ok   { param([string]$Msg) Write-Host "  + $Msg" -ForegroundColor Green }
    function Write-Warn { param([string]$Msg) Write-Host "  ! $Msg" -ForegroundColor Yellow }
    function Write-Err  { param([string]$Msg) Write-Host "  x $Msg" -ForegroundColor Red }

    # ── Pré-requisitos ────────────────────────────────────────────────────
    Write-Step "Verificando pré-requisitos..."

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Err "Python não encontrado. Instale Python 3.11+: https://python.org"
        return
    }
    $pyVer = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    & python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Python $pyVer encontrado, mas 3.11+ é necessário."
        return
    }
    Write-Ok "Python $pyVer"

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Err "git não encontrado. Instale git: https://git-scm.com"
        return
    }
    Write-Ok "git $((git --version) -replace '^git version ', '')"

    $claudeOk = $null -ne (Get-Command claude -ErrorAction SilentlyContinue)
    if (-not $claudeOk) { Write-Warn "claude CLI não encontrado — instale o Claude Code para usar as skills." }

    # ── Instalar / atualizar ──────────────────────────────────────────────
    if (Test-Path "$InstallDir\.git") {
        Write-Step "Atualizando instalação existente em $InstallDir..."
        git -C $InstallDir pull --ff-only 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Warn "git pull falhou — continuando com a versão local." }
    } else {
        Write-Step "Clonando repositório em $InstallDir..."
        $parent = Split-Path $InstallDir
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        git clone --depth 1 $Repo $InstallDir 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Falha ao clonar repositório — verifique acesso à internet."
            return
        }
    }
    Write-Ok "Repositório em $InstallDir"

    # ── Instalar pacote Python ────────────────────────────────────────────
    Write-Step "Instalando pacote Python..."
    & python -m pip install -e $InstallDir --quiet --no-warn-script-location 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { Write-Warn "pip install do sdlc-kit falhou — algumas skills podem não funcionar." }
    & python -m pip install "pyyaml>=6" --quiet --no-warn-script-location 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Ok "pyyaml instalado" } else { Write-Warn "pyyaml não instalado (opcional)" }

    $pythonScripts = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>$null
    if ($pythonScripts -and (Test-Path $pythonScripts)) {
        $env:PATH = "$pythonScripts;$env:PATH"
        Write-Ok "sdlc-kit instalado (scripts em $pythonScripts)"
    } else {
        Write-Ok "sdlc-kit instalado"
    }

    # ── Registrar plugin no Claude Code ───────────────────────────────────
    $ClaudeDir    = "$env:USERPROFILE\.claude"
    $SettingsFile = "$ClaudeDir\settings.json"
    Write-Step "Registrando plugin em $SettingsFile..."

    if (-not (Test-Path $ClaudeDir)) {
        New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
    }
    if (-not (Test-Path $SettingsFile)) {
        '{}' | Set-Content -Path $SettingsFile -Encoding UTF8
        Write-Warn "settings.json não existia — criado vazio."
    }

    $pyScript = @'
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as f:
        s = json.load(f)
except Exception:
    s = {}
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
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Plugin registrado (sdlc-kit@sdlc-kit)"
    } else {
        Write-Warn "Falha ao atualizar settings.json: $result"
    }

    Write-Host ""
    Write-Host "SDLC Kit instalado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Proximos passos:"
    Write-Host "  1. Reinicie o Claude Code (feche e abra novamente)"
    Write-Host "  2. Abra o Claude Code em qualquer projeto Git"
    Write-Host "  3. Execute: /sdlc-kit:init"
    Write-Host "     (isso cria o vault .sdlc/ e inicializa tudo automaticamente)"
    Write-Host ""
}
