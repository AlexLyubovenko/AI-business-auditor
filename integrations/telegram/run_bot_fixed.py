# integrations/telegram/run_bot_fixed.py
import os
import sys

# Добавляем корневую директорию в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

from integrations.telegram.bot import BusinessAuditorBot


def main():
    print("""
🤖 Запуск AI Business Auditor Bot (полная версия)

    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
    █                                                       █
    █     AI BUSINESS AUDITOR - TELEGRAM BOT               █
    █     Полнофункциональная версия                       █
    █                                                       █
    █     ✅ GPT анализ с OpenAI                           █
    █     ✅ AmoCRM интеграция                             █
    █     ✅ Профессиональные отчеты                       █
    █     ✅ Визуализация данных                           █
    █                                                       █
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    """)

    try:
        bot = BusinessAuditorBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()