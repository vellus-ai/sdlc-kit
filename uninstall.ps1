# SDLC Kit — desinstalador (Windows PowerShell)
# Uso: irm https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/uninstall.ps1 | iex
#Requires -Version 5.1

& {
    $ErrorActionPreference = "Continue"

    $InstallDir   = if ($env:SDLC_KIT_DIR) { $env:SDLC_KIT_DIR } else { "$env:USERPROFILE\.claude\plugins\sdlc-kit" }
    $CacheDir     = "$env:USERPROFILE\.claude\plugins\cache\sdlc-kit"
    $SettingsFile = "$env:USERPROFILE\.claude\settings.json"

    function Write-Step { param([string]$Msg) Write-Host "[sdlc-kit] $Msg" -ForegroundColor Cyan }
    function Write-Ok   { param([string]$Msg) Write-Host "  + $Msg" -ForegroundColor Green }
    function Write-Warn { param([string]$Msg) Write-Host "  ! $Msg" -ForegroundColor Yellow }

    Write-Step "Desinstalando SDLC Kit..."
    Write-Host ""
    Write-Warn "Os vaults .sdlc/ criados em seus projetos NÃO serão tocados."
    Write-Host ""

    # ── 1. Remover do settings.json ──────────────────────────────────────
    Write-Step "Removendo registro em $SettingsFile..."
    if (Test-Path $SettingsFile) {
        try {
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            $raw = [System.IO.File]::ReadAllText($SettingsFile)
            if (-not [string]::IsNullOrWhiteSpace($raw)) {
                $settings = $raw | ConvertFrom-Json

                if ($settings.PSObject.Properties['extraKnownMarketplaces'] -and
                    $settings.extraKnownMarketplaces.PSObject.Properties['sdlc-kit']) {
                    $settings.extraKnownMarketplaces.PSObject.Properties.Remove('sdlc-kit')
                    Write-Ok "Marketplace 'sdlc-kit' removido"
                }

                if ($settings.PSObject.Properties['enabledPlugins'] -and
                    $settings.enabledPlugins.PSObject.Properties['sdlc-kit@sdlc-kit']) {
                    $settings.enabledPlugins.PSObject.Properties.Remove('sdlc-kit@sdlc-kit')
                    Write-Ok "Plugin 'sdlc-kit@sdlc-kit' desabilitado"
                }

                $json = $settings | ConvertTo-Json -Depth 10
                [System.IO.File]::WriteAllText($SettingsFile, $json, $utf8NoBom)
            }
        } catch {
            Write-Warn "Não foi possível atualizar settings.json: $($_.Exception.Message)"
        }
    } else {
        Write-Warn "settings.json não encontrado (nada a remover)"
    }

    # ── 2. Desinstalar pacote Python ─────────────────────────────────────
    Write-Step "Desinstalando pacote Python..."
    $null = & python -m pip uninstall -y sdlc-kit 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Ok "pacote sdlc-kit removido" }
    else { Write-Warn "pip uninstall retornou $LASTEXITCODE (pode não estar instalado)" }

    # ── 3. Remover clone do install script ───────────────────────────────
    if (Test-Path $InstallDir) {
        Write-Step "Removendo $InstallDir..."
        Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
        if (-not (Test-Path $InstallDir)) { Write-Ok "Diretório removido" }
        else { Write-Warn "Não foi possível remover $InstallDir — remova manualmente" }
    }

    # ── 4. Remover cache do Claude Code ──────────────────────────────────
    if (Test-Path $CacheDir) {
        Write-Step "Removendo cache em $CacheDir..."
        Remove-Item -Recurse -Force $CacheDir -ErrorAction SilentlyContinue
        if (-not (Test-Path $CacheDir)) { Write-Ok "Cache removido" }
        else { Write-Warn "Não foi possível remover $CacheDir — remova manualmente" }
    }

    Write-Host ""
    Write-Host "SDLC Kit desinstalado!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Para aplicar: feche e reabra o Claude Code."
    Write-Host "  Seus vaults .sdlc/ nos projetos permanecem intactos."
    Write-Host ""
}
