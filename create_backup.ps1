# create_backup.ps1
Write-Host "=== СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ ===" -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupFile = "../ai-auditor-backup-$timestamp.zip"

Write-Host "`nСоздаю резервную копию в: $backupFile" -ForegroundColor Yellow

# Исключаем большие папки из бэкапа
$exclude = @("venv", ".venv", "__pycache__")
$filesToBackup = Get-ChildItem -Path . -Recurse -File | 
    Where-Object { 
        $exclude -notcontains $_.Directory.Name -and
        $exclude -notcontains $_.Parent.Name
    }

# Создаем временную папку для бэкапа
$tempDir = "../temp-backup-$timestamp"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

Write-Host "Копирую файлы..." -ForegroundColor Yellow
foreach ($file in $filesToBackup) {
    $relativePath = $file.FullName.Substring((Get-Location).Path.Length + 1)
    $destPath = Join-Path $tempDir $relativePath
    $destDir = Split-Path $destPath -Parent
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    Copy-Item $file.FullName -Destination $destPath
}

Write-Host "Архивирую..." -ForegroundColor Yellow
Compress-Archive -Path "$tempDir/*" -DestinationPath $backupFile -CompressionLevel Optimal

Write-Host "Очищаю временные файлы..." -ForegroundColor Yellow
Remove-Item $tempDir -Recurse -Force

Write-Host "`n✓ Резервная копия создана: $backupFile" -ForegroundColor Green
Write-Host "Размер: $([math]::Round((Get-Item $backupFile).Length/1MB, 2)) MB" -ForegroundColor Green

# Проверка
Test-Path $backupFile