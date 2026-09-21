# 停本仓库开发机：算法 main.py（含 Windows spawn 子进程）+ MediaMTX 容器。
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Stop-Compose {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "未找到 docker，跳过容器。"
        return
    }
    docker compose stop mediamtx 2>$null | Out-Null
    docker compose stop rail-vision 2>$null | Out-Null
    docker rm -f mccbts-mediamtx-webcam 2>$null | Out-Null
    Write-Host "已请求停止 docker compose 中的 mediamtx / rail-vision。"
}

function Stop-Algorithm {
    $escapedRoot = [regex]::Escape($Root)
    $candidates = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -match '^python(\.exe)?$' -and $_.CommandLine -and (
            $_.CommandLine -match $escapedRoot -or
            ($_.ExecutablePath -and $_.ExecutablePath -match $escapedRoot)
        ) -and $_.CommandLine -match 'main\.py'
    }
    if (-not $candidates) {
        Write-Host "没有发现本仓库的 python main.py。"
        return
    }
    $ids = $candidates | Select-Object -ExpandProperty ProcessId -Unique
    foreach ($id in $ids) {
        & taskkill.exe /F /T /PID $id 2>$null | Out-Null
        Write-Host "已结束进程树 PID $id"
    }
}

Stop-Compose
Stop-Algorithm
Write-Host "关闭完成。"
