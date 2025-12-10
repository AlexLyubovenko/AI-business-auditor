# check_duplicates.ps1 - ТОЛЬКО ПРОВЕРКА БЕЗ УДАЛЕНИЯ
Write-Host "=== ПРОВЕРКА ДУБЛИРУЮЩИХСЯ ФАЙЛОВ (БЕЗ УДАЛЕНИЯ) ===" -ForegroundColor Cyan
Write-Host "Этот скрипт только показывает что будет удалено" -ForegroundColor Yellow
Write-Host "Для удаления запустите clean_duplicates.ps1" -ForegroundColor Yellow

# 1. Тестовые файлы из корня
Write-Host "`n1. Тестовые файлы в корне (будут удалены):" -ForegroundColor Yellow
$rootTestFiles = @(
    "my.working.py",
    "minimal_working_bot.py", 
    "one_file_bot.py",
    "run_bot.py",
    "run_bot_fixed.py",
    "simple_bot.py",
    "smart_bot.py",
    "states.py",
    "test_imports.py",
    "working_bot.py",
    "import streamlit as st.py",
    "test_amocrm_demo.py",
    "test_bot_setup.py"
)

foreach ($file in $rootTestFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file (размер: $([math]::Round((Get-Item $file).Length/1024, 2)) KB)" -ForegroundColor Red
    }
}

# 2. Дублирующиеся файлы
Write-Host "`n2. Возможные дубликаты:" -ForegroundColor Yellow

# main.py
if (Test-Path "main.py") {
    $mainSize = [math]::Round((Get-Item "main.py").Length/1024, 2)
    Write-Host "  main.py ($mainSize KB) - вероятно дубль ui/streamlit_app.py" -ForegroundColor Magenta
}

# openai патчи
if (Test-Path "openai_patch.py") {
    Write-Host "  openai_patch.py - патч" -ForegroundColor Magenta
}
if (Test-Path "openai_monkey_patch.py") {
    Write-Host "  openai_monkey_patch.py - патч" -ForegroundColor Magenta
}

# 3. Дубли в integrations/telegram
Write-Host "`n3. Дубли в integrations/telegram:" -ForegroundColor Yellow
$telegramPath = "integrations/telegram"
if (Test-Path $telegramPath) {
    $telegramFiles = @("ai_bot.py", "bot.py", "final_bot.py")
    foreach ($file in $telegramFiles) {
        $fullPath = Join-Path $telegramPath $file
        if (Test-Path $fullPath) {
            $size = [math]::Round((Get-Item $fullPath).Length/1024, 2)
            Write-Host "  ✓ $file ($size KB) - старая версия" -ForegroundColor Red
        }
    }
    
    # Рабочие файлы
    $workingFiles = @("gpt_bot.py", "handlers.py")
    foreach ($file in $workingFiles) {
        $fullPath = Join-Path $telegramPath $file
        if (Test-Path $fullPath) {
            Write-Host "  ✓ $file - РАБОЧИЙ (останется)" -ForegroundColor Green
        }
    }
}

# 4. Дубли в agents
Write-Host "`n4. Дубли в agents:" -ForegroundColor Yellow
$agentsPath = "agents"
if (Test-Path $agentsPath) {
    if (Test-Path "$agentsPath/analyzer_fixed.py") {
        Write-Host "  analyzer_fixed.py - вероятно дубль analyzer.py" -ForegroundColor Magenta
    }
    if (Test-Path "$agentsPath/solution_architect.py") {
        Write-Host "  solution_architect.py - проверить использование" -ForegroundColor Magenta
    }
}

# 5. Логотипы
Write-Host "`n5. Логотипы:" -ForegroundColor Yellow
if (Test-Path "logo.jpeg" -And (Test-Path "ui/logo.jpeg")) {
    Write-Host "  logo.jpeg в корне - дубль ui/logo.jpeg" -ForegroundColor Red
}

# 6. Статистика
Write-Host "`n=== СТАТИСТИКА ===" -ForegroundColor Cyan
$totalFiles = Get-ChildItem -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count
$totalSizeMB = [math]::Round((Get-ChildItem -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Host "Всего файлов: $totalFiles" -ForegroundColor White
Write-Host "Общий размер: $totalSizeMB MB" -ForegroundColor White

# 7. Что делать дальше
Write-Host "`n=== ЧТО ДЕЛАТЬ ДАЛЬШЕ ===" -ForegroundColor Green
Write-Host "1. Создайте резервную копию: .\create_backup.ps1" -ForegroundColor Yellow
Write-Host "2. Запустите очистку: .\clean_duplicates.ps1" -ForegroundColor Yellow
Write-Host "3. Протестируйте приложение" -ForegroundColor Yellow
Write-Host "4. Закоммитьте изменения" -ForegroundColor Yellow