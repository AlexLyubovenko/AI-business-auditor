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

# Импорт telegram модулей ДО main функции
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
        CallbackContext,
        CallbackQueryHandler
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error("❌ python-telegram-bot не установлен")
    logger.error("Выполните: pip install python-telegram-bot==20.7")

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

# Глобальная переменная для хранения последнего файла пользователя
user_files = {}  # {user_id: {'file_path': path, 'df': df, 'file_name': name}}

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

        if not TELEGRAM_AVAILABLE:
            logger.error("❌ python-telegram-bot не установлен")
            return

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

    except Exception as e:
        logger.error(f"❌ Критическая ошибка бота: {e}")
        raise

async def setup_handlers(application):
    """Настройка всех обработчиков"""

    # Обработчик callback-запросов (для кнопок)
    async def button_callback(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        data = query.data

        logger.info(f"🔘 [{user_id}] Нажата кнопка: {data}")

        if data == 'analyze_gpt':
            # Анализ с помощью GPT
            if user_id in user_files and user_files[user_id]:
                file_info = user_files[user_id]
                await query.edit_message_text(
                    text="🤖 *Запускаю GPT анализ...*\n\nПожалуйста, подождите...",
                    parse_mode='Markdown'
                )

                # Получаем DataFrame
                df = file_info['df']
                file_name = file_info['file_name']

                # Запускаем GPT анализ
                await gpt_analysis_handler(query, df, file_name, user_id)
            else:
                await query.edit_message_text(
                    text="❌ *Нет данных для анализа*\n\nПожалуйста, сначала загрузите файл.",
                    parse_mode='Markdown'
                )

        elif data == 'show_charts':
            # Показать графики
            await query.edit_message_text(
                text="📊 *Графики*\n\nДля просмотра графиков используйте веб-интерфейс:\n"
                     f"{os.getenv('RENDER_EXTERNAL_URL', 'https://ai-business-auditor.onrender.com')}",
                parse_mode='Markdown'
            )

        elif data == 'connect_amocrm':
            # Подключить AmoCRM
            await query.edit_message_text(
                text="🔗 *Интеграция с AmoCRM*\n\n"
                     "Для настройки интеграции с AmoCRM:\n"
                     "1. Получите доступ в AmoCRM\n"
                     "2. Настройте API ключ\n"
                     "3. Используйте веб-интерфейс для подключения",
                parse_mode='Markdown'
            )

        elif data == 'export_report':
            # Экспорт отчета
            await query.edit_message_text(
                text="📄 *Экспорт отчета*\n\n"
                     "Отчеты доступны в веб-интерфейсе:\n"
                     f"{os.getenv('RENDER_EXTERNAL_URL', 'https://ai-business-auditor.onrender.com')}\n\n"
                     "Там вы можете экспортировать в PDF, Excel или PNG.",
                parse_mode='Markdown'
            )

        elif data == 'back_to_menu':
            # Назад в меню
            await show_main_menu(query)

    # Команда /start
    async def start_command(update: Update, context: CallbackContext):
        user = update.effective_user
        logger.info(f"👤 Пользователь {user.id} ({user.username}) запустил бота")

        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("📊 Анализ файла", callback_data='analyze_file')],
            [InlineKeyboardButton("🤖 GPT Анализ", callback_data='analyze_gpt')],
            [InlineKeyboardButton("📈 Графики", callback_data='show_charts')],
            [InlineKeyboardButton("🔗 AmoCRM", callback_data='connect_amocrm')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

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
2️⃣ Используйте кнопки для анализа
3️⃣ Получите AI рекомендации

📁 *Форматы:* CSV, Excel, JSON
⚙️ *Макс. размер:* 10 MB

*Веб-версия:* {os.getenv('RENDER_EXTERNAL_URL', 'https://ai-business-auditor.onrender.com')}

Используйте кнопки ниже или команды:
/help - Справка
/status - Статус системы
        """

        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    async def show_main_menu(query):
        """Показать главное меню"""
        keyboard = [
            [InlineKeyboardButton("📊 Анализ файла", callback_data='analyze_file')],
            [InlineKeyboardButton("🤖 GPT Анализ", callback_data='analyze_gpt')],
            [InlineKeyboardButton("📈 Графики", callback_data='show_charts')],
            [InlineKeyboardButton("🔗 AmoCRM", callback_data='connect_amocrm')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="🎛️ *Главное меню*\n\nВыберите действие:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    # Команда /help
    async def help_command(update: Update, context: CallbackContext):
        help_text = """
*Помощь по AI Business Auditor Bot*

*📋 Команды:*
/start - Запустить бота
/help - Эта справка
/status - Статус бота и системы

*📁 Как использовать:*
1. Отправьте файл с данными (CSV/Excel/JSON)
2. Получите автоматический анализ
3. Используйте кнопки для дополнительного анализа

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
    async def status_command(update: Update, context: CallbackContext):
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
    async def handle_document(update: Update, context: CallbackContext):
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

            # Сохраняем файл для пользователя
            user_files[user_id] = {
                'file_path': temp_file_path,
                'df': df,
                'file_name': file_name
            }

            # Анализируем данные
            analysis_text = await analyze_dataframe(df, file_name)

            # Создаем клавиатуру для действий с файлом
            keyboard = [
                [InlineKeyboardButton("🤖 GPT Анализ", callback_data='analyze_gpt')],
                [InlineKeyboardButton("📊 Графики", callback_data='show_charts')],
                [InlineKeyboardButton("📄 Экспорт отчета", callback_data='export_report')],
                [InlineKeyboardButton("🔗 AmoCRM", callback_data='connect_amocrm')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Формируем финальное сообщение
            result_text = (
                f"✅ *Анализ завершен!*\n\n"
                f"👤 Пользователь: {user_name}\n"
                f"📁 Файл: `{file_name}`\n"
                f"📊 Записей: *{len(df):,}*\n"
                f"📋 Колонок: *{len(df.columns)}*\n"
                f"📈 Числовых колонок: *{len(df.select_dtypes(include='number').columns)}*\n\n"
                f"{analysis_text}\n\n"
                f"💡 *Выберите дальнейшие действия:*"
            )

            # Отправляем результат с кнопками
            await status_msg.edit_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=reply_markup,
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
            elif "Can't parse entities" in error_msg:
                error_display = "Ошибка форматирования текста. Упростите имя файла."
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
                    f"4. Что файл не пустой\n"
                    f"5. Имя файла не содержит спецсимволов",
                    parse_mode='Markdown'
                )
            except Exception as edit_error:
                logger.error(f"Ошибка редактирования сообщения: {edit_error}")
                await update.message.reply_text(
                    f"❌ Ошибка анализа файла: {error_display[:100]}"
                )

        finally:
            # Удаляем временный файл (но сохраняем DataFrame в памяти)
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    # Оставляем только DataFrame в памяти
                    if user_id in user_files:
                        user_files[user_id]['file_path'] = None
                except Exception as cleanup_error:
                    logger.warning(f"Не удалось удалить временный файл: {cleanup_error}")

    async def gpt_analysis_handler(query, df, file_name, user_id):
        """Обработчик GPT анализа"""
        try:
            await query.edit_message_text(
                text="🧠 *Запускаю GPT анализ...*\n\nЭто может занять несколько секунд...",
                parse_mode='Markdown'
            )

            # Выполняем GPT анализ
            gpt_result = await perform_gpt_analysis(df, file_name)

            # Создаем клавиатуру для дальнейших действий
            keyboard = [
                [InlineKeyboardButton("📊 Графики", callback_data='show_charts')],
                [InlineKeyboardButton("📄 Экспорт отчета", callback_data='export_report')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text=f"🤖 *GPT Анализ завершен!*\n\n"
                     f"📁 Файл: `{file_name}`\n"
                     f"📊 Записей: {len(df):,}\n\n"
                     f"{gpt_result}\n\n"
                     f"💡 *Дальнейшие действия:*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

            logger.info(f"✅ [{user_id}] GPT анализ успешен")

        except Exception as error:
            logger.error(f"❌ [{user_id}] Ошибка GPT анализа: {error}")
            await query.edit_message_text(
                text=f"❌ *Ошибка GPT анализа*\n\n"
                     f"Причина: {str(error)[:200]}\n\n"
                     f"*Проверьте:*\n"
                     f"• Наличие OPENAI_API_KEY\n"
                     f"• Доступ к интернету\n"
                     f"• Лимиты OpenAI API",
                parse_mode='Markdown'
            )

    # Обработка текстовых сообщений
    async def handle_text(update: Update, context: CallbackContext):
        text = update.message.text
        user_id = update.effective_user.id

        logger.info(f"💬 [{user_id}] Текст: {text}")

        # Ответы на приветствия
        greetings = ['привет', 'hello', 'hi', 'здравствуй', 'добрый день', 'добрый вечер']

        if any(greet in text.lower() for greet in greetings):
            # Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("📊 Анализ файла", callback_data='analyze_file')],
                [InlineKeyboardButton("🤖 GPT Анализ", callback_data='analyze_gpt')],
                [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"👋 Привет, {update.effective_user.first_name or 'друг'}!\n\n"
                f"Я AI Business Auditor Bot 🤖\n"
                f"Отправьте мне файл с данными для анализа (CSV, Excel, JSON)\n\n"
                f"Или используйте кнопки ниже:",
                parse_mode=None,
                reply_markup=reply_markup
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
            # Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("📊 Анализ файла", callback_data='analyze_file')],
                [InlineKeyboardButton("🤖 GPT Анализ", callback_data='analyze_gpt')],
                [InlineKeyboardButton("📈 Графики", callback_data='show_charts')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "🤔 Я понимаю команды, файлы и кнопки.\n\n"
                "*Доступные команды:*\n"
                "• /start - Запустить бота\n"
                "• /help - Справка\n"
                "• /status - Статус системы\n\n"
                "*Или используйте кнопки:*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))

    # Обработчик callback-запросов (кнопки)
    application.add_handler(CallbackQueryHandler(button_callback))

    # Обработчик документов (ВАЖНО: должен быть до текстовых)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Обработчик текстовых сообщений (последний)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик ошибок
    async def error_handler(update: Update, context: CallbackContext):
        logger.error(f"Ошибка в обработчике: {context.error}")

        # Логируем детали ошибки
        if hasattr(context.error, '__dict__'):
            for key, value in context.error.__dict__.items():
                logger.error(f"  {key}: {value}")

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
            return pd.read_json(file_path, orient='records')
        else:
            raise ValueError(f"Неизвестный формат: {file_ext}")
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {e}")
        raise ValueError(f"Ошибка чтения файла: {str(e)}")

async def analyze_dataframe(df, filename):
    """Базовый анализ DataFrame"""
    try:
        response = ""

        response += "*📊 БАЗОВЫЙ АНАЛИЗ:*\n"
        response += f"• Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        response += f"• Всего записей: {len(df):,}\n"
        response += f"• Колонок: {len(df.columns)}\n"

        # Типы данных
        response += "\n*ТИПЫ ДАННЫХ:*\n"
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

        # Категориальные колонки
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            response += f"\n*ТЕКСТОВЫЕ КОЛОНКИ:*\n"
            for col in categorical_cols[:2]:
                unique_count = df[col].nunique()
                response += f"• `{col}`: {unique_count} уникальных значений\n"

        return response

    except Exception as error:
        logger.error(f"Ошибка анализа DataFrame: {error}")
        return f"⚠️ Ошибка анализа данных: {str(error)[:200]}"

async def perform_gpt_analysis(df, filename):
    """Выполнение GPT анализа через DataAnalyzer"""
    try:
        # Пробуем импортировать DataAnalyzer
        sys.path.insert(0, str(root_dir))

        # Проверяем доступность OpenAI API
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key or not openai_key.startswith('sk-'):
            return "⚠️ *GPT анализ недоступен*\n\nДобавьте OPENAI_API_KEY в настройках Render"

        try:
            from agents.analyzer import DataAnalyzer

            analyzer = DataAnalyzer()

            # Выполняем GPT анализ
            gpt_result = analyzer.gpt_analysis(df)

            if isinstance(gpt_result, str):
                if len(gpt_result) > 1500:
                    return f"{gpt_result[:1500]}...\n\n[Продолжение в веб-версии]"
                return gpt_result
            elif isinstance(gpt_result, dict):
                response = "*🤖 GPT Анализ:*\n\n"
                for key, value in gpt_result.items():
                    if isinstance(value, str) and value:
                        response += f"• *{key}:* {value[:200]}...\n"
                return response
            else:
                return "✅ GPT анализ выполнен. Подробности в веб-версии."

        except ImportError:
            # Если DataAnalyzer не доступен, используем простой OpenAI запрос
            return await simple_gpt_analysis(df, filename)

    except Exception as error:
        logger.error(f"Ошибка GPT анализа: {error}")
        return f"❌ Ошибка GPT анализа: {str(error)[:200]}"

async def simple_gpt_analysis(df, filename):
    """Простой GPT анализ через OpenAI API напрямую"""
    try:
        import openai

        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            return "⚠️ OpenAI API ключ не настроен"

        # Создаем промпт для анализа
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        prompt = f"""
Проанализируй эти бизнес-данные:
Файл: {filename}
Количество записей: {len(df)}
Колонок: {len(df.columns)}

Числовые колонки: {', '.join(numeric_cols[:5])}
Текстовые колонки: {', '.join(categorical_cols[:5])}

Основные статистики:
{df.describe().to_string() if len(numeric_cols) > 0 else 'Нет числовых данных'}

Дайте краткий анализ:
1. Основные тренды
2. Потенциальные проблемы
3. Рекомендации по оптимизации
4. Ключевые метрики

Ответ должен быть кратким и по делу.
"""

        client = openai.OpenAI(api_key=openai_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты AI бизнес-аналитик. Анализируй данные и давай практические рекомендации."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as error:
        logger.error(f"Ошибка простого GPT анализа: {error}")
        return f"⚠️ Ошибка при обращении к OpenAI API: {str(error)[:200]}"

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