# test_bot_setup.py
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")


async def test_bot():
    print("🤖 Тестирование подключения к Telegram Bot API...")
    print(f"Токен: {TOKEN[:15]}...{TOKEN[-10:]}")
    print(f"Admin ID: {ADMIN_ID}")

    try:
        # Создаем экземпляр бота
        bot = Bot(token=TOKEN)

        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"\n✅ Бот найден:")
        print(f"   Имя: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")

        # Отправляем тестовое сообщение
        print(f"\n📤 Отправка тестового сообщения...")
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="🎉 *AI Business Auditor Bot готов к работе!*\n\n"
                 "✅ Бот успешно настроен\n"
                 "✅ Telegram ID получен\n"
                 "✅ Все системы работают\n\n"
                 "_Теперь можно запускать основного бота с меню_",
            parse_mode='Markdown'
        )
        print("✅ Сообщение отправлено успешно!")

        # Проверяем возможность отправки файлов
        print(f"\n📊 Проверка отправки файла...")

        # Создаем тестовый CSV файл
        import pandas as pd
        import tempfile

        test_data = pd.DataFrame({
            'Дата': ['2024-01', '2024-02', '2024-03'],
            'Выручка': [100000, 120000, 150000],
            'Расходы': [70000, 80000, 90000],
            'Прибыль': [30000, 40000, 60000]
        })

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            test_data.to_csv(f.name, index=False)
            temp_path = f.name

        # Отправляем файл
        await bot.send_document(
            chat_id=ADMIN_ID,
            document=open(temp_path, 'rb'),
            filename="test_data.csv",
            caption="📊 Тестовые данные для анализа"
        )
        print("✅ Файл отправлен успешно!")

        # Очистка
        import os
        os.unlink(temp_path)

        print("\n" + "=" * 50)
        print("🎯 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Бот готов к полноценной работе.")

    except Exception as e:
        print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
        return False

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("AI BUSINESS AUDITOR - TELEGRAM BOT SETUP")
    print("=" * 50)

    success = asyncio.run(test_bot())

    if success:
        print("\n✅ Настройка завершена успешно!")
        print("Теперь можно запускать основного бота:")
        print("python integrations/telegram/run_bot.py")
    else:
        print("\n❌ Настройка не удалась. Проверьте:")
        print("1. Правильность токена в .env файле")
        print("2. Что бот активирован в @BotFather")
        print("3. Интернет-подключение")