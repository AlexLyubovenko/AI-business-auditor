"""
Telegram бот AI Business Auditor с настоящим GPT анализом
Безопасная версия с конфигурацией из config.py
"""

import os
import sys
import logging
import pandas as pd
import tempfile
import random
import hashlib
import sqlite3
import shutil
import atexit
import re
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from functools import lru_cache
from typing import Dict, Any, Optional, List, Tuple

import os
import sys
import logging
import asyncio
from datetime import datetime

# Настройка логирования для работы в контейнере
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Проверяем, запущен ли в контейнере
def is_in_container():
    return os.getenv('RENDER') == 'true' or os.path.exists('/.dockerenv')


async def main():
    """Основная асинхронная функция бота"""
    try:
        # Инициализация бота
        from integrations.telegram.config import TELEGRAM_BOT_TOKEN, BOT_CONFIG
        from telegram.ext import Application

        if not TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
            return

        logger.info(f"🤖 Инициализация Telegram бота...")
        logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Создаем приложение
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Импортируем и регистрируем обработчики
        from integrations.telegram.handlers import setup_handlers
        setup_handlers(application)

        logger.info("✅ Обработчики зарегистрированы")

        # Настройка polling
        await application.initialize()
        await application.start()

        if is_in_container():
            logger.info("🚀 Запуск в режиме polling (контейнер)...")
            await application.updater.start_polling(
                drop_pending_updates=BOT_CONFIG.get("skip_updates", True),
                timeout=BOT_CONFIG.get("timeout", 30)
            )
        else:
            logger.info("🚀 Запуск в режиме polling (локально)...")
            await application.updater.start_polling()

        logger.info("✅ Бот запущен и готов к работе!")
        logger.info(f"👤 Имя бота: @{(await application.bot.get_me()).username}")

        # Бесконечный цикл для работы в контейнере
        while True:
            await asyncio.sleep(3600)  # Спим 1 час

    except Exception as e:
        logger.error(f"❌ Критическая ошибка бота: {e}")
        raise


if __name__ == "__main__":
    # Проверяем наличие обязательных переменных
    required_vars = ['TELEGRAM_BOT_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.warning(f"⚠️ Отсутствуют переменные: {missing}")
        logger.info("💡 Telegram бот не будет запущен без TELEGRAM_BOT_TOKEN")
        sys.exit(0)  # Не падаем, просто не запускаем бота

    # Запускаем асинхронно
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")


# ========== НАСТРОЙКА ПУТЕЙ И КОНФИГУРАЦИИ ==========
# Добавляем корневую директорию в путь
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Импортируем конфигурацию
try:
    from config import config as bot_config

    TOKEN = bot_config.TOKEN
    ADMIN_ID = bot_config.ADMIN_ID
    MAX_FILE_SIZE = bot_config.MAX_FILE_SIZE
    ALLOWED_EXTENSIONS = bot_config.ALLOWED_EXTENSIONS

    # Проверяем конфигурацию
    if not bot_config.validate():
        print("⚠️  Внимание: некоторые настройки отсутствуют, бот может работать неполноценно")
        print("   Рекомендуется настроить .env файл")

except ImportError as e:
    print(f"❌ Ошибка импорта config: {e}")
    print("⚠️  Завершаю работу - требуется корректная конфигурация")
    sys.exit(1)

# Проверяем токен бота
if not TOKEN or TOKEN == "your_actual_bot_token_here":
    print("❌ ОШИБКА: Токен бота не настроен!")
    print("   Добавьте TELEGRAM_BOT_TOKEN в .env файл")
    print("   Получите новый токен через @BotFather если старый был скомпрометирован")
    sys.exit(1)

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
# Создаем директорию для логов если её нет
logs_dir = bot_config.LOGS_DIR if hasattr(bot_config, 'LOGS_DIR') else Path("logs")
logs_dir.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(logs_dir / 'telegram_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram импорты
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes


# ========== УТИЛИТЫ ДЛЯ ОБРАБОТКИ ТЕКСТА ==========
def escape_markdown(text: str) -> str:
    """Экранирование специальных символов Markdown для Telegram"""
    if not text:
        return text

    # Экранируем специальные символы Markdown
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text


def sanitize_markdown(text: str) -> str:
    """Безопасное форматирование Markdown"""
    # Удаляем проблемные последовательности
    text = re.sub(r'(\*){3,}', '**', text)  # Множественные звездочки
    text = re.sub(r'(_{3,})', '__', text)  # Множественные подчеркивания
    text = re.sub(r'(`){3,}', '`', text)  # Множественные обратные кавычки

    # Убеждаемся, что все теги парные
    tags = [('**', '**'), ('__', '__'), ('`', '`'), ('*', '*'), ('_', '_')]

    for open_tag, close_tag in tags:
        # Считаем открывающие и закрывающие теги
        open_count = text.count(open_tag)
        close_count = text.count(close_tag)

        # Если нечетное количество, добавляем недостающий тег
        if open_count > close_count:
            text += close_tag
        elif close_count > open_count:
            text = open_tag + text

    return text


def truncate_text(text: str, max_length: int = 3500, suffix: str = "...") -> str:
    """Обрезка текста с учетом Markdown"""
    if len(text) <= max_length:
        return text

    # Ищем место для обрезки после последнего пробела или новой строки
    truncate_point = text.rfind('\n', 0, max_length - len(suffix))
    if truncate_point == -1:
        truncate_point = text.rfind(' ', 0, max_length - len(suffix))
    if truncate_point == -1:
        truncate_point = max_length - len(suffix)

    truncated = text[:truncate_point] + suffix

    # Закрываем незакрытые Markdown теги
    return sanitize_markdown(truncated)


# ========== МЕНЕДЖЕР БАЗЫ ДАННЫХ ==========
class DatabaseManager:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = Path(db_path)
        self.init_db()

    def get_connection(self):
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Инициализация таблиц базы данных"""
        with self.get_connection() as conn:
            # Таблица пользователей
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP
                )
            """)

            # Таблица анализов
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    file_hash TEXT,
                    record_count INTEGER,
                    columns_count INTEGER,
                    analysis_type TEXT,
                    gpt_used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Таблица rate limits
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    gpt_requests_today INTEGER DEFAULT 0,
                    last_gpt_request TIMESTAMP,
                    reset_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            conn.commit()

    def save_user(self, user_id: int, username: str, first_name: str, last_name: str, language_code: str):
        """Сохранить или обновить пользователя"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, language_code, last_active)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, username, first_name, last_name, language_code))
            conn.commit()

    def log_analysis(self, user_id: int, filename: str, file_hash: str, record_count: int,
                     columns_count: int, analysis_type: str, gpt_used: bool = False):
        """Записать анализ в базу данных"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO analyses 
                (user_id, filename, file_hash, record_count, columns_count, analysis_type, gpt_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, filename, file_hash, record_count, columns_count, analysis_type, gpt_used))
            conn.commit()

    def check_rate_limit(self, user_id: int) -> tuple:
        """Проверить rate limit для пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT gpt_requests_today, last_gpt_request, reset_date
                FROM rate_limits WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()

            today = datetime.now().date()

            if row is None:
                # Создать запись
                conn.execute("""
                    INSERT INTO rate_limits (user_id, reset_date)
                    VALUES (?, ?)
                """, (user_id, today))
                conn.commit()
                return 0, None, today

            # Проверить, нужно ли сбросить счетчик
            reset_date = datetime.strptime(row['reset_date'], '%Y-%m-%d').date() if isinstance(row['reset_date'],
                                                                                               str) else row[
                'reset_date']

            if today > reset_date:
                # Сбросить счетчик
                conn.execute("""
                    UPDATE rate_limits 
                    SET gpt_requests_today = 0, reset_date = ?
                    WHERE user_id = ?
                """, (today, user_id))
                conn.commit()
                return 0, row['last_gpt_request'], today

            return row['gpt_requests_today'], row['last_gpt_request'], reset_date

    def increment_gpt_requests(self, user_id: int):
        """Увеличить счетчик GPT запросов"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE rate_limits 
                SET gpt_requests_today = gpt_requests_today + 1,
                    last_gpt_request = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_analyses,
                    SUM(CASE WHEN gpt_used = 1 THEN 1 ELSE 0 END) as gpt_analyses,
                    MAX(created_at) as last_analysis
                FROM analyses 
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()

            return {
                'total_analyses': row['total_analyses'] if row else 0,
                'gpt_analyses': row['gpt_analyses'] if row else 0,
                'last_analysis': row['last_analysis']
            }

    def get_admin_stats(self) -> Dict[str, Any]:
        """Получить статистику для администратора"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(*) as total_analyses,
                    SUM(CASE WHEN gpt_used = 1 THEN 1 ELSE 0 END) as total_gpt_analyses,
                    DATE(created_at) as date,
                    COUNT(*) as daily_count
                FROM analyses 
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 7
            """)

            daily_stats = cursor.fetchall()

            cursor = conn.execute("""
                SELECT COUNT(*) as active_users
                FROM users 
                WHERE last_active > DATE('now', '-7 days')
            """)
            active_users = cursor.fetchone()['active_users']

            return {
                'total_users': daily_stats[0]['total_users'] if daily_stats else 0,
                'total_analyses': daily_stats[0]['total_analyses'] if daily_stats else 0,
                'total_gpt_analyses': daily_stats[0]['total_gpt_analyses'] if daily_stats else 0,
                'active_users': active_users,
                'daily_stats': daily_stats
            }


