# clean_duplicates.ps1 - ФАКТИЧЕСКОЕ УДАЛЕНИЕ
Write-Host "=== ОЧИСТКА ДУБЛИРУЮЩИХСЯ ФАЙЛОВ ===" -ForegroundColor Cyan
Write-Host "Убедитесь что создали резервную копию!" -ForegroundColor Red

$confirm = Read-Host "`nВы уверены что хотите удалить файлы? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Отмена операции" -ForegroundColor Yellow
    exit
}

# 1. Тестовые файлы из корня
Write-Host "`n1. Удаление тестовых файлов из корня..." -ForegroundColor Yellow
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

$deletedCount = 0
foreach ($file in $rootTestFiles) {
    if (Test-Path $file) {
        Write-Host "  Удаляю: $file" -ForegroundColor Gray
        Remove-Item $file -Force -ErrorAction SilentlyContinue
        $deletedCount++
    }
}
Write-Host "  Удалено файлов: $deletedCount" -ForegroundColor Green

# 2. main.py (предложить удаление)
Write-Host "`n2. Проверка main.py..." -ForegroundColor Yellow
if (Test-Path "main.py") {
    Write-Host "  Найден main.py" -ForegroundColor Magenta
    $choice = Read-Host "  Удалить main.py? (y/n)"
    if ($choice -eq 'y') {
        Remove-Item "main.py" -Force
        Write-Host "  main.py удален" -ForegroundColor Green
    }
}

# 3. OpenAI патчи (оставить один)
Write-Host "`n3. Обработка патчей OpenAI..." -ForegroundColor Yellow
$hasPatch1 = Test-Path "openai_patch.py"
$hasPatch2 = Test-Path "openai_monkey_patch.py"

if ($hasPatch1 -and $hasPatch2) {
    Write-Host "  Найдены оба патча" -ForegroundColor Magenta
    Write-Host "  openai_patch.py: $(Get-Content 'openai_patch.py' | Measure-Object -Line).Lines строк" -ForegroundColor White
    Write-Host "  openai_monkey_patch.py: $(Get-Content 'openai_monkey_patch.py' | Measure-Object -Line).Lines строк" -ForegroundColor White
    
    $choice = Read-Host "  Какой удалить? (1=openai_patch.py, 2=openai_monkey_patch.py, n=оставить оба)"
    switch ($choice) {
        '1' { Remove-Item "openai_patch.py" -Force; Write-Host "  Удалил openai_patch.py" -ForegroundColor Green }
        '2' { Remove-Item "openai_monkey_patch.py" -Force; Write-Host "  Удалил openai_monkey_patch.py" -ForegroundColor Green }
    }
}

# 4. Дубли в integrations/telegram
Write-Host "`n4. Очистка integrations/telegram..." -ForegroundColor Yellow
$telegramPath = "integrations/telegram"
if (Test-Path $telegramPath) {
    $telegramFiles = @("ai_bot.py", "bot.py", "final_bot.py")
    foreach ($file in $telegramFiles) {
        $fullPath = Join-Path $telegramPath $file
        if (Test-Path $fullPath) {
            Write-Host "  Удаляю: $file" -ForegroundColor Gray
            Remove-Item $fullPath -Force
        }
    }
    Write-Host "  gpt_bot.py и handlers.py остаются (рабочие файлы)" -ForegroundColor Green
}

# 5. Дубли в agents
Write-Host "`n5. Очистка agents..." -ForegroundColor Yellow
$agentsPath = "agents"
if (Test-Path $agentsPath) {
    # analyzer_fixed.py
    if (Test-Path "$agentsPath/analyzer_fixed.py") {
        Write-Host "  Найден analyzer_fixed.py" -ForegroundColor Magenta
        $choice = Read-Host "  Удалить analyzer_fixed.py? (y/n)"
        if ($choice -eq 'y') {
            Remove-Item "$agentsPath/analyzer_fixed.py" -Force
            Write-Host "  analyzer_fixed.py удален" -ForegroundColor Green
        }
    }
    
    # solution_architect.py
    if (Test-Path "$agentsPath/solution_architect.py") {
        Write-Host "  Найден solution_architect.py" -ForegroundColor Magenta
        # Проверяем используется ли
        $usage = Select-String -Path . -Pattern "solution_architect" -Recurse -Quiet
        if (-not $usage) {
            Write-Host "  Файл не используется" -ForegroundColor White
            $choice = Read-Host "  Удалить solution_architect.py? (y/n)"
            if ($choice -eq 'y') {
                Remove-Item "$agentsPath/solution_architect.py" -Force
                Write-Host "  solution_architect.py удален" -ForegroundColor Green
            }
        }
    }
}

# 6. Логотипы
Write-Host "`n6. Логотипы..." -ForegroundColor Yellow
if (Test-Path "logo.jpeg" -And (Test-Path "ui/logo.jpeg")) {
    Write-Host "  Логотип в корне - дубль" -ForegroundColor Magenta
    $choice = Read-Host "  Удалить logo.jpeg из корня? (y/n)"
    if ($choice -eq 'y') {
        Remove-Item "logo.jpeg" -Force
        Write-Host "  logo.jpeg удален" -ForegroundColor Green
    }
}

# 7. Итоги
Write-Host "`n=== ОЧИСТКА ЗАВЕРШЕНА ===" -ForegroundColor Green

$remainingFiles = Get-ChildItem -File | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Файлов в корне: $remainingFiles" -ForegroundColor Cyan

Write-Host "`nСДЕЛАЙТЕ ТЕСТ:" -ForegroundColor Yellow
Write-Host "1. streamlit run ui/streamlit_app.py" -ForegroundColor White
Write-Host "2. python integrations/telegram/gpt_bot.py" -ForegroundColor White