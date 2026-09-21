# 启动本仓库开发机算法（须已 docker compose up -d mediamtx）。
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $Python = $venvPython
} else {
    $Python = "python"
}

$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Get-Content -LiteralPath $envFile -Encoding utf8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) {
            return
        }
        $name = $line.Substring(0, $eq).Trim()
        $value = $line.Substring($eq + 1).Trim()
        Set-Item -Path "Env:$name" -Value $value
    }
}

$calib = Join-Path $Root "config\calib\cam01\camera.npz"
if (-not (Test-Path $calib)) {
    & $Python (Join-Path $Root "scripts\gen_sample_calib.py")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

& $Python (Join-Path $Root "main.py") --config-dir config
exit $LASTEXITCODE