# ========== ИМПОРТ ВАШИХ МОДУЛЕЙ ==========
GPT_AVAILABLE = False
try:
    print("🔍 Импорт DataAnalyzer через адаптер...")

    # Пробуем импортировать адаптер
    try:
        from analyzer_adapter import analyzer as gpt_analyzer

        print("✅ Адаптированный DataAnalyzer импортирован")
        GPT_AVAILABLE = True
    except ImportError:
        # Если адаптера нет, пробуем напрямую
        print("⚠️  Адаптер не найден, пробую прямой импорт...")

        # Добавляем путь к agents
        project_root = current_dir.parent.parent
        agents_path = project_root / "agents"
        if str(agents_path) not in sys.path:
            sys.path.insert(0, str(agents_path))

        from analyzer import DataAnalyzer

        print("✅ DataAnalyzer импортирован напрямую")


        # Создаем совместимую обертку
        class CompatibleDataAnalyzer:
            def __init__(self):
                self.analyzer = DataAnalyzer()

            def basic_analysis(self, df):
                result = self.analyzer.basic_analysis(df)
                # Гарантируем наличие нужных полей
                if isinstance(result, dict):
                    if 'trends' not in result:
                        result['trends'] = []
                    if 'financial_metrics' not in result:
                        result['financial_metrics'] = {}
                return result

            def gpt_analysis(self, df):
                try:
                    # Пробуем разные варианты вызова
                    try:
                        return self.analyzer.gpt_analysis(df)
                    except TypeError as e:
                        if "missing" in str(e) and "required" in str(e):
                            # Нужны trends и financial_metrics
                            basic = self.basic_analysis(df)
                            trends = basic.get('trends', [])
                            financial_metrics = basic.get('financial_metrics', {})
                            return self.analyzer.gpt_analysis(df, trends=trends, financial_metrics=financial_metrics)
                        else:
                            raise e
                except Exception as e:
                    # Возвращаем демо-анализ при ошибке
                    return self._get_fallback_analysis(df)

            def _get_fallback_analysis(self, df):
                numeric_cols = df.select_dtypes(include='number').columns
                if len(numeric_cols) > 0:
                    response = "*GPT Анализ (совместимый режим)*\n\n"
                    response += "*Обнаруженные тренды:*\n"
                    for col in numeric_cols[:2]:
                        mean_val = df[col].mean()
                        response += f"• {col}: среднее значение {mean_val:,.2f}\n"
                    return response
                else:
                    return "*GPT Анализ:* Загрузите файл с числовыми данными"


        gpt_analyzer = CompatibleDataAnalyzer()
        GPT_AVAILABLE = True

    # Проверяем доступность OpenAI API
    if hasattr(bot_config, 'OPENAI_API_KEY') and bot_config.OPENAI_API_KEY:
        print("🔑 OpenAI API ключ обнаружен в конфигурации")
    else:
        print("⚠️  OpenAI API ключ не настроен, GPT анализ может не работать")

except ImportError as e:
    print(f"⚠️  DataAnalyzer не найден: {e}")
    print("⚠️  Используем демо-режим GPT анализа")


    # Демо-заглушка для анализатора
    class DemoAnalyzer:
        def basic_analysis(self, df):
            return {
                'record_count': len(df),
                'columns': list(df.columns),
                'summary': 'Демо-анализ: используйте веб-версию для полного функционала',
                'trends': [],
                'financial_metrics': {},
                'recommendations': ['Загрузите в веб-интерфейс для GPT анализа']
            }

        def gpt_analysis(self, df):
            numeric_cols = df.select_dtypes(include='number').columns

            if len(numeric_cols) > 0:
                response = "*GPT Анализ (демо-режим)*\n\n"
                response += "*Обнаруженные тренды:*\n"

                for col in numeric_cols[:2]:
                    mean_val = df[col].mean()
                    response += f"• {col}: среднее значение {mean_val:,.2f}\n"

                response += "\n*Рекомендации:*\n"
                response += "1. Используйте веб-интерфейс для полного GPT анализа\n"
                response += "2. Добавьте OpenAI API ключ в .env файл\n"
                response += "3. Настройте интеграцию с AmoCRM\n"

                return response
            else:
                return "*GPT Анализ:* Загрузите файл с числовыми данными для анализа"


    gpt_analyzer = DemoAnalyzer()


# ========== КЛАВИАТУРЫ ==========
def get_main_menu():
    """Главное меню"""
    keyboard = [
        [KeyboardButton("📊 Анализ файла"), KeyboardButton("🤖 GPT Анализ")],
        [KeyboardButton("📈 Графики"), KeyboardButton("📋 Отчет")],
        [KeyboardButton("🏢 AmoCRM"), KeyboardButton("💡 Советы")],
        [KeyboardButton("⚙️ Настройки"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("❓ Помощь"), KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_analysis_menu():
    """Меню анализа"""
    buttons = [
        [
            InlineKeyboardButton("📊 Быстрый анализ", callback_data="quick"),
            InlineKeyboardButton("🤖 GPT Анализ", callback_data="gpt")
        ],
        [
            InlineKeyboardButton("📈 Визуализация", callback_data="viz"),
            InlineKeyboardButton("📋 Полный отчет", callback_data="full_report")
        ],
        [
            InlineKeyboardButton("🎯 Рекомендации", callback_data="recommend"),
            InlineKeyboardButton("🔍 Детали", callback_data="details")
        ],
        [
            InlineKeyboardButton("📊 Моя статистика", callback_data="my_stats"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_gpt_settings_menu():
    """Меню настроек GPT"""
    buttons = [
        [InlineKeyboardButton("🔑 Настроить API ключ", callback_data="set_api_key")],
        [InlineKeyboardButton("⚙️ Настройки модели", callback_data="set_model")],
        [InlineKeyboardButton("📊 Контекст анализа", callback_data="set_context")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_cancel_menu():
    """Меню отмены"""
    buttons = [
        [InlineKeyboardButton("❌ Отменить операцию", callback_data="cancel_operation")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_model_settings_menu():
    """Меню настроек модели"""
    buttons = [
        [
            InlineKeyboardButton("GPT-3.5 Turbo", callback_data="model_gpt35"),
            InlineKeyboardButton("GPT-4", callback_data="model_gpt4")
        ],
        [
            InlineKeyboardButton("GPT-4 Turbo", callback_data="model_gpt4t"),
            InlineKeyboardButton("GPT-4o", callback_data="model_gpt4o")
        ],
        [
            InlineKeyboardButton("🔙 Назад к настройкам", callback_data="back_to_settings")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


# ========== ОСНОВНОЙ КЛАСС БОТА ==========
class GPTBusinessBot:
    def __init__(self):
        self.analyzer = gpt_analyzer
        self.user_data = {}
        self.db = DatabaseManager()
        self.temp_dir = bot_config.TEMP_DIR if hasattr(bot_config, 'TEMP_DIR') else Path("temp")
        self.temp_dir.mkdir(exist_ok=True, parents=True)

        # Настройки rate limit
        self.MAX_GPT_REQUESTS_PER_DAY = getattr(bot_config, 'MAX_GPT_REQUESTS_PER_DAY', 50)
        self.GPT_COOLDOWN_SECONDS = getattr(bot_config, 'GPT_COOLDOWN_SECONDS', 30)

        self.gpt_settings = {
            'model': bot_config.OPENAI_MODEL if hasattr(bot_config, 'OPENAI_MODEL') else 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 1000
        }

        # Регистрируем очистку при завершении
        atexit.register(self.cleanup)

        print("=" * 60)
        print("🤖 GPT BUSINESS AUDITOR BOT")
        print(f"✅ Token: {'Установлен' if TOKEN and TOKEN != 'your_actual_bot_token_here' else 'Не настроен'}")
        print(f"📊 GPT анализ: {'ДОСТУПЕН' if GPT_AVAILABLE else 'ДЕМО-РЕЖИМ'}")
        print(f"👤 Админ ID: {ADMIN_ID if ADMIN_ID else 'Не настроен'}")
        print(f"🗄️  База данных: {self.db.db_path}")
        print("=" * 60)

    def cleanup(self):
        """Очистка временных файлов при завершении"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("Временные файлы очищены")
        except Exception as e:
            logger.warning(f"Не удалось очистить временные файлы: {e}")

    def create_data_hash(self, df: pd.DataFrame) -> str:
        """Создать хеш данных для кэширования"""
        try:
            return hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()
        except:
            # Fallback для совместимости
            return hashlib.md5(str(df.shape).encode() + str(df.columns.tolist()).encode()).hexdigest()

    @lru_cache(maxsize=100)
    def get_cached_analysis(self, data_hash: str, analysis_type: str) -> Optional[str]:
        """Получить кэшированный анализ"""
        # В реальной реализации здесь было бы обращение к Redis или другой кэш-системе
        return None

    async def check_gpt_rate_limit(self, user_id: int) -> tuple:
        """Проверить rate limit для GPT запросов"""
        requests_today, last_request, reset_date = self.db.check_rate_limit(user_id)

        # Проверить daily limit
        if requests_today >= self.MAX_GPT_REQUESTS_PER_DAY:
            reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            time_left = reset_time - datetime.now()
            return False, f"Достигнут дневной лимит ({self.MAX_GPT_REQUESTS_PER_DAY} запросов).\nЛимит сбросится через {time_left.seconds // 3600} ч. {(time_left.seconds % 3600) // 60} мин."

        # Проверить cooldown
        if last_request:
            last_request_time = datetime.strptime(last_request, '%Y-%m-%d %H:%M:%S') if isinstance(last_request,
                                                                                                   str) else last_request
            time_since_last = datetime.now() - last_request_time

            if time_since_last.total_seconds() < self.GPT_COOLDOWN_SECONDS:
                wait_time = self.GPT_COOLDOWN_SECONDS - time_since_last.total_seconds()
                return False, f"Подождите {int(wait_time)} секунд перед следующим GPT запросом."

        return True, ""

    async def safe_send_message(self, chat_id: int, text: str,
                                parse_mode: str = None,
                                reply_markup=None,
                                context: ContextTypes.DEFAULT_TYPE = None) -> bool:
        """Безопасная отправка сообщения с обработкой ошибок Markdown"""
        try:
            # Очищаем Markdown
            if parse_mode == 'Markdown':
                text = sanitize_markdown(text)
                # Обрезаем если слишком длинный
                text = truncate_text(text, 3500)

            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

            # Пробуем отправить без Markdown
            if parse_mode == 'Markdown':
                try:
                    clean_text = escape_markdown(text)
                    clean_text = truncate_text(clean_text, 3500)

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=clean_text,
                        parse_mode=None,
                        reply_markup=reply_markup
                    )
                    return True
                except Exception as e2:
                    logger.error(f"Ошибка отправки без Markdown: {e2}")

            return False

    async def safe_edit_message_text(self, message, text: str,
                                     parse_mode: str = None,
                                     reply_markup=None,
                                     context: ContextTypes.DEFAULT_TYPE = None) -> bool:
        """Безопасное редактирование сообщения с обработкой ошибок Markdown"""
        try:
            # Очищаем Markdown
            if parse_mode == 'Markdown':
                text = sanitize_markdown(text)
                text = truncate_text(text, 3500)

            await message.edit_text(
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения: {e}")

            # Пробуем отправить без Markdown
            if parse_mode == 'Markdown':
                try:
                    clean_text = escape_markdown(text)
                    clean_text = truncate_text(clean_text, 3500)

                    await message.edit_text(
                        text=clean_text,
                        parse_mode=None,
                        reply_markup=reply_markup
                    )
                    return True
                except Exception as e2:
                    logger.error(f"Ошибка редактирования без Markdown: {e2}")

            return False

    async def safe_edit_callback_message(self, query, text: str,
                                         parse_mode: str = None,
                                         reply_markup=None) -> bool:
        """Безопасное редактирование сообщения callback query"""
        try:
            # Очищаем Markdown
            if parse_mode == 'Markdown':
                text = sanitize_markdown(text)
                text = truncate_text(text, 3500)

            await query.edit_message_text(
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка редактирования callback сообщения: {e}")

            # Пробуем отправить без Markdown
            if parse_mode == 'Markdown':
                try:
                    clean_text = escape_markdown(text)
                    clean_text = truncate_text(clean_text, 3500)

                    await query.edit_message_text(
                        text=clean_text,
                        parse_mode=None,
                        reply_markup=reply_markup
                    )
                    return True
                except Exception as e2:
                    logger.error(f"Ошибка редактирования callback без Markdown: {e2}")

            return False

    # ========== ОСНОВНЫЕ КОМАНДЫ ==========
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")

        # Сохраняем пользователя в БД
        self.db.save_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )

        gpt_status = "*GPT АНАЛИЗ ДОСТУПЕН*" if GPT_AVAILABLE else "*GPT АНАЛИЗ (демо)*"

        welcome = f"""
*ДОБРО ПОЖАЛОВАТЬ В AI BUSINESS AUDITOR!*

{gpt_status}

*ПОЛНЫЙ ФУНКЦИОНАЛ:*
• Анализ CSV/Excel/JSON файлов
• Настоящий GPT анализ с AI рекомендациями
• Детальная аналитика и визуализация
• Профессиональные отчеты в Markdown/PDF
• Интеграция с AmoCRM (демо + реальная)

*ПОЛУЧИТЕ GPT АНАЛИЗ:*
1. Нажмите 📊 Анализ файла
2. Отправьте финансовые данные
3. Выберите 🤖 GPT Анализ
4. Получите AI рекомендации

*Используйте меню ниже:*
        """

        await update.message.reply_text(
            welcome,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
*ПОМОЩЬ ПО GPT BUSINESS AUDITOR*

*GPT АНАЛИЗ:*
• Использует OpenAI GPT для анализа данных
• Дает бизнес-рекомендации на основе данных
• Обнаруживает тренды и аномалии
• Формирует прогнозы

*ТРЕБОВАНИЯ ДЛЯ GPT:*
1. OpenAI API ключ в .env файле:
   OPENAI_API_KEY=sk-ваш_ключ
2. Активная подписка OpenAI
3. Интернет-подключение

*ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ:*
• CSV (финансовые отчеты, продажи)
• Excel (бюджеты, аналитика)
• JSON (структурированные данные)

*ПРИМЕР ФАЙЛА ДЛЯ АНАЛИЗА:*
Месяц,Выручка,Расходы,Прибыль,Клиенты
Январь 2024,1000000,700000,300000,150
Февраль 2024,1200000,800000,400000,180
Март 2024,1500000,900000,600000,220

*ПОДДЕРЖКА:* @alex_lyubovenko

*Команды:*
/start - Запустить бота
/help - Помощь
/cancel - Отменить текущую операцию
/stats - Ваша статистика
        """

        await update.message.reply_text(
            help_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /cancel - отмена текущей операции"""
        user_id = update.effective_user.id

        if user_id in self.user_data:
            # Очищаем данные пользователя
            self.user_data.pop(user_id, None)

        await update.message.reply_text(
            "✅ Операция отменена. Все временные данные удалены.",
            reply_markup=get_main_menu()
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика пользователя"""
        user_id = update.effective_user.id
        stats = self.db.get_user_stats(user_id)

        stats_text = f"""
*ВАША СТАТИСТИКА*

*Общая статистика:*
• Всего анализов: {stats['total_analyses']}
• GPT анализов: {stats['gpt_analyses']}
• Последний анализ: {stats['last_analysis'] or 'Нет данных'}

*Лимиты:*
• GPT запросов сегодня: {self.db.check_rate_limit(user_id)[0]}/{self.MAX_GPT_REQUESTS_PER_DAY}
• Лимит на день: {self.MAX_GPT_REQUESTS_PER_DAY}
• Задержка между запросами: {self.GPT_COOLDOWN_SECONDS} сек.

*Совет:* Используйте веб-интерфейс для полной статистики.
        """

        await update.message.reply_text(
            stats_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def admin_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /admin_stats - статистика для администратора"""
        user_id = update.effective_user.id

        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Эта команда только для администратора.")
            return

        stats = self.db.get_admin_stats()

        stats_text = f"""
*СТАТИСТИКА АДМИНИСТРАТОРА*

*Пользователи:*
• Всего пользователей: {stats['total_users']}
• Активных (7 дней): {stats['active_users']}

*Анализы:*
• Всего анализов: {stats['total_analyses']}
• GPT анализов: {stats['total_gpt_analyses']}

*Последние 7 дней:*
"""

        for day_stat in stats['daily_stats'][:5]:
            stats_text += f"• {day_stat['date']}: {day_stat['daily_count']} анализов\n"

        stats_text += "\n*Дополнительная статистика в веб-интерфейсе.*"

        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown'
        )

    async def notify_admin(self, message: str, context: ContextTypes.DEFAULT_TYPE):
        """Уведомление администратора о важных событиях"""
        if ADMIN_ID:
            try:
                await self.safe_send_message(
                    chat_id=ADMIN_ID,
                    text=f"*УВЕДОМЛЕНИЕ БОТА*\n\n{message}",
                    parse_mode='Markdown',
                    context=context
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу: {e}")

    # ========== ОБРАБОТКА СООБЩЕНИЙ ==========
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        text = update.message.text
        user_id = update.effective_user.id

        logger.info(f"[{user_id}] Кнопка: {text}")

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "*ЗАГРУЗИТЕ ФАЙЛ ДЛЯ GPT АНАЛИЗА*\n\n"
                "*Рекомендуемые данные:*\n"
                "• Финансовые отчеты\n"
                "• Данные о продажах\n"
                "• Бюджеты и расходы\n"
                "• Метрики бизнеса\n\n"
                f"*Форматы:* {', '.join(ALLOWED_EXTENSIONS)}\n"
                f"*Макс. размер:* {MAX_FILE_SIZE / 1024 / 1024:.0f} MB\n\n"
                "*Для лучшего анализа:*\n"
                "1. Добавьте временные метки\n"
                "2. Включите числовые показатели\n"
                "3. Уберите лишние пустые строки",
                parse_mode='Markdown'
            )

        elif text == "🤖 GPT Анализ":
            if user_id in self.user_data and 'df' in self.user_data[user_id]:
                await self.perform_gpt_analysis(update, context, user_id)
            else:
                status = "ГОТОВ К РАБОТЕ" if GPT_AVAILABLE else "ТРЕБУЕТ НАСТРОЙКИ"

                await update.message.reply_text(
                    f"*GPT АНАЛИЗ* {status}\n\n"
                    f"*Статус:* {'Настроен' if GPT_AVAILABLE else 'Требуется API ключ'}\n\n"
                    f"*Что анализирую:*\n"
                    f"• Финансовые показатели\n"
                    f"• Тренды и закономерности\n"
                    f"• Аномалии и риски\n"
                    f"• Оптимизационные возможности\n"
                    f"• Прогнозы на основе данных\n\n"
                    f"*Сначала:* Загрузите файл через 📊 Анализ файла",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

        elif text == "📈 Графики":
            await update.message.reply_text(
                "*ВИЗУАЛИЗАЦИЯ В ВЕБ-ИНТЕРФЕЙСЕ*\n\n"
                "Полные графики и дашборды доступны в веб-версии:\n\n"
                "streamlit run ui/streamlit_app.py\n\n"
                "*Что доступно в веб-версии:*\n"
                "• Интерактивные графики Plotly\n"
                "• Динамические дашборды\n"
                "• Тепловые карты корреляций\n"
                "• Распределения и гистограммы\n\n"
                "*Telegram бот фокусируется на текстовом анализе и рекомендациях*",
                parse_mode='Markdown'
            )

        elif text == "📋 Отчет":
            if user_id in self.user_data and 'df' in self.user_data[user_id]:
                await self.generate_gpt_report(update, context, user_id)
            else:
                await update.message.reply_text(
                    "*ГЕНЕРАЦИЯ GPT ОТЧЕТА*\n\n"
                    "Сначала загрузите файл для анализа\n\n"
                    "*Что будет в отчете:*\n"
                    "• Сводка анализа\n"
                    "• GPT рекомендации\n"
                    "• Ключевые метрики\n"
                    "• План действий\n"
                    "• Прогнозы и риски",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

        elif text == "🏢 AmoCRM":
            await self.show_amocrm_integration(update, context)

        elif text == "💡 Советы":
            await self.show_gpt_tips(update, context)

        elif text == "⚙️ Настройки":
            await self.show_gpt_settings(update, context)

        elif text == "📊 Статистика":
            await self.stats_command(update, context)

        elif text == "❓ Помощь":
            await self.help_command(update, context)

        elif text == "❌ Отмена":
            await self.cancel_command(update, context)

        else:
            await update.message.reply_text(
                "🤔 Я не понял ваше сообщение. Используйте меню ниже или команды /start, /help",
                reply_markup=get_main_menu()
            )

    # ========== ОБРАБОТКА ФАЙЛОВ ==========
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженных файлов"""
        user_id = update.effective_user.id
        document = update.message.document
        file_name = document.file_name

        logger.info(f"[{user_id}] Загрузка файла: {file_name} ({document.file_size} bytes)")

        # Проверка размера файла
        if document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"*ФАЙЛ СЛИШКОМ БОЛЬШОЙ*\n\n"
                f"Файл: {file_name}\n"
                f"Размер: {document.file_size / 1024 / 1024:.2f} MB\n"
                f"Лимит: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB\n\n"
                f"*Совет:* Разделите данные на несколько файлов",
                parse_mode='Markdown'
            )
            return

        # Проверка формата файла
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            await update.message.reply_text(
                f"*НЕПОДДЕРЖИВАЕМЫЙ ФОРМАТ*\n\n"
                f"Файл: {file_name}\n"
                f"Формат: .{file_ext}\n\n"
                f"*Поддерживаемые форматы:* {', '.join(ALLOWED_EXTENSIONS)}",
                parse_mode='Markdown'
            )
            return

        # Статус загрузки
        status_msg = await update.message.reply_text(
            f"*ЗАГРУЗКА ФАЙЛА ДЛЯ GPT АНАЛИЗА...*\n\n"
            f"{file_name}\n"
            f"Размер: {document.file_size / 1024:.0f} KB\n"
            f"Подготовка к анализу...",
            parse_mode='Markdown'
        )

        # Скачиваем файл
        try:
            file = await document.get_file()

            temp_file_path = self.temp_dir / f"upload_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            await file.download_to_drive(temp_file_path)

            # Загружаем данные
            df = self.load_dataframe(temp_file_path, file_ext)

            # Проверяем данные
            if df.empty:
                raise ValueError("Файл пуст или не содержит данных")

            # Создаем хеш данных
            data_hash = self.create_data_hash(df)

            # Сохраняем данные
            self.user_data[user_id] = {
                'df': df,
                'filename': file_name,
                'file_path': str(temp_file_path),
                'data_hash': data_hash,
                'uploaded_at': datetime.now(),
                'preview': self.get_data_preview(df)
            }

            # Формируем ответ
            preview = self.user_data[user_id]['preview']

            # Редактируем исходное сообщение
            success = await self.safe_edit_message_text(
                message=status_msg,
                text=f"*ФАЙЛ ГОТОВ К GPT АНАЛИЗУ!*\n\n"
                     f"{file_name}\n"
                     f"*{len(df):,}* записей | *{len(df.columns)}* колонок\n\n"
                     f"{preview}\n\n"
                     f"*ВЫБЕРИТЕ ТИП АНАЛИЗА:*",
                parse_mode='Markdown',
                reply_markup=get_analysis_menu(),
                context=context
            )

            if not success:
                # Если не удалось отредактировать, отправляем новое сообщение
                await self.safe_send_message(
                    chat_id=user_id,
                    text=f"*ФАЙЛ ГОТОВ К GPT АНАЛИЗУ!*\n\n"
                         f"{file_name}\n"
                         f"*{len(df):,}* записей | *{len(df.columns)}* колонок\n\n"
                         f"{preview}\n\n"
                         f"*ВЫБЕРИТЕ ТИП АНАЛИЗА:*",
                    parse_mode='Markdown',
                    reply_markup=get_analysis_menu(),
                    context=context
                )

            logger.info(f"[{user_id}] Файл успешно загружен: {len(df)} записей, {len(df.columns)} колонок")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{user_id}] Ошибка загрузки файла: {error_msg}")

            # Удаляем временный файл если он существует
            try:
                if 'temp_file_path' in locals():
                    os.unlink(temp_file_path)
            except:
                pass

            success = await self.safe_edit_message_text(
                message=status_msg,
                text=f"*ОШИБКА ЗАГРРУЗКИ*\n\n"
                     f"Файл: {file_name}\n\n"
                     f"*Причина:* {error_msg[:150]}\n\n"
                     f"*Проверьте:*\n"
                     f"1. Корректность формата данных\n"
                     f"2. Кодировку файла (используйте UTF-8)\n"
                     f"3. Разделители в CSV (запятая или точка с запятой)",
                parse_mode='Markdown',
                context=context
            )

            if not success:
                await update.message.reply_text(
                    f"❌ Ошибка загрузки файла: {error_msg[:150]}",
                    parse_mode=None
                )

    def load_dataframe(self, file_path, file_ext):
        """Загрузка DataFrame с обработкой ошибок"""
        try:
            if file_ext == 'csv':
                # Пробуем разные кодировки
                try:
                    return pd.read_csv(file_path, encoding='utf-8')
                except:
                    return pd.read_csv(file_path, encoding='cp1251')
            elif file_ext in ['xlsx', 'xls']:
                return pd.read_excel(file_path)
            elif file_ext == 'json':
                return pd.read_json(file_path)
            else:
                # Автоопределение
                try:
                    return pd.read_csv(file_path)
                except:
                    try:
                        return pd.read_excel(file_path)
                    except:
                        raise ValueError(f"Неподдерживаемый формат: .{file_ext}")
        except Exception as e:
            raise ValueError(f"Ошибка чтения файла: {str(e)}")

    def get_data_preview(self, df):
        """Предпросмотр данных"""
        preview = "*СТРУКТУРА ДАННЫХ:*\n"

        numeric_cols = df.select_dtypes(include='number').columns
        text_cols = df.select_dtypes(include='object').columns

        preview += f"• Числовых колонок: {len(numeric_cols)}\n"
        preview += f"• Текстовых колонок: {len(text_cols)}\n"
        preview += f"• Пропусков: {df.isnull().sum().sum()}\n"

        # Показываем первые несколько строк
        if len(df) > 0:
            preview += f"• Первая дата/время: "
            # Ищем колонки с датами
            for col in df.columns:
                try:
                    if pd.api.types.is_datetime64_any_dtype(df[col]) or 'date' in col.lower() or 'time' in col.lower():
                        preview += f"{df[col].iloc[0]}\n"
                        break
                except:
                    pass

            if len(numeric_cols) > 0:
                preview += "\n*ПЕРВЫЕ ЧИСЛОВЫЕ КОЛОНКИ:*\n"
                for col in numeric_cols[:3]:
                    preview += f"• {col}: {df[col].dtype}, "
                    preview += f"avg: {df[col].mean():.2f}\n"

        return preview

    # ========== ОБРАБОТКА CALLBACK ==========
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback кнопок"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        action = query.data

        logger.info(f"[{user_id}] Callback: {action}")

        if action == "quick":
            await self.quick_analysis(query, context, user_id)
        elif action == "gpt":
            await self.gpt_analysis_callback(query, context, user_id)
        elif action == "full_report":
            await self.full_report_callback(query, context, user_id)
        elif action == "recommend":
            await self.show_recommendations(query, context, user_id)
        elif action == "details":
            await self.show_details(query, context, user_id)
        elif action == "viz":
            await self.show_visualization_info(query, context)
        elif action == "my_stats":
            await self.show_my_stats_callback(query, context, user_id)
        elif action == "set_api_key":
            await self.show_api_key_help(query, context)
        elif action == "set_model":
            await self.show_model_settings(query, context)
        elif action == "model_gpt35":
            await self.set_model(query, context, "gpt-3.5-turbo")
        elif action == "model_gpt4":
            await self.set_model(query, context, "gpt-4")
        elif action == "model_gpt4t":
            await self.set_model(query, context, "gpt-4-turbo")
        elif action == "model_gpt4o":
            await self.set_model(query, context, "gpt-4o")
        elif action == "set_context":
            await self.show_context_settings(query, context)
        elif action == "back_to_settings":
            await self.back_to_settings(query, context)
        elif action == "back_to_main":
            await self.back_to_main(query, context)
        elif action == "cancel_operation":
            await self.cancel_operation(query, context, user_id)
        else:
            await self.safe_edit_callback_message(
                query=query,
                text="🤔 Действие не распознано",
                reply_markup=get_main_menu()
            )

    async def quick_analysis(self, query, context, user_id):
        """Быстрый анализ"""
        if user_id not in self.user_data:
            await self.safe_edit_callback_message(
                query=query,
                text="❌ Нет данных для анализа",
                parse_mode=None
            )
            return

        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        await self.safe_edit_callback_message(
            query=query,
            text="*ВЫПОЛНЯЮ БЫСТРЫЙ АНАЛИЗ...*",
            parse_mode='Markdown'
        )

        try:
            # Базовый анализ
            basic_analysis = self.analyzer.basic_analysis(df)

            response = f"*БЫСТРЫЙ АНАЛИЗ: {filename}*\n\n"
            response += f"*ОСНОВНЫЕ МЕТРИКИ:*\n"
            response += f"• Записей: {len(df):,}\n"
            response += f"• Колонок: {len(df.columns)}\n"

            if 'record_count' in basic_analysis:
                response += f"• Проанализировано: {basic_analysis['record_count']}\n"

            if 'summary' in basic_analysis:
                summary = basic_analysis['summary'][:300]
                response += f"\n*СВОДКА:*\n{summary}...\n"

            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                response += f"\n*ФИНАНСОВЫЕ ПОКАЗАТЕЛИ:*\n"
                for col in numeric_cols[:3]:
                    if df[col].dtype in ['int64', 'float64']:
                        response += f"• {col}:\n"
                        response += f"  Среднее: {df[col].mean():,.2f}\n"
                        response += f"  Сумма: {df[col].sum():,.2f}\n"
                        response += f"  Диапазон: {df[col].min():.2f} - {df[col].max():.2f}\n\n"

            response += "*ДЛЯ ПОДРОБНОГО АНАЛИЗА:*\n"
            response += "Нажмите 🤖 GPT Анализ"

            await self.safe_edit_callback_message(
                query=query,
                text=response,
                parse_mode='Markdown',
                reply_markup=get_analysis_menu()
            )

            # Логируем анализ в БД
            self.db.log_analysis(
                user_id=user_id,
                filename=filename,
                file_hash=data['data_hash'],
                record_count=len(df),
                columns_count=len(df.columns),
                analysis_type='quick'
            )

        except Exception as e:
            logger.error(f"[{user_id}] Ошибка быстрого анализа: {e}")
            error_msg = str(e)[:200] if len(str(e)) > 200 else str(e)
            await self.safe_edit_callback_message(
                query=query,
                text=f"❌ Ошибка анализа: {error_msg}",
                parse_mode=None,
                reply_markup=get_analysis_menu()
            )

    async def gpt_analysis_callback(self, query, context, user_id):
        """GPT анализ через callback"""
        if user_id not in self.user_data:
            await self.safe_edit_callback_message(
                query=query,
                text="❌ Нет данных для анализа",
                parse_mode=None
            )
            return

        # Проверяем rate limit
        allowed, error_message = await self.check_gpt_rate_limit(user_id)
        if not allowed:
            await self.safe_edit_callback_message(
                query=query,
                text=f"❌ *Лимит превышен*\n\n{error_message}",
                parse_mode='Markdown',
                reply_markup=get_analysis_menu()
            )
            return

        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        await self.safe_edit_callback_message(
            query=query,
            text="*ЗАПУСКАЮ GPT АНАЛИЗ...*\n\n"
                 "Искусственный интеллект анализирует ваши данные.\n"
                 "⏳ Это займет 10-30 секунд...",
            parse_mode='Markdown'
        )

        try:
            # Проверяем кэш
            cached_result = self.get_cached_analysis(data['data_hash'], 'gpt')
            if cached_result:
                response = cached_result
                logger.info(f"[{user_id}] Использован кэшированный GPT анализ")
            else:
                # Выполняем GPT анализ
                gpt_result = self.analyzer.gpt_analysis(df)
                response = self.format_gpt_response(gpt_result, filename)

            # Разбиваем на части если длинный
            MESSAGE_LIMIT = 3500  # Безопасный лимит для Telegram
            if len(response) > MESSAGE_LIMIT:
                parts = self.split_long_message(response, MESSAGE_LIMIT)
                for i, part in enumerate(parts):
                    if i == 0:
                        await self.safe_edit_callback_message(
                            query=query,
                            text=part,
                            parse_mode='Markdown',
                            reply_markup=get_analysis_menu() if i == len(parts) - 1 else None
                        )
                    else:
                        await self.safe_send_message(
                            chat_id=user_id,
                            text=part,
                            parse_mode='Markdown',
                            context=context
                        )
            else:
                await self.safe_edit_callback_message(
                    query=query,
                    text=response,
                    parse_mode='Markdown',
                    reply_markup=get_analysis_menu()
                )

            # Обновляем счетчик GPT запросов
            self.db.increment_gpt_requests(user_id)

            # Логируем анализ в БД
            self.db.log_analysis(
                user_id=user_id,
                filename=filename,
                file_hash=data['data_hash'],
                record_count=len(df),
                columns_count=len(df.columns),
                analysis_type='gpt',
                gpt_used=True
            )

            logger.info(f"[{user_id}] GPT анализ выполнен успешно")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{user_id}] Ошибка GPT анализа: {error_msg}")

            if "API" in error_msg or "key" in error_msg.lower() or "openai" in error_msg.lower():
                error_display = """
❌ *ОШИБКА GPT АНАЛИЗА*

*Причина:* Не настроен OpenAI API ключ

*КАК ИСПРАВИТЬ:*
1. Получите API ключ на platform.openai.com
2. Добавьте в файл `.env`:
   OPENAI_API_KEY=sk-ваш_ключ_здесь
3. Перезапустите бота

*АЛЬТЕРНАТИВА:*
Используйте веб-интерфейс с уже настроенным GPT анализом
                """
            else:
                error_display = f"❌ *ОШИБКА GPT АНАЛИЗА:*\n\n{error_msg[:300]}"

            await self.safe_edit_callback_message(
                query=query,
                text=error_display,
                parse_mode='Markdown',
                reply_markup=get_analysis_menu()
            )

    def format_gpt_response(self, gpt_result, filename):
        """Форматирование GPT ответа"""
        response = f"*GPT АНАЛИЗ: {filename}*\n\n"
        response += "=" * 40 + "\n\n"

        # Добавляем результат GPT анализа
        response += gpt_result

        response += "\n" + "=" * 40 + "\n\n"
        response += "*КЛЮЧЕВЫЕ ВЫВОДЫ:*\n\n"

        # Добавляем рекомендации
        recommendations = [
            "*Используйте веб-интерфейс* для визуализации",
            "*Интегрируйте с AmoCRM* для полной аналитики",
            "*Настройте регулярные отчеты* для мониторинга",
            "*Включите автоматический анализ* в настройках"
        ]

        for rec in recommendations:
            response += f"• {rec}\n"

        response += "\n*ДЛЯ УГЛУБЛЕННОГО АНАЛИЗА:*\n"
        response += "1. Загрузите исторические данные (2+ года)\n"
        response += "2. Добавьте сегментацию клиентов\n"
        response += "3. Включите операционные метрики\n"
        response += "4. Интегрируйте с CRM системой"

        return response

    def split_long_message(self, text, max_length=3500):
        """Разбивка длинного сообщения на части"""
        parts = []
        while len(text) > max_length:
            # Ищем хорошее место для разрыва
            split_pos = text.rfind('\n\n', 0, max_length)
            if split_pos == -1:
                split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            parts.append(text[:split_pos])
            text = text[split_pos:].lstrip()
        parts.append(text)
        return parts

    async def full_report_callback(self, query, context, user_id):
        """Генерация полного отчета через callback"""
        if user_id not in self.user_data:
            await self.safe_edit_callback_message(
                query=query,
                text="❌ Нет данных для отчета",
                parse_mode=None
            )
            return

        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        await self.safe_edit_callback_message(
            query=query,
            text="*СОЗДАЮ GPT ОТЧЕТ...*\n\n"
                 "Генерирую профессиональный отчет с анализом...",
            parse_mode='Markdown'
        )

        temp_path = None
        try:
            # Выполняем анализ для отчета
            basic_analysis = self.analyzer.basic_analysis(df)
            gpt_analysis = self.analyzer.gpt_analysis(
                df) if GPT_AVAILABLE else "GPT анализ недоступен. Настройте API ключ."

            # Создаем отчет
            report = self.create_gpt_report(df, filename, basic_analysis, gpt_analysis)

            # Сохраняем временный файл
            temp_path = self.temp_dir / f"report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(report)

            # Отправляем файл
            await context.bot.send_document(
                chat_id=user_id,
                document=open(temp_path, 'rb'),
                filename=f"GPT_Report_{filename.replace('.', '_')}.md",
                caption=f"*GPT ОТЧЕТ: {filename}*\n\nПолный анализ от AI Business Auditor",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )

            await self.safe_edit_callback_message(
                query=query,
                text="✅ *GPT ОТЧЕТ СОЗДАН!*\n\n"
                     "Проверьте файл в чате 📎",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )

            # Логируем в БД
            self.db.log_analysis(
                user_id=user_id,
                filename=filename,
                file_hash=data['data_hash'],
                record_count=len(df),
                columns_count=len(df.columns),
                analysis_type='full_report'
            )

            logger.info(f"[{user_id}] Отчет создан: {temp_path}")

        except Exception as e:
            logger.error(f"[{user_id}] Ошибка создания отчета: {e}")
            await self.safe_edit_callback_message(
                query=query,
                text=f"❌ Ошибка создания отчета: {str(e)[:100]}",
                parse_mode=None,
                reply_markup=get_main_menu()
            )
        finally:
            # Удаляем временный файл
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл: {e}")

    def create_gpt_report(self, df, filename, basic_analysis, gpt_analysis):
        """Создание GPT отчета"""
        report = f"# 📊 GPT ОТЧЕТ: {filename}\n\n"
        report += f"*Дата анализа:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"*Записей:* {len(df):,}\n"
        report += f"*Колонок:* {len(df.columns)}\n\n"

        report += "## 📈 ОБЩАЯ СВОДКА\n\n"
        if 'summary' in basic_analysis:
            report += f"{basic_analysis['summary']}\n\n"

        report += "## 🤖 GPT АНАЛИЗ\n\n"
        report += f"{gpt_analysis}\n\n"

        report += "## 📊 КЛЮЧЕВЫЕ МЕТРИКИ\n\n"
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            report += "| Показатель | Среднее | Сумма | Мин | Макс |\n"
            report += "|------------|---------|-------|-----|------|\n"
            for col in numeric_cols[:5]:
                report += f"| {col} | {df[col].mean():.2f} | {df[col].sum():.2f} | {df[col].min():.2f} | {df[col].max():.2f} |\n"
            report += "\n"

        report += "## 💡 РЕКОМЕНДАЦИИ\n\n"
        recommendations = [
            "1. **Внедрите систему мониторинга** ключевых метрик",
            "2. **Настройте регулярные отчеты** для отслеживания динамики",
            "3. **Интегрируйте данные** с CRM системой (AmoCRM)",
            "4. **Автоматизируйте сбор данных** для актуальности анализа",
            "5. **Внедрите предиктивную аналитику** для прогнозирования"
        ]

        for rec in recommendations:
            report += f"{rec}\n"

        report += "\n## 🎯 ПЛАН ДЕЙСТВИЙ\n\n"
        report += "### Неделя 1-2:\n"
        report += "- [ ] Настройка автоматических отчетов\n"
        report += "- [ ] Интеграция с AmoCRM\n"
        report += "- [ ] Определение KPI\n\n"

        report += "### Неделя 3-4:\n"
        report += "- [ ] Внедрение дашбордов\n"
        report += "- [ ] Обучение команды\n"
        report += "- [ ] Оптимизация процессов\n\n"

        report += "---\n"
        report += "*Сгенерировано AI Business Auditor с использованием GPT*\n"
        report += "*Для уточнения анализа используйте веб-интерфейс*"

        return report

    async def perform_gpt_analysis(self, update, context, user_id):
        """GPT анализ через сообщение"""
        if user_id not in self.user_data:
            await update.message.reply_text("❌ Сначала загрузите файл")
            return

        # Проверяем rate limit
        allowed, error_message = await self.check_gpt_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(
                f"❌ *Лимит превышен*\n\n{error_message}",
                parse_mode='Markdown'
            )
            return

        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        status_msg = await update.message.reply_text(
            "*ЗАПУСКАЮ GPT АНАЛИЗ...*\n\n"
            "AI анализирует ваши данные...",
            parse_mode='Markdown'
        )

        try:
            gpt_result = self.analyzer.gpt_analysis(df)
            response = self.format_gpt_response(gpt_result, filename)

            # Отправляем частями если нужно
            MESSAGE_LIMIT = 3500
            if len(response) > MESSAGE_LIMIT:
                parts = self.split_long_message(response, MESSAGE_LIMIT)
                for i, part in enumerate(parts):
                    if i == 0:
                        success = await self.safe_edit_message_text(
                            message=status_msg,
                            text=part,
                            parse_mode='Markdown',
                            context=context
                        )
                        if not success:
                            # Если не удалось отредактировать, отправляем новое сообщение
                            await self.safe_send_message(
                                chat_id=user_id,
                                text=part,
                                parse_mode='Markdown',
                                context=context
                            )
                    else:
                        await self.safe_send_message(
                            chat_id=user_id,
                            text=part,
                            parse_mode='Markdown',
                            context=context
                        )
            else:
                success = await self.safe_edit_message_text(
                    message=status_msg,
                    text=response,
                    parse_mode='Markdown',
                    reply_markup=get_main_menu(),
                    context=context
                )

                if not success:
                    # Если не удалось отредактировать, отправляем новое сообщение
                    await self.safe_send_message(
                        chat_id=user_id,
                        text=response,
                        parse_mode='Markdown',
                        reply_markup=get_main_menu(),
                        context=context
                    )

            # Обновляем счетчик GPT запросов
            self.db.increment_gpt_requests(user_id)

            # Логируем анализ в БД
            self.db.log_analysis(
                user_id=user_id,
                filename=filename,
                file_hash=data['data_hash'],
                record_count=len(df),
                columns_count=len(df.columns),
                analysis_type='gpt',
                gpt_used=True
            )

        except Exception as e:
            logger.error(f"[{user_id}] Ошибка GPT анализа в сообщении: {e}")
            error_msg = str(e)[:200] if len(str(e)) > 200 else str(e)

            success = await self.safe_edit_message_text(
                message=status_msg,
                text=f"❌ Ошибка GPT анализа: {error_msg}",
                parse_mode=None,
                reply_markup=get_main_menu(),
                context=context
            )

            if not success:
                await update.message.reply_text(
                    f"❌ Ошибка GPT анализа: {error_msg}",
                    reply_markup=get_main_menu()
                )

    async def generate_gpt_report(self, update, context, user_id):
        """Генерация отчета через сообщение"""
        if user_id not in self.user_data:
            await update.message.reply_text("❌ Нет данных для отчета")
            return

        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        # Создаем простой отчет
        report = f"# Отчет: {filename}\n\n"
        report += f"Дата: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        report += f"📊 Записей: {len(df):,}\n"
        report += f"📋 Колонок: {len(df.columns)}\n\n"

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            report += "📈 **Основные показатели:**\n\n"
            for col in numeric_cols[:3]:
                report += f"**{col}:**\n"
                report += f"- Среднее: {df[col].mean():.2f}\n"
                report += f"- Сумма: {df[col].sum():.2f}\n"
                report += f"- Мин/Макс: {df[col].min():.2f} / {df[col].max():.2f}\n\n"

        report += "💡 *Для полного GPT отчета:*\n"
        report += "1. Используйте веб-интерфейс\n"
        report += "2. Настройте OpenAI API ключ\n"
        report += "3. Запустите полный анализ через меню бота"

        temp_path = None
        try:
            temp_path = self.temp_dir / f"simple_report_{user_id}_{datetime.now().strftime('%H%M%S')}.md"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(report)

            await context.bot.send_document(
                chat_id=user_id,
                document=open(temp_path, 'rb'),
                filename=f"simple_report_{filename.replace('.', '_')}.md",
                caption="📋 Быстрый отчет по вашим данным",
                reply_markup=get_main_menu()
            )

            # Логируем в БД
            self.db.log_analysis(
                user_id=user_id,
                filename=filename,
                file_hash=data['data_hash'],
                record_count=len(df),
                columns_count=len(df.columns),
                analysis_type='simple_report'
            )

        except Exception as e:
            logger.error(f"[{user_id}] Ошибка генерации быстрого отчета: {e}")
            await update.message.reply_text(
                f"❌ Ошибка создания отчета: {str(e)[:100]}",
                reply_markup=get_main_menu()
            )
        finally:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass

    async def show_recommendations(self, query, context, user_id):
        """Показать рекомендации"""
        if user_id not in self.user_data:
            await self.safe_edit_callback_message(
                query=query,
                text="❌ Нет данных для рекомендаций",
                parse_mode=None
            )
            return

        data = self.user_data[user_id]
        df = data['df']

        recommendations = [
            "*СОБИРАЙТЕ БОЛЬШЕ ДАННЫХ:* Чем больше история, тем точнее анализ",
            "*ИНТЕГРИРУЙТЕ С CRM:* Объедините данные о продажах и клиентах",
            "*АВТОМАТИЗИРУЙТЕ ОТЧЕТЫ:* Настройте регулярную генерацию",
            "*ИСПОЛЬЗУЙТЕ GPT АНАЛИЗ:* Получайте AI рекомендации",
            "*ОПРЕДЕЛИТЕ KPI:* Четкие метрики для оценки эффективности"
        ]

        response = "*РЕКОМЕНДАЦИИ ДЛЯ ВАШИХ ДАННЫХ*\n\n"
        response += f"На основе анализа {len(df)} записей:\n\n"

        for i, rec in enumerate(recommendations[:4], 1):
            response += f"{i}. {rec}\n"

        response += "\n*СЛЕДУЮЩИЕ ШАГИ:*\n"
        response += "1. Нажмите 🤖 GPT Анализ\n"
        response += "2. Создайте полный отчет\n"
        response += "3. Интегрируйте с AmoCRM"

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_analysis_menu()
        )

    async def show_details(self, query, context, user_id):
        """Показать детали данных"""
        if user_id not in self.user_data:
            await self.safe_edit_callback_message(
                query=query,
                text="❌ Нет данных",
                parse_mode=None
            )
            return

        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        response = f"*ДЕТАЛИ ДАННЫХ: {filename}*\n\n"

        response += "*СТРУКТУРА:*\n"
        response += f"• Типы данных:\n"

        for col in df.columns[:5]:
            dtype = str(df[col].dtype)
            response += f"  {col}: {dtype}\n"

        if len(df.columns) > 5:
            response += f"  ... и еще {len(df.columns) - 5} колонок\n"

        response += f"\n*РАЗМЕР:* {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB\n"
        response += f"*ПРОПУСКИ:* {df.isnull().sum().sum()}\n"

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            response += f"\n*ЧИСЛОВЫЕ ПОКАЗАТЕЛИ:* {len(numeric_cols)} колонок\n"

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_analysis_menu()
        )

    async def show_visualization_info(self, query, context):
        """Информация о визуализации"""
        response = "*ВИЗУАЛИЗАЦИЯ ДАННЫХ*\n\n"
        response += "Полные возможности визуализации доступны в веб-интерфейсе:\n\n"
        response += "streamlit run ui/streamlit_app.py\n\n"
        response += "*Доступные графики:*\n"
        response += "• Линейные графики трендов\n"
        response += "• Столбчатые диаграммы\n"
        response += "• Точечные диаграммы корреляций\n"
        response += "• Гистограммы распределений\n"
        response += "• Heatmaps взаимосвязей\n\n"
        response += "Telegram бот фокусируется на текстовых анализах и рекомендациях."

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_analysis_menu()
        )

    async def show_my_stats_callback(self, query, context, user_id):
        """Показать статистику пользователя через callback"""
        stats = self.db.get_user_stats(user_id)

        requests_today, last_request, reset_date = self.db.check_rate_limit(user_id)

        stats_text = f"""
*ВАША СТАТИСТИКА*

*Общая статистика:*
• Всего анализов: {stats['total_analyses']}
• GPT анализов: {stats['gpt_analyses']}
• Последний анализ: {stats['last_analysis'] or 'Нет данных'}

*Текущие лимиты:*
• GPT запросов сегодня: {requests_today}/{self.MAX_GPT_REQUESTS_PER_DAY}
• Сброс лимита: {reset_date}

*Рекомендации:*
1. Используйте веб-интерфейс для полной статистики
2. Оптимизируйте анализ с помощью GPT
3. Интегрируйте с AmoCRM
        """

        await self.safe_edit_callback_message(
            query=query,
            text=stats_text,
            parse_mode='Markdown',
            reply_markup=get_analysis_menu()
        )

    async def show_amocrm_integration(self, update, context):
        """Показать интеграцию с AmoCRM"""
        response = """
*AMOCRM ИНТЕГРАЦИЯ*

*ДОСТУПНЫЕ ВОЗМОЖНОСТИ:*
• Анализ сделок и воронок
• Сегментация клиентов
• Прогноз выручки
• Эффективность менеджеров

*КАК НАСТРОИТЬ:*
1. Создайте интеграцию в AmoCRM
2. Получите access_token
3. Добавьте в .env файл:
   AMOCRM_ACCESS_TOKEN=ваш_токен
   AMOCRM_SUBDOMAIN=ваш_домен
4. Перезапустите бота

*ДЕМО-РЕЖИМ:* Уже доступен в боте
*ПОЛНАЯ ВЕРСИЯ:* В веб-интерфейсе
        """

        await self.safe_send_message(
            chat_id=update.effective_chat.id,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_main_menu(),
            context=context
        )

    async def show_gpt_tips(self, update, context):
        """Показать GPT советы"""
        tips = [
            "*ДЛЯ ЛУЧШЕГО GPT АНАЛИЗА:* Добавьте колонки с датами",
            "*ЧИСЛОВЫЕ ДАННЫЕ:* GPT лучше анализирует количественные показатели",
            "*КОНТЕКСТ:* Укажите тип бизнеса в комментарии к данным",
            "*ИСТОРИЯ:* Данные за 2+ года дают лучшие прогнозы",
            "*ЦЕЛИ:* Четко определите, что хотите оптимизировать"
        ]

        tip = random.choice(tips)

        response = f"*GPT СОВЕТ*\n\n{tip}\n\n"
        response += "*ХОТИТЕ ЛУЧШИЙ АНАЛИЗ?*\n"
        response += "1. Загрузите структурированные данные\n"
        response += "2. Включите финансовые показатели\n"
        response += "3. Используйте веб-интерфейс для полного функционала"

        await self.safe_send_message(
            chat_id=update.effective_chat.id,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_main_menu(),
            context=context
        )

    async def show_gpt_settings(self, update, context):
        """Показать настройки GPT"""
        status = "НАСТРОЕН" if GPT_AVAILABLE else "ТРЕБУЕТ НАСТРОЙКИ"

        response = f"*НАСТРОЙКИ GPT АНАЛИЗА*\n\n"
        response += f"Статус: {status}\n\n"

        response += "*ТЕКУЩИЕ НАСТРОЙКИ:*\n"
        response += f"• Модель: {self.gpt_settings['model']}\n"
        response += f"• Температура: {self.gpt_settings['temperature']}\n"
        response += f"• Макс. токенов: {self.gpt_settings['max_tokens']}\n\n"

        if not GPT_AVAILABLE:
            response += "❌ *GPT АНАЛИЗ НЕ ДОСТУПЕН*\n\n"
            response += "*ПРИЧИНА:* Нет OpenAI API ключа\n\n"
            response += "*КАК ИСПРАВИТЬ:*\n"
            response += "1. Получите ключ на platform.openai.com\n"
            response += "2. Добавьте в .env файл:\n"
            response += "   OPENAI_API_KEY=sk-ваш_ключ\n"
            response += "3. Перезапустите бота\n\n"
            response += "*АЛЬТЕРНАТИВА:* Используйте веб-интерфейс"

        await self.safe_send_message(
            chat_id=update.effective_chat.id,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_gpt_settings_menu(),
            context=context
        )

    async def show_model_settings(self, query, context):
        """Показать настройки модели"""
        response = f"""
*НАСТРОЙКИ МОДЕЛИ GPT*

Текущая модель: {self.gpt_settings['model']}

*Доступные модели:*
• GPT-3.5 Turbo - быстрый и экономичный
• GPT-4 - более умный и точный
• GPT-4 Turbo - баланс скорости и качества
• GPT-4o - последняя и самая мощная

*Рекомендации:*
• Для быстрого анализа: GPT-3.5 Turbo
• Для точного анализа: GPT-4
• Для сложных задач: GPT-4 Turbo или GPT-4o

Выберите модель:
        """

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_model_settings_menu()
        )

    async def set_model(self, query, context, model_name):
        """Установить модель GPT"""
        self.gpt_settings['model'] = model_name

        response = f"""
✅ *МОДЕЛЬ УСТАНОВЛЕНА*

Новая модель: {model_name}

Настройки сохранены. Они будут использоваться в следующих GPT анализах.

*Примечание:* Для применения изменений может потребоваться перезапуск бота.
        """

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_gpt_settings_menu()
        )

    async def show_context_settings(self, query, context):
        """Показать настройки контекста"""
        response = f"""
*НАСТРОЙКИ КОНТЕКСТА АНАЛИЗА*

*Текущие настройки:*
• Температура: {self.gpt_settings['temperature']}
• Макс. токенов: {self.gpt_settings['max_tokens']}

*Температура:* 
• 0.0 - более детерминированные ответы
• 0.7 - баланс креативности и точности
• 1.0 - более креативные ответы

*Макс. токенов:* 
• 500-1000 для кратких ответов
• 1000-2000 для детальных анализов
• 2000-4000 для сложных отчетов

*Для изменения настроек добавьте в config.py:*
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
        """

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_gpt_settings_menu()
        )

    async def show_api_key_help(self, query, context):
        """Помощь по настройке API ключа"""
        response = """
*НАСТРОЙКА OPENAI API КЛЮЧА*

*ШАГИ:*
1. Перейдите на platform.openai.com
2. Войдите в аккаунт (или создайте)
3. Перейдите в раздел API Keys
4. Нажмите "Create new secret key"
5. Скопируйте ключ (начинается с sk-)

*ДОБАВЛЕНИЕ В ПРОЕКТ:*
1. Откройте файл `.env` в корне проекта
2. Добавьте строку:
   OPENAI_API_KEY=sk-ваш_ключ_здесь
3. Сохраните файл
4. Перезапустите бота

*СТОИМОСТЬ:*
• Первые $5 бесплатно (новые аккаунты)
• ~$0.002 за 1K токенов (~750 слов)
• ~$0.02 за типичный анализ

*ВАЖНО:*
• Никому не передавайте ваш ключ
• Храните его в .env файле (не в коде)
• Следите за расходом в кабинете OpenAI

*ПОДДЕРЖКА:* @alex_lyubovenko
        """

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_gpt_settings_menu()
        )

    async def back_to_settings(self, query, context):
        """Вернуться к настройкам"""
        status = "НАСТРОЕН" if GPT_AVAILABLE else "ТРЕБУЕТ НАСТРОЙКИ"

        response = f"*НАСТРОЙКИ GPT АНАЛИЗА*\n\n"
        response += f"Статус: {status}\n\n"

        response += "*ТЕКУЩИЕ НАСТРОЙКИ:*\n"
        response += f"• Модель: {self.gpt_settings['model']}\n"
        response += f"• Температура: {self.gpt_settings['temperature']}\n"
        response += f"• Макс. токенов: {self.gpt_settings['max_tokens']}\n\n"

        if not GPT_AVAILABLE:
            response += "❌ *GPT АНАЛИЗ НЕ ДОСТУПЕН*\n\n"
            response += "*ПРИЧИНА:* Нет OpenAI API ключа\n\n"
            response += "*КАК ИСПРАВИТЬ:*\n"
            response += "1. Получите ключ на platform.openai.com\n"
            response += "2. Добавьте в .env файл:\n"
            response += "   OPENAI_API_KEY=sk-ваш_ключ\n"
            response += "3. Перезапустите бота\n\n"
            response += "*АЛЬТЕРНАТИВА:* Используйте веб-интерфейс"

        await self.safe_edit_callback_message(
            query=query,
            text=response,
            parse_mode='Markdown',
            reply_markup=get_gpt_settings_menu()
        )

    async def back_to_main(self, query, context):
        """Вернуться в главное меню"""
        await self.safe_edit_callback_message(
            query=query,
            text="*ГЛАВНОЕ МЕНЮ*",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )

    async def cancel_operation(self, query, context, user_id):
        """Отмена операции через callback"""
        if user_id in self.user_data:
            # Очищаем данные пользователя
            self.user_data.pop(user_id, None)

        await self.safe_edit_callback_message(
            query=query,
            text="✅ Операция отменена. Все временные данные удалены.",
            parse_mode=None,
            reply_markup=get_main_menu()
        )

    # ========== ЗАПУСК БОТА ==========
    def run(self):
        """Запуск бота"""
        try:
            # Создаем Application
            application = Application.builder().token(TOKEN).build()

            # Обработчики команд
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("cancel", self.cancel_command))
            application.add_handler(CommandHandler("stats", self.stats_command))
            application.add_handler(CommandHandler("admin_stats", self.admin_stats_command))

            # Обработчики callback
            application.add_handler(CallbackQueryHandler(self.handle_callback))

            # Обработчики документов
            application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

            # Обработчики текстовых сообщений (последними)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            # Обработка ошибок
            async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                logger.error(f"Ошибка: {context.error}", exc_info=True)
                if update and update.effective_user:
                    try:
                        await context.bot.send_message(
                            chat_id=update.effective_user.id,
                            text="❌ Произошла ошибка. Попробуйте позже."
                        )
                    except:
                        pass

            application.add_error_handler(error_handler)

            # Информация о запуске
            print("\n" + "=" * 60)
            print("🚀 GPT BUSINESS AUDITOR BOT ЗАПУЩЕН!")
            print("=" * 60)
            print(f"📊 GPT анализ: {'✅ ДОСТУПЕН' if GPT_AVAILABLE else '⚠️ ТРЕБУЕТ НАСТРОЙКИ'}")
            print(f"👤 Админ: {ADMIN_ID if ADMIN_ID else 'Не настроен'}")
            print(f"📁 Макс. размер файла: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB")
            print(f"🗄️  База данных: {self.db.db_path}")
            print(f"📊 Rate limit: {self.MAX_GPT_REQUESTS_PER_DAY} запросов/день")
            print("=" * 60)
            print("\n📱 Откройте Telegram")
            print("🔍 Найдите вашего бота")
            print("💬 Напишите /start")
            print("🤖 Используйте GPT анализ")
            print("👋 Ctrl+C для остановки")
            print("\n" + "=" * 60)

            # Запуск бота
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )

        except KeyboardInterrupt:
            print("\n👋 Бот остановлен пользователем")
        except Exception as e:
            logger.critical(f"Критическая ошибка при запуске бота: {e}")
            print(f"\n❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Инициализация GPT Business Auditor Bot...")

    try:
        # Проверяем токен перед запуском
        if not TOKEN or TOKEN == "your_actual_bot_token_here":
            print("\n❌ ОШИБКА: Токен бота не настроен!")
            print("   Добавьте TELEGRAM_BOT_TOKEN в .env файл")
            print("   Пример .env файла:")
            print("   TELEGRAM_BOT_TOKEN=ваш_новый_токен_от_botfather")
            print("   TELEGRAM_ADMIN_ID=427861947")
            print("   OPENAI_API_KEY=sk-ваш_ключ_openai")
            sys.exit(1)

        bot = GPTBusinessBot()
        bot.run()

    except Exception as e:
        print(f"\n❌ Ошибка при инициализации бота: {e}")