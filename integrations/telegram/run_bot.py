#!/usr/bin/env python3
import asyncio
import sys
import os

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from integrations.telegram.bot import BusinessAuditorBot


def main():
    """Основная функция запуска"""
    print("""
🤖 Запуск AI Business Auditor Telegram Bot...

▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█                                                       █
█     AI BUSINESS AUDITOR - TELEGRAM BOT               █
█                                                       █
█     📊 Анализ данных                                 █
█     📋 Генерация отчетов                             █
█     🏢 Интеграция с AmoCRM                           █
█     📈 Бизнес-метрики                                █
█     💡 Умные рекомендации                            █
█                                                       █
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    """)

    try:
        bot = BusinessAuditorBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()