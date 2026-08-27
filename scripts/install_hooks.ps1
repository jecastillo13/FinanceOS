$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $projectRoot

git config core.hooksPath .githooks
if ($LASTEXITCODE -ne 0) {
    throw "No fue posible configurar los hooks de Git."
}

Write-Host "Hooks instalados correctamente." -ForegroundColor Green
Write-Host "pre-commit: validación rápida de archivos preparados."
Write-Host "pre-push: pruebas de backend, web y móvil."
Write-Host "Para omitirlos solo en una emergencia: git commit --no-verify"
