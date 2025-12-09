# integrations/telegram/minimal_working_bot.py
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = "8457812721:AAEO-db6iR0oimab8VNuMwiwG5XPMLKdQqQ"

async def start(update: Update, context):
    keyboard = [[KeyboardButton("📊 Анализ файла")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 AI Business Auditor Bot\n\nОтправьте файл для анализа",
        reply_markup=reply_markup
    )

async def handle_document(update: Update, context):
    await update.message.reply_text("✅ Файл получен! Функционал анализа будет добавлен.")

def main():
    print("🤖 Запуск минимального бота...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT, start))
    app.run_polling()

if __name__ == "__main__":
    main()