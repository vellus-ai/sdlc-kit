# SDLC Kit — instalador one-liner (Windows PowerShell)
# Uso: irm https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.ps1 | iex
#Requires -Version 5.1

# IMPORTANTE: todo o corpo é envolto em & { ... } para que `return` encerre
# apenas este bloco quando executado via `irm | iex` — nunca o terminal do usuário.
& {
    $ErrorActionPreference = "Continue"

    $Repo       = "https://github.com/vellus-ai/sdlc-kit.git"
    $InstallDir = if ($env:SDLC_KIT_DIR) { $env:SDLC_KIT_DIR } else { "$env:USERPROFILE\.claude\plugins\sdlc-kit" }

    function Write-Step { param([string]$Msg) Write-Host "[sdlc-kit] $Msg" -ForegroundColor Cyan }
    function Write-Ok   { param([string]$Msg) Write-Host "  + $Msg" -ForegroundColor Green }
    function Write-Warn { param([string]$Msg) Write-Host "  ! $Msg" -ForegroundColor Yellow }
    function Write-Err  { param([string]$Msg) Write-Host "  x $Msg" -ForegroundColor Red }

    # Invoca comandos nativos silenciando stderr quando só queremos o exit code
    function Invoke-Native {
        param([string]$Exe, [string[]]$Args)
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Exe
        foreach ($a in $Args) { $psi.ArgumentList.Add($a) | Out-Null } 2>$null
        if ($psi.ArgumentList.Count -eq 0) {
            $psi.Arguments = ($Args -join ' ')
        }
        $psi.RedirectStandardError = $true
        $psi.RedirectStandardOutput = $true
        $psi.UseShellExecute = $false
        $p = [System.Diagnostics.Process]::Start($psi)
        $out = $p.StandardOutput.ReadToEnd()
        $err = $p.StandardError.ReadToEnd()
        $p.WaitForExit()
        return @{ ExitCode = $p.ExitCode; StdOut = $out; StdErr = $err }
    }

    # ── Pré-requisitos ────────────────────────────────────────────────────
    Write-Step "Verificando pré-requisitos..."

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Err "Python não encontrado. Instale Python 3.11+: https://python.org"
        return
    }
    $pyVer = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null).Trim()
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
    $gitVer = ((git --version) -replace '^git version ', '').Trim()
    Write-Ok "git $gitVer"

    $claudeOk = $null -ne (Get-Command claude -ErrorAction SilentlyContinue)
    if (-not $claudeOk) { Write-Warn "claude CLI não encontrado — instale o Claude Code para usar as skills." }

    # ── Instalar / atualizar ──────────────────────────────────────────────
    # Git escreve mensagens informativas no stderr; suprimimos com --quiet + 2>$null
    # para manter a saída do instalador limpa.
    if (Test-Path "$InstallDir\.git") {
        Write-Step "Atualizando instalação existente em $InstallDir..."
        $null = git -C $InstallDir pull --ff-only --quiet 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Warn "git pull falhou — usando versão local." }
    } else {
        Write-Step "Clonando repositório em $InstallDir..."
        $parent = Split-Path $InstallDir
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        $null = git clone --depth 1 --quiet $Repo $InstallDir 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Falha ao clonar repositório — verifique acesso à internet."
            return
        }
    }
    Write-Ok "Repositório em $InstallDir"

    # ── Instalar pacote Python ────────────────────────────────────────────
    Write-Step "Instalando pacote Python..."
    $null = & python -m pip install -e $InstallDir --quiet --no-warn-script-location 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Warn "pip install do sdlc-kit falhou — algumas skills podem não funcionar." }
    $null = & python -m pip install "pyyaml>=6" --quiet --no-warn-script-location 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Ok "pyyaml instalado" } else { Write-Warn "pyyaml não instalado (opcional)" }

    $pythonScripts = (& python -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>$null).Trim()
    if ($pythonScripts -and (Test-Path $pythonScripts)) {
        $env:PATH = "$pythonScripts;$env:PATH"
        Write-Ok "sdlc-kit instalado (scripts em $pythonScripts)"
    } else {
        Write-Ok "sdlc-kit instalado"
    }

    # ── Registrar plugin no Claude Code (JSON nativo, sem subprocess) ─────
    $ClaudeDir    = "$env:USERPROFILE\.claude"
    $SettingsFile = "$ClaudeDir\settings.json"
    Write-Step "Registrando plugin em $SettingsFile..."

    if (-not (Test-Path $ClaudeDir)) {
        New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
    }
    # Usamos .NET para I/O para escrever UTF-8 SEM BOM — Get-Content / Set-Content
    # no PowerShell 5.1 adicionam BOM mesmo com -Encoding UTF8, e o Claude Code
    # (Node/JSON.parse) rejeita arquivos com BOM.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

    if (-not (Test-Path $SettingsFile)) {
        [System.IO.File]::WriteAllText($SettingsFile, '{}', $utf8NoBom)
        Write-Warn "settings.json não existia — criado vazio."
    }

    try {
        $raw = [System.IO.File]::ReadAllText($SettingsFile)
        if ([string]::IsNullOrWhiteSpace($raw)) { $raw = '{}' }
        $settings = $raw | ConvertFrom-Json

        # extraKnownMarketplaces
        if (-not $settings.PSObject.Properties['extraKnownMarketplaces']) {
            $settings | Add-Member -NotePropertyName 'extraKnownMarketplaces' -NotePropertyValue ([PSCustomObject]@{})
        }
        if (-not $settings.extraKnownMarketplaces.PSObject.Properties['sdlc-kit']) {
            $mkt = [PSCustomObject]@{
                source = [PSCustomObject]@{
                    source = 'github'
                    repo   = 'vellus-ai/sdlc-kit'
                }
            }
            $settings.extraKnownMarketplaces | Add-Member -NotePropertyName 'sdlc-kit' -NotePropertyValue $mkt
        }

        # enabledPlugins
        if (-not $settings.PSObject.Properties['enabledPlugins']) {
            $settings | Add-Member -NotePropertyName 'enabledPlugins' -NotePropertyValue ([PSCustomObject]@{})
        }
        if ($settings.enabledPlugins.PSObject.Properties['sdlc-kit@sdlc-kit']) {
            $settings.enabledPlugins.'sdlc-kit@sdlc-kit' = $true
        } else {
            $settings.enabledPlugins | Add-Member -NotePropertyName 'sdlc-kit@sdlc-kit' -NotePropertyValue $true
        }

        $json = $settings | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($SettingsFile, $json, $utf8NoBom)
        Write-Ok "Plugin registrado (sdlc-kit@sdlc-kit)"
    } catch {
        Write-Warn "Falha ao atualizar settings.json: $($_.Exception.Message)"
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
