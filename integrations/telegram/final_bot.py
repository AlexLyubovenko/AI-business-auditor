# integrations/telegram/final_bot.py
"""
Финальная рабочая версия Telegram бота
"""

print("=" * 50)
print("🚀 ЗАПУСК TELEGRAM БОТА AI BUSINESS AUDITOR")
print("=" * 50)

# Попробуем импортировать с отладкой
try:
    print("1. Импортируем библиотеки...")
    import os
    import logging
    import pandas as pd
    import tempfile
    import random
    from datetime import datetime, timedelta

    print("   ✅ Базовые библиотеки импортированы")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    exit(1)

try:
    print("2. Импортируем Telegram библиотеки...")
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

    print("   ✅ Telegram библиотеки импортированы")
except Exception as e:
    print(f"   ❌ Ошибка Telegram импорта: {e}")
    print("   Установите: pip install python-telegram-bot")
    exit(1)

# ========== КОНСТАНТЫ ==========
TOKEN = "8457812721:AAEO-db6iR0oimab8VNuMwiwG5XPMLKdQqQ"
ADMIN_ID = "427861947"

print(f"✅ Токен: {TOKEN[:15]}...")
print(f"✅ Admin ID: {ADMIN_ID}")


# ========== ПРОСТЫЕ ФУНКЦИИ ==========
def get_simple_menu():
    """Простое меню"""
    keyboard = [[KeyboardButton("📊 Анализ файла")], [KeyboardButton("❓ Помощь")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    print(f"👤 Пользователь {update.effective_user.id} запустил бота")
    await update.message.reply_text(
        "🤖 *AI Business Auditor Bot*\n\n"
        "Я помогу проанализировать ваши бизнес-данные!\n\n"
        "Отправьте мне CSV или Excel файл для анализа.",
        reply_markup=get_simple_menu(),
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 *Помощь:*\n\n"
        "1. Нажмите '📊 Анализ файла'\n"
        "2. Отправьте CSV/Excel файл\n"
        "3. Получите анализ данных\n\n"
        "Пример CSV:\n"
        "Месяц,Выручка,Расходы\n"
        "Январь,100000,70000\n"
        "Февраль,120000,80000",
        reply_markup=get_simple_menu(),
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений"""
    text = update.message.text
    print(f"📨 Сообщение от {update.effective_user.id}: {text}")

    if text == "📊 Анализ файла":
        await update.message.reply_text(
            "📤 Отправьте мне CSV или Excel файл для анализа",
            reply_markup=get_simple_menu()
        )
    elif text == "❓ Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню 👇",
            reply_markup=get_simple_menu()
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка документов"""
    user_id = update.effective_user.id
    file_name = update.message.document.file_name

    print(f"📁 Пользователь {user_id} отправил файл: {file_name}")

    await update.message.reply_text(
        f"📥 Загружаю файл: {file_name}..."
    )

    # Скачиваем файл
    file = await update.message.document.get_file()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
    await file.download_to_drive(temp_file.name)

    try:
        # Пробуем прочитать файл
        try:
            df = pd.read_csv(temp_file.name)
            file_type = "CSV"
        except:
            df = pd.read_excel(temp_file.name)
            file_type = "Excel"

        # Анализируем
        row_count = len(df)
        col_count = len(df.columns)

        response = f"✅ *Файл {file_name} успешно загружен!*\n\n"
        response += f"📊 *Анализ:*\n"
        response += f"• Тип файла: {file_type}\n"
        response += f"• Записей: {row_count:,}\n"
        response += f"• Колонок: {col_count}\n"

        # Анализ числовых данных
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            response += f"• Числовых колонок: {len(numeric_cols)}\n"
            # Показываем первую числовую колонку
            first_col = numeric_cols[0]
            response += f"• Среднее '{first_col}': {df[first_col].mean():.2f}\n"

        response += f"\n🎯 *Что дальше:*\n"
        response += f"1. Используйте веб-интерфейс для полного анализа\n"
        response += f"2. Настройте интеграцию с AmoCRM\n"
        response += f"3. Включите GPT анализ в настройках"

        await update.message.reply_text(
            response,
            reply_markup=get_simple_menu(),
            parse_mode='Markdown'
        )

        print(f"✅ Файл {file_name} проанализирован: {row_count} строк, {col_count} колонок")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ошибка обработки файла: {error_msg}")

        await update.message.reply_text(
            f"❌ *Ошибка обработки файла*\n\n"
            f"Проверьте формат файла. Поддерживаются:\n"
            f"• CSV (разделитель запятая)\n"
            f"• Excel (.xlsx, .xls)\n\n"
            f"Ошибка: {error_msg[:100]}",
            reply_markup=get_simple_menu(),
            parse_mode='Markdown'
        )

    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_file.name)
            print(f"🧹 Временный файл удален")
        except:
            pass


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    print(f"❌ Ошибка бота: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте позже.",
                reply_markup=get_simple_menu()
            )
        except:
            pass


async def post_init(application):
    """После инициализации"""
    print("✅ Бот успешно подключился к Telegram API")

    # Отправляем сообщение админу
    try:
        await application.bot.send_message(
            chat_id=int(ADMIN_ID),
            text="🤖 AI Business Auditor Bot запущен!\n\n"
                 "Бот готов к работе. Отправьте /start для начала."
        )
        print(f"✅ Сообщение отправлено админу {ADMIN_ID}")
    except Exception as e:
        print(f"⚠️ Не удалось отправить сообщение админу: {e}")


# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска"""
    print("\n" + "=" * 50)
    print("🤖 НАСТРОЙКА И ЗАПУСК БОТА...")
    print("=" * 50)

    try:
        # Создаем приложение
        print("1. Создаем приложение Telegram...")
        application = Application.builder().token(TOKEN).post_init(post_init).build()
        print("   ✅ Приложение создано")

        # Добавляем обработчики
        print("2. Настраиваем обработчики...")
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)
        print("   ✅ Обработчики настроены")

        # Запускаем бота
        print("\n" + "=" * 50)
        print("🎉 БОТ УСПЕШНО ЗАПУЩЕН!")
        print("=" * 50)
        print("\n📱 Откройте Telegram и найдите вашего бота")
        print("💬 Напишите /start для начала работы")
        print("👋 Для остановки нажмите Ctrl+C")
        print("\n" + "=" * 50)

        # Запускаем поллинг
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ЗАПУСКА: {e}")
        print("\n🔧 Возможные причины:")
        print("1. Неправильный токен бота")
        print("2. Проблемы с интернет-подключением")
        print("3. Блокировка Telegram в сети")
        print("4. Ошибка в библиотеке python-telegram-bot")

        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()