"""
Конфигурация Telegram бота
Все чувствительные данные здесь
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл из корня проекта
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)


class TelegramBotConfig:
    """Конфигурация Telegram бота"""

    # Токен бота - ОБЯЗАТЕЛЬНО из .env
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # ID администратора
    ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", 0))

    # Лимиты и настройки
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xls', 'json']

    # OpenAI настройки
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # AmoCRM настройки (если есть интеграция)
    AMOCRM_ACCESS_TOKEN = os.getenv("AMOCRM_ACCESS_TOKEN", "")
    AMOCRM_SUBDOMAIN = os.getenv("AMOCRM_SUBDOMAIN", "")

    # Пути
    LOGS_DIR = project_root / "logs"
    TEMP_DIR = project_root / "temp"

    @classmethod
    def validate(cls):
        """Проверка обязательных настроек"""
        errors = []

        if not cls.TOKEN or cls.TOKEN == "your_actual_bot_token_here":
            errors.append("TELEGRAM_BOT_TOKEN не установлен в .env файле")

        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY не установлен (бот будет работать в демо-режиме)")

        if errors:
            error_msg = "\n".join([f"⚠️  {error}" for error in errors])
            print(f"\n{'=' * 50}")
            print("ПРЕДУПРЕЖДЕНИЯ КОНФИГУРАЦИИ:")
            print(error_msg)
            print(f"{'=' * 50}\n")

        return len(errors) == 0


# Создаем экземпляр конфигурации
config = TelegramBotConfig()