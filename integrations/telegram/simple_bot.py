# integrations/telegram/simple_bot.py
"""
Упрощенная версия бота с гарантированной работой
"""

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

# Используем исправленные обработчики
from .handlers_fixed import MessageHandlersFixed

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SimpleBusinessBot:
    """Упрощенный бот с гарантированной работой"""

    def __init__(self):
        load_dotenv()
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.handlers = MessageHandlersFixed()

        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        from .handlers_fixed import get_main_menu

        welcome_text = """
🤖 *AI Business Auditor Bot* (упрощенная версия)

*Что умеет:*
• 📊 Анализировать CSV/Excel файлы
• 🏢 Показывать демо-данные AmoCRM
• 📄 Генерировать отчеты

Просто отправьте мне файл!
        """
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        await self.start_command(update, context)

    def run(self):
        """Запуск бота"""
        application = Application.builder().token(self.token).build()

        # Команды
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))

        # Обработчики из исправленного модуля
        from .handlers_fixed import get_main_menu

        # Callback-запросы
        application.add_handler(CallbackQueryHandler(self.handlers.handle_callback_query))

        # Документы
        application.add_handler(MessageHandler(
            filters.Document.ALL,
            self.handlers.handle_document
        ))

        # Текстовые сообщения
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handlers.handle_main_menu
        ))

        # Обработка ошибок
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Ошибка: {context.error}")
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Попробуйте позже."
                )

        application.add_error_handler(error_handler)

        # Запуск
        logger.info("🤖 Запуск упрощенного бота...")
        print("=" * 50)
        print("🤖 AI BUSINESS AUDITOR BOT")
        print("   Упрощенная версия с гарантированной работой")
        print("=" * 50)

        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Точка входа"""
    print("🚀 Запуск упрощенного Telegram бота...")

    try:
        bot = SimpleBusinessBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()