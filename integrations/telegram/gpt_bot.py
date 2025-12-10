"""
Telegram бот AI Business Auditor с настоящим GPT анализом
Упрощенная версия для работы в контейнере Render
"""

import os
import sys
import logging
import asyncio
import pandas as pd
import tempfile
from datetime import datetime
from pathlib import Path

# ДОБАВЛЯЕМ ПУТИ для корректных импортов
current_dir = Path(__file__).parent.absolute()
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))  # Добавляем корень проекта
sys.path.insert(0, '/app')  # Для Render

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальные настройки
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xls', 'json']

async def main():
    """Основная асинхронная функция бота"""
    try:
        logger.info("🤖 Инициализация Telegram бота...")

        # Проверяем токен
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
            logger.info("💡 Добавьте TELEGRAM_BOT_TOKEN в настройках Render")
            return

        # Импортируем telegram модули ВНУТРИ функции
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
            ContextTypes
        )

        # Создаем приложение
        application = Application.builder().token(token).build()

        # Регистрируем обработчики
        await setup_handlers(application)

        logger.info("✅ Обработчики зарегистрированы")

        # Запускаем polling
        await application.initialize()
        await application.start()

        # Начинаем polling с настройками для контейнера
        await application.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            allowed_updates=Update.ALL_TYPES
        )

        # Получаем информацию о боте
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Бот запущен и готов к работе!")
        logger.info(f"👤 Имя бота: @{bot_info.username}")

        # Бесконечный цикл
        while True:
            await asyncio.sleep(3600)

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Убедитесь, что установлен python-telegram-bot==20.7")
        logger.error("Выполните: pip install python-telegram-bot==20.7")
        raise
    except Exception as e:
        logger.error(f"❌ Критическая ошибка бота: {e}")
        raise

async def setup_handlers(application):
    """Настройка всех обработчиков"""
    from telegram import Update
    from telegram.ext import ContextTypes

    # Команда /start
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info(f"👤 Пользователь {user.id} ({user.username}) запустил бота")

        welcome_text = f"""
🤖 *AI Business Auditor Bot*

👋 Привет, {user.first_name or 'друг'}!

*Доступные функции:*
📊 Анализ CSV/Excel/JSON файлов
🤖 GPT анализ бизнес-данных
💡 Рекомендации по оптимизации
📈 Генерация отчетов

*Как начать:*
1️⃣ Отправьте мне файл с данными
2️⃣ Получите автоматический анализ
3️⃣ Используйте GPT для детальных рекомендаций

📁 *Форматы:* CSV, Excel, JSON
⚙️ *Макс. размер:* 10 MB

*Веб-версия:* {os.getenv('RENDER_EXTERNAL_URL', 'https://ai-business-auditor.onrender.com')}

*Команды:*
/start - Запустить бота
/help - Справка
/status - Статус системы
        """

        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    # Команда /help
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
*Помощь по AI Business Auditor Bot*

*📋 Команды:*
/start - Запустить бота
/help - Эта справка
/status - Статус бота и системы

*📁 Как использовать:*
1. Отправьте файл с данными (CSV/Excel/JSON)
2. Получите автоматический анализ
3. Используйте GPT для детальных рекомендаций

*✅ Требования к файлам:*
• Поддерживаемые форматы: .csv, .xlsx, .xls, .json
• Максимальный размер: 10 MB
• Рекомендуются структурированные бизнес-данные

*🔧 Примеры данных:*
• Финансовые отчеты
• Данные о продажах
• Метрики бизнеса
• Статистика клиентов

*🌐 Веб-версия:*
Полный функционал с графиками и отчетами:
https://ai-business-auditor.onrender.com

*💬 Поддержка:*
Для вопросов и помощи
        """

        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    # Команда /status
    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        # Проверяем доступность сервисов
        openai_status = "✅ настроен" if os.getenv('OPENAI_API_KEY') else "⚠️ не настроен"
        web_status = "✅ работает" if os.getenv('RENDER_EXTERNAL_URL') else "⚠️ проверьте"

        status_text = f"""
*📊 Статус системы AI Business Auditor*

*👤 Ваш ID:* {user.id}
*⏰ Время сервера:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*🔧 Сервисы:*
• Telegram бот: ✅ работает
• OpenAI GPT: {openai_status}
• Веб-интерфейс: {web_status}
• База данных: ✅ готова

*📈 Статистика:*
• Запущен: {datetime.now().strftime('%Y-%m-%d %H:%M')}
• Режим: {'🚀 Продакшен' if os.getenv('RENDER') else '🛠️ Разработка'}
• Память: Проверка...

*🔗 Ссылки:*
• Веб-интерфейс: {os.getenv('RENDER_EXTERNAL_URL', 'Не настроен')}
• GitHub: https://github.com/AlexLyubovenko/AI-business-auditor

*💡 Что делать если не работает:*
1. Проверьте токен бота в настройках Render
2. Убедитесь что добавлен OPENAI_API_KEY
3. Перезапустите сервис в панели Render
        """

        await update.message.reply_text(
            status_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    # Обработка файлов
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_name = update.effective_user.username or update.effective_user.first_name
        document = update.message.document
        file_name = document.file_name

        logger.info(f"📥 [{user_id}] Загрузка файла: {file_name} ({document.file_size} байт)")

        # Проверяем размер
        if document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ *Файл слишком большой*\n\n"
                f"Файл: {file_name}\n"
                f"Размер: {document.file_size/1024/1024:.1f} MB\n"
                f"Лимит: {MAX_FILE_SIZE/1024/1024:.0f} MB\n\n"
                f"*Совет:* Разделите данные на несколько файлов",
                parse_mode='Markdown'
            )
            return

        # Проверяем формат
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

        if file_ext not in ALLOWED_EXTENSIONS:
            await update.message.reply_text(
                f"❌ *Неподдерживаемый формат*\n\n"
                f"Файл: {file_name}\n"
                f"Формат: .{file_ext}\n\n"
                f"*Поддерживаемые:* {', '.join(ALLOWED_EXTENSIONS)}",
                parse_mode='Markdown'
            )
            return

        # Отправляем статус
        status_msg = await update.message.reply_text(
            f"📥 *Загружаю файл...*\n\n"
            f"Файл: `{file_name}`\n"
            f"Размер: {document.file_size/1024:.0f} KB\n"
            f"Формат: .{file_ext}\n\n"
            f"⏳ Анализирую данные...",
            parse_mode='Markdown'
        )

        temp_file_path = None
        try:
            # Скачиваем файл
            file = await document.get_file()

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=f'.{file_ext}', delete=False) as tmp:
                temp_file_path = tmp.name
                await file.download_to_drive(temp_file_path)

            # Загружаем данные
            df = await load_dataframe(temp_file_path, file_ext)

            if df.empty or len(df) == 0:
                raise ValueError("Файл пуст или не содержит данных")

            # Анализируем данные
            analysis_text = await analyze_dataframe(df, file_name)

            # Формируем финальное сообщение
            result_text = (
                f"✅ *Анализ завершен!*\n\n"
                f"👤 Пользователь: {user_name}\n"
                f"📁 Файл: `{file_name}`\n"
                f"📊 Записей: *{len(df):,}*\n"
                f"📋 Колонок: *{len(df.columns)}*\n"
                f"📈 Числовых колонок: *{len(df.select_dtypes(include='number').columns)}*\n\n"
                f"{analysis_text}\n\n"
                f"💡 *Дальнейшие действия:*\n"
                f"• Используйте веб-интерфейс для графиков\n"
                f"• Настройте GPT анализ в конфигурации\n"
                f"• Интегрируйте с AmoCRM для полной аналитики"
            )

            # Отправляем результат
            await status_msg.edit_text(
                result_text,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

            logger.info(f"✅ [{user_id}] Анализ успешен: {len(df)} записей")

        except Exception as error:
            error_msg = str(error)
            logger.error(f"❌ [{user_id}] Ошибка анализа: {error_msg}")

            # Формируем понятное сообщение об ошибке
            if "No such file or directory" in error_msg:
                error_display = "Ошибка чтения файла. Проверьте путь."
            elif "decode" in error_msg.lower():
                error_display = "Ошибка кодировки файла. Используйте UTF-8."
            elif "empty" in error_msg.lower():
                error_display = "Файл пуст или не содержит данных."
            else:
                error_display = error_msg[:200]

            # Пробуем отредактировать сообщение об ошибке
            try:
                await status_msg.edit_text(
                    f"❌ *Ошибка анализа*\n\n"
                    f"Файл: `{file_name}`\n\n"
                    f"*Причина:* {error_display}\n\n"
                    f"*Проверьте:*\n"
                    f"1. Корректность формата данных\n"
                    f"2. Кодировку файла (рекомендуется UTF-8)\n"
                    f"3. Разделители в CSV (запятая или точка с запятой)\n"
                    f"4. Что файл не пустой",
                    parse_mode='Markdown'
                )
            except Exception as edit_error:
                logger.error(f"Ошибка редактирования сообщения: {edit_error}")
                await update.message.reply_text(
                    f"❌ Ошибка анализа файла: {error_display[:100]}"
                )

        finally:
            # Удаляем временный файл
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Не удалось удалить временный файл: {cleanup_error}")

    # Обработка текстовых сообщений
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = update.effective_user.id

        logger.info(f"💬 [{user_id}] Текст: {text}")

        # Ответы на приветствия
        greetings = ['привет', 'hello', 'hi', 'здравствуй', 'добрый день', 'добрый вечер']

        if any(greet in text.lower() for greet in greetings):
            await update.message.reply_text(
                f"👋 Привет, {update.effective_user.first_name or 'друг'}!\n\n"
                f"Я AI Business Auditor Bot 🤖\n"
                f"Отправьте мне файл с данными для анализа (CSV, Excel, JSON)\n\n"
                f"Используйте /help для справки",
                parse_mode=None
            )
        elif 'спасибо' in text.lower():
            await update.message.reply_text(
                "🙏 Всегда рад помочь!\n"
                "Если нужен более детальный анализ - используйте веб-версию.",
                parse_mode=None
            )
        elif any(word in text.lower() for word in ['как', 'помощь', 'help', 'что делать']):
            await update.message.reply_text(
                "📋 Используйте команду /help для полной справки\n"
                "Или отправьте файл с данными для начала анализа.",
                parse_mode=None
            )
        else:
            await update.message.reply_text(
                "🤔 Я понимаю команды и файлы.\n\n"
                "*Доступные команды:*\n"
                "• /start - Запустить бота\n"
                "• /help - Справка\n"
                "• /status - Статус системы\n\n"
                "*Или просто отправьте файл* с данными для анализа.",
                parse_mode='Markdown'
            )

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))

    # Обработчик документов (ВАЖНО: должен быть до текстовых)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Обработчик текстовых сообщений (последний)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик ошибок
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Ошибка в обработчике: {context.error}")

        # Пытаемся отправить сообщение об ошибке пользователю
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Произошла ошибка при обработке запроса. Попробуйте позже.",
                    parse_mode=None
                )
            except Exception:
                pass

    application.add_error_handler(error_handler)

async def load_dataframe(file_path, file_ext):
    """Загрузка DataFrame из файла с обработкой ошибок"""
    try:
        if file_ext == 'csv':
            # Пробуем разные кодировки и разделители
            try:
                return pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    return pd.read_csv(file_path, encoding='cp1251')
                except Exception:
                    return pd.read_csv(file_path, encoding='latin1')
        elif file_ext in ['xlsx', 'xls']:
            return pd.read_excel(file_path)
        elif file_ext == 'json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Неизвестный формат: {file_ext}")
    except Exception as e:
        raise ValueError(f"Ошибка чтения файла: {str(e)}")

async def analyze_dataframe(df, filename):
    """Анализ DataFrame с GPT и базовой аналитикой"""
    try:
        response = ""

        # Проверяем доступность анализатора
        try:
            # Пробуем импортировать из agents
            sys.path.insert(0, str(root_dir))
            from agents.analyzer import DataAnalyzer

            logger.info("✅ DataAnalyzer найден, запускаю анализ...")
            analyzer = DataAnalyzer()

            # 1. Базовый анализ
            basic = analyzer.basic_analysis(df)

            response += "*📊 БАЗОВЫЙ АНАЛИЗ:*\n"
            response += f"• Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            response += f"• Всего записей: {len(df):,}\n"
            response += f"• Колонок: {len(df.columns)}\n"

            # Добавляем сводку если есть
            if isinstance(basic, dict) and 'summary' in basic:
                summary = basic['summary']
                if summary and len(summary) > 0:
                    response += f"• Сводка: {summary[:200]}...\n"

            # 2. GPT анализ (если доступен OpenAI)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key.startswith('sk-'):
                try:
                    response += "\n*🤖 GPT АНАЛИЗ:*\n"

                    # Проверяем, есть ли числовые данные для анализа
                    numeric_cols = df.select_dtypes(include='number').columns
                    if len(numeric_cols) > 0:
                        gpt_result = analyzer.gpt_analysis(df)

                        if isinstance(gpt_result, str):
                            response += f"{gpt_result[:400]}..."
                        elif isinstance(gpt_result, dict):
                            # Извлекаем текст из словаря
                            for key, value in gpt_result.items():
                                if isinstance(value, str) and len(value) > 0:
                                    response += f"• {key}: {value[:100]}...\n"
                        else:
                            response += "GPT анализ выполнен. Подробности в веб-версии.\n"
                    else:
                        response += "⚠️ Для GPT анализа нужны числовые данные\n"

                except Exception as gpt_error:
                    logger.warning(f"GPT анализ не удался: {gpt_error}")
                    response += "⚠️ GPT анализ временно недоступен\n"
            else:
                response += "\n*⚠️ GPT АНАЛИЗ:*\n"
                response += "Добавьте OPENAI_API_KEY в настройки Render\n"
                response += "для доступа к AI рекомендациям\n"

            # 3. Статистика по колонкам
            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                response += f"\n*📈 ЧИСЛОВЫЕ КОЛОНКИ ({len(numeric_cols)}):*\n"
                for i, col in enumerate(numeric_cols[:3]):  # Показываем первые 3
                    response += f"{i+1}. `{col}`:\n"
                    response += f"   Среднее: {df[col].mean():.2f}\n"
                    response += f"   Сумма: {df[col].sum():.2f}\n"
                    response += f"   Диапазон: {df[col].min():.2f} - {df[col].max():.2f}\n"

                if len(numeric_cols) > 3:
                    response += f"   ... и еще {len(numeric_cols) - 3} колонок\n"

            # 4. Категориальные колонки
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                response += f"\n*📋 ТЕКСТОВЫЕ КОЛОНКИ ({len(categorical_cols)}):*\n"
                for i, col in enumerate(categorical_cols[:2]):  # Показываем первые 2
                    unique_count = df[col].nunique()
                    response += f"{i+1}. `{col}`: {unique_count} уникальных значений\n"

                if len(categorical_cols) > 2:
                    response += f"   ... и еще {len(categorical_cols) - 2} колонок\n"

        except ImportError as import_error:
            logger.warning(f"DataAnalyzer не найден: {import_error}")

            # Простой анализ без DataAnalyzer
            response += "*📊 ПРОСТОЙ АНАЛИЗ:*\n"
            response += f"• Файл: {filename}\n"
            response += f"• Записей: {len(df):,}\n"
            response += f"• Колонок: {len(df.columns)}\n\n"

            # Типы данных
            response += "*ТИПЫ ДАННЫХ:*\n"
            dtypes = df.dtypes.value_counts()
            for dtype, count in dtypes.items():
                response += f"• {dtype}: {count} колонок\n"

            # Основные статистики для числовых колонок
            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                response += f"\n*ОСНОВНЫЕ МЕТРИКИ:*\n"
                for col in numeric_cols[:3]:
                    response += f"• `{col}`:\n"
                    response += f"  Среднее: {df[col].mean():.2f}\n"
                    response += f"  Сумма: {df[col].sum():.2f}\n"
                    response += f"  Мин/Макс: {df[col].min():.2f}/{df[col].max():.2f}\n"

            response += f"\n*💡 Для полного анализа:*\n"
            response += f"Установите зависимости и настройте DataAnalyzer\n"

        # Добавляем рекомендации
        response += f"\n*🎯 РЕКОМЕНДАЦИИ:*\n"
        recommendations = [
            "1. Используйте веб-интерфейс для графиков",
            "2. Настройте GPT анализ с OpenAI API",
            "3. Интегрируйте с AmoCRM для CRM-аналитики",
            "4. Экспортируйте отчеты в PDF/Excel"
        ]

        for rec in recommendations:
            response += f"• {rec}\n"

        return response

    except Exception as error:
        logger.error(f"Ошибка анализа DataFrame: {error}")
        return f"⚠️ Ошибка анализа данных: {str(error)[:200]}"

if __name__ == "__main__":
    # Проверяем наличие обязательных переменных
    required_vars = ['TELEGRAM_BOT_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"❌ Отсутствуют обязательные переменные: {missing}")
        logger.info("💡 Добавьте в настройках Render: Environment → Add Variable")
        logger.info("Получите токен через @BotFather в Telegram")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК AI BUSINESS AUDITOR BOT")
    logger.info("=" * 60)
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🤖 Токен бота: {'✅ установлен' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ отсутствует'}")
    logger.info(f"🧠 OpenAI GPT: {'✅ доступен' if os.getenv('OPENAI_API_KEY') else '⚠️ не настроен'}")
    logger.info(f"🌐 Веб-интерфейс: {os.getenv('RENDER_EXTERNAL_URL', '⚠️ не настроен')}")
    logger.info("=" * 60)
    logger.info("📱 Откройте Telegram и напишите /start боту")
    logger.info("=" * 60)

    try:
        # Запускаем бота
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        sys.exit(1)