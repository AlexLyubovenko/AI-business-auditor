# integrations/telegram/bot.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from .keyboards import get_main_menu
from .handlers import MessageHandlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BusinessAuditorBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.handlers = MessageHandlers()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        welcome_text = """
🤖 *AI Business Auditor Bot*

*Полнофункциональный AI-ассистент для бизнес-анализа*

🎯 *Доступные функции:*
• 📊 Анализ CSV/Excel/JSON файлов
• 🤖 GPT-анализ с AI рекомендациями
• 📋 Профессиональные отчеты
• 📈 Ключевые метрики бизнеса
• 🏢 Интеграция с AmoCRM (демо)
• 💡 Персональные советы

Используйте меню ниже 👇
        """
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        await self.handlers.handle_main_menu(update, context)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка документов"""
        await self.handlers.handle_document(update, context)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback-запросов"""
        await self.handlers.handle_callback_query(update, context)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error(f"Update {update} caused error {context.error}")

        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    def setup_handlers(self, application: Application):
        """Настройка обработчиков"""
        # Команды
        application.add_handler(CommandHandler("start", self.start_command))

        # Callback-запросы (inline кнопки)
        application.add_handler(CallbackQueryHandler(self.handle_callback))

        # Документы (файлы)
        application.add_handler(MessageHandler(
            filters.Document.ALL,
            self.handle_document
        ))

        # Текстовые сообщения
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))

        # Обработка ошибок
        application.add_error_handler(self.error_handler)

    async def post_init(self, application: Application):
        """Действия после инициализации"""
        logger.info("Бот запущен и готов к работе!")

        # Отправляем сообщение админу
        admin_id = os.getenv("TELEGRAM_ADMIN_ID")
        if admin_id:
            try:
                await application.bot.send_message(
                    chat_id=int(admin_id),
                    text="🤖 AI Business Auditor Bot запущен в полном режиме!\n"
                         "✅ Все модули загружены\n"
                         "✅ GPT анализ доступен\n"
                         "✅ Готов к работе!"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение админу: {e}")

    def run(self):
        """Запуск бота"""
        application = Application.builder().token(self.token).post_init(self.post_init).build()

        # Настраиваем обработчики
        self.setup_handlers(application)

        # Запускаем бота
        logger.info("Запуск бота...")
        print("🤖 AI Business Auditor Bot запускается...")
        print("✅ Проверка импортов...")

        application.run_polling(allowed_updates=Update.ALL_TYPES)