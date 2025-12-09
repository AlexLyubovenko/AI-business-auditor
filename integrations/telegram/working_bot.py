# integrations/telegram/working_bot.py
"""
Рабочая версия Telegram бота AI Business Auditor
"""

import os
import logging
import pandas as pd
import tempfile
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ========== НАСТРОЙКА ==========
TOKEN = "8457812721:AAEO-db6iR0oimab8VNuMwiwG5XPMLKdQqQ"
ADMIN_ID = "427861947"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== КЛАВИАТУРЫ ==========
def get_main_menu():
    """Главное меню"""
    keyboard = [
        [KeyboardButton("📊 Анализ файла")],
        [KeyboardButton("🤖 GPT Анализ"), KeyboardButton("📋 Отчеты")],
        [KeyboardButton("🏢 AmoCRM"), KeyboardButton("💡 Советы")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_analysis_menu():
    """Меню анализа"""
    buttons = [
        [InlineKeyboardButton("📊 Быстрый анализ", callback_data="quick_analysis")],
        [InlineKeyboardButton("📄 Сгенерировать отчет", callback_data="generate_report")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)


# ========== ОБРАБОТЧИКИ ==========
class WorkingBot:
    def __init__(self):
        self.user_sessions = {}
        print("=" * 50)
        print("🤖 AI Business Auditor Bot - Рабочая версия")
        print("=" * 50)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_text = """
🤖 *AI Business Auditor Bot*

*Доступные функции:*
• 📊 Анализ CSV/Excel файлов
• 📋 Генерация отчетов  
• 🏢 Демо AmoCRM данные
• 💡 Бизнес-советы

Отправьте файл или используйте меню:
        """
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        text = update.message.text

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "📤 *Загрузите файл для анализа*\n\n"
                "Поддерживаемые форматы:\n"
                "• CSV (табличные данные)\n"
                "• Excel (.xlsx, .xls)\n\n"
                "Просто отправьте мне файл!",
                parse_mode='Markdown'
            )

        elif text == "🤖 GPT Анализ":
            await update.message.reply_text(
                "🤖 *GPT Анализ*\n\n"
                "Эта функция доступна в веб-интерфейсе.\n"
                "Запустите: `streamlit run ui/streamlit_app.py`",
                parse_mode='Markdown'
            )

        elif text == "📋 Отчеты":
            user_id = update.effective_user.id
            if user_id in self.user_sessions and 'dataframe' in self.user_sessions[user_id]:
                await update.message.reply_text(
                    "📄 *Генерация отчетов*\n\n"
                    "Для ваших данных доступны отчеты:",
                    reply_markup=get_analysis_menu()
                )
            else:
                await update.message.reply_text(
                    "📄 *Генерация отчетов*\n\n"
                    "Сначала загрузите файл через 📊 Анализ файла",
                    reply_markup=get_main_menu()
                )

        elif text == "🏢 AmoCRM":
            # Демо данные AmoCRM
            leads = self._generate_demo_leads(5)

            response = "🏢 *AmoCRM (демо-данные):*\n\n"
            response += "*Последние сделки:*\n"
            for i, lead in enumerate(leads, 1):
                response += f"{i}. {lead['name']}\n"
                response += f"   💰 {lead['price']:,} руб. | 📊 {lead['status']}\n\n"

            response += "*Для реальной интеграции:*\n"
            response += "1. Добавьте AMOCRM_ACCESS_TOKEN в .env\n"
            response += "2. Перезапустите бота"

            await update.message.reply_text(
                response,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif text == "💡 Советы":
            tips = [
                "💰 *Увеличьте средний чек* на 10% с помощью up-sell",
                "📈 *Анализируйте CAC и LTV* для оптимизации маркетинга",
                "🤝 *Улучшите удержание*: лояльные клиенты дешевле новых",
                "📊 *Автоматизируйте отчетность* - экономия 5+ часов в неделю",
                "🎯 *Фокусируйтесь* на 20% клиентов, дающих 80% прибыли"
            ]

            tip = random.choice(tips)

            await update.message.reply_text(
                f"💡 *Бизнес-совет:*\n\n{tip}\n\n"
                f"Нажмите кнопку снова для нового совета!",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif text == "❓ Помощь":
            help_text = """
❓ *Помощь по боту*

*Основные функции:*
• 📊 **Анализ файла** - загрузите CSV/Excel для анализа
• 📋 **Отчеты** - генерация отчетов по данным
• 🏢 **AmoCRM** - демо-данные и интеграция
• 💡 **Советы** - бизнес-рекомендации

*Как использовать:*
1. Нажмите 📊 Анализ файла
2. Отправьте CSV или Excel файл
3. Выберите тип анализа
4. Получите результат

*Пример CSV файла:*
            Месяц,Выручка,Расходы
            Январь,100000,70000
            Февраль,120000,80000
            Март,150000,90000
                        """
            await update.message.reply_text(
                help_text,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработка загруженных файлов"""
            user_id = update.effective_user.id

            # Скачиваем файл
            document = update.message.document
            file = await document.get_file()
            file_name = document.file_name

            # Сохраняем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            await file.download_to_drive(temp_file.name)

            try:
                # Пробуем загрузить как CSV
                try:
                    df = pd.read_csv(temp_file.name)
                except:
                    # Пробуем как Excel
                    try:
                        df = pd.read_excel(temp_file.name)
                    except:
                        await update.message.reply_text(
                            "❌ Неподдерживаемый формат файла. Используйте CSV или Excel.",
                            reply_markup=get_main_menu()
                        )
                        return

                # Сохраняем данные
                self.user_sessions[user_id] = {
                    'dataframe': df,
                    'filename': file_name,
                    'uploaded_at': datetime.now()
                }

                # Анализируем
                analysis = self._simple_analysis(df)

                # Формируем ответ
                response = f"✅ *Файл загружен: {file_name}*\n\n"
                response += f"📊 *Статистика:*\n"
                response += f"• Записей: {len(df):,}\n"
                response += f"• Колонок: {len(df.columns)}\n"

                # Анализ числовых данных
                numeric_cols = df.select_dtypes(include='number').columns
                if len(numeric_cols) > 0:
                    response += f"• Числовых колонок: {len(numeric_cols)}\n"
                    if len(numeric_cols) > 0:
                        col = numeric_cols[0]
                        response += f"• Среднее значение '{col}': {df[col].mean():.2f}\n"

                response += f"\n📈 *Рекомендации:*\n"
                response += f"1. Выберите '📋 Отчеты' для генерации отчета\n"
                response += f"2. Используйте веб-интерфейс для продвинутого анализа\n"
                response += f"3. Интегрируйте с AmoCRM для CRM-аналитики"

                await update.message.reply_text(
                    response,
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

            except Exception as e:
                await update.message.reply_text(
                    f"❌ *Ошибка обработки файла:*\n{str(e)[:100]}",
                    reply_markup=get_main_menu()
                )
            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

        def _simple_analysis(self, df):
            """Простой анализ данных"""
            return {
                'rows': len(df),
                'columns': len(df.columns),
                'numeric_cols': len(df.select_dtypes(include='number').columns),
                'missing_values': df.isnull().sum().sum()
            }

        def _generate_demo_leads(self, count):
            """Генерация демо-сделок"""
            leads = []
            statuses = ['Новая', 'В работе', 'Успешная', 'Закрыта']

            for i in range(1, count + 1):
                leads.append({
                    'id': i,
                    'name': f'Демо сделка #{i}',
                    'price': random.randint(10000, 500000),
                    'status': random.choice(statuses),
                    'created_at': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
                })

            return leads

        async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработка callback-кнопок"""
            query = update.callback_query
            await query.answer()

            user_id = update.effective_user.id
            data = query.data

            if data == "quick_analysis":
                if user_id in self.user_sessions and 'dataframe' in self.user_sessions[user_id]:
                    df = self.user_sessions[user_id]['dataframe']
                    filename = self.user_sessions[user_id]['filename']

                    # Выполняем анализ
                    analysis = self._detailed_analysis(df)

                    response = f"📊 *Детальный анализ: {filename}*\n\n"
                    response += f"📈 *Общая статистика:*\n"
                    response += f"• Записей: {analysis['rows']:,}\n"
                    response += f"• Колонок: {analysis['columns']}\n"
                    response += f"• Пропущенных значений: {analysis['missing']}\n\n"

                    if analysis['numeric_summary']:
                        response += f"📊 *Числовые данные:*\n"
                        for col, stats in analysis['numeric_summary'].items():
                            response += f"• {col}:\n"
                            response += f"  Среднее: {stats['mean']:.2f}\n"
                            response += f"  Сумма: {stats['sum']:,.2f}\n\n"

                    response += "💡 *Что дальше:*\n"
                    response += "1. Сгенерируйте полный отчет\n"
                    response += "2. Загрузите в веб-интерфейс для GPT анализа\n"
                    response += "3. Интегрируйте с AmoCRM"

                    await query.edit_message_text(
                        response,
                        reply_markup=get_analysis_menu(),
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "❌ Нет данных для анализа",
                        reply_markup=get_main_menu()
                    )

            elif data == "generate_report":
                if user_id in self.user_sessions and 'dataframe' in self.user_sessions[user_id]:
                    df = self.user_sessions[user_id]['dataframe']
                    filename = self.user_sessions[user_id]['filename']

                    await query.edit_message_text(
                        "📄 *Генерация отчета...*",
                        parse_mode='Markdown'
                    )

                    # Генерируем отчет
                    report = self._generate_report(df, filename)

                    # Сохраняем временный файл
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                        f.write(report)
                        temp_path = f.name

                    # Отправляем файл
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=open(temp_path, 'rb'),
                        filename=f"business_report_{filename}.md",
                        caption=f"📄 Отчет по анализу {filename}",
                        reply_markup=get_main_menu()
                    )

                    # Удаляем временный файл
                    os.unlink(temp_path)

                    await query.edit_message_text(
                        "✅ *Отчет сгенерирован и отправлен!*",
                        reply_markup=get_main_menu()
                    )
                else:
                    await query.edit_message_text(
                        "❌ Нет данных для отчета",
                        reply_markup=get_main_menu()
                    )

            elif data == "back_to_main":
                await query.edit_message_text(
                    "🏠 *Главное меню*",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

        def _detailed_analysis(self, df):
            """Детальный анализ данных"""
            analysis = {
                'rows': len(df),
                'columns': len(df.columns),
                'missing': df.isnull().sum().sum(),
                'numeric_summary': {}
            }

            # Анализ числовых колонок
            numeric_cols = df.select_dtypes(include='number').columns
            for col in numeric_cols:
                analysis['numeric_summary'][col] = {
                    'mean': float(df[col].mean()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'sum': float(df[col].sum()),
                    'std': float(df[col].std())
                }

            return analysis

        def _generate_report(self, df, filename):
            """Генерация отчета"""
            report = f"# 📊 Отчет AI Business Auditor\n\n"
            report += f"*Файл:* {filename}\n"
            report += f"*Дата анализа:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

            report += "## 📈 Общая информация\n\n"
            report += f"- **Количество записей:** {len(df):,}\n"
            report += f"- **Количество колонок:** {len(df.columns)}\n"
            report += f"- **Пропущенные значения:** {df.isnull().sum().sum()}\n\n"

            report += "## 🔍 Структура данных\n\n"
            report += "| Колонка | Тип данных | Пример значения |\n"
            report += "|---------|------------|-----------------|\n"

            for col in df.columns[:5]:  # Показываем первые 5 колонок
                dtype = str(df[col].dtype)
                sample = str(df[col].iloc[0]) if len(df) > 0 else "N/A"
                if len(sample) > 30:
                    sample = sample[:30] + "..."
                report += f"| {col} | {dtype} | {sample} |\n"

            if len(df.columns) > 5:
                report += f"| ... и еще {len(df.columns) - 5} колонок | ... | ... |\n"

            report += "\n## 📊 Статистика\n\n"

            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                report += "### Числовые показатели:\n\n"
                for col in numeric_cols[:3]:  # Показываем первые 3 числовые колонки
                    report += f"**{col}:**\n"
                    report += f"- Среднее: {df[col].mean():.2f}\n"
                    report += f"- Мин/Макс: {df[col].min():.2f} / {df[col].max():.2f}\n"
                    report += f"- Сумма: {df[col].sum():,.2f}\n"
                    report += f"- Стандартное отклонение: {df[col].std():.2f}\n\n"

            report += "## 💡 Рекомендации\n\n"
            report += "1. **Для точного анализа** используйте веб-интерфейс AI Business Auditor\n"
            report += "2. **Для AI-рекомендаций** включите GPT анализ в настройках\n"
            report += "3. **Для CRM аналитики** настройте интеграцию с AmoCRM\n"
            report += "4. **Для автоматизации** настройте регулярные отчеты\n\n"

            report += "---\n"
            report += "*Сгенерировано AI Business Auditor Telegram Bot*\n"

            return report

            # ========== ЗАПУСК БОТА ==========

        def setup_handlers(self, application):
            """Настройка обработчиков"""
            # Команды
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.start_command))

            # Callback запросы
            application.add_handler(CallbackQueryHandler(self.handle_callback))

            # Документы
            application.add_handler(MessageHandler(
                filters.Document.ALL,
                self.handle_document
            ))

            # Текстовые сообщения
            application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            ))

        async def post_init(self, application):
            """После инициализации"""
            logger.info("🤖 Бот запущен и готов к работе!")

            # Отправляем сообщение админу
            try:
                await application.bot.send_message(
                    chat_id=int(ADMIN_ID),
                    text="✅ AI Business Auditor Bot запущен!\n\n"
                         "Функции:\n"
                         "• 📊 Анализ файлов\n"
                         "• 📋 Генерация отчетов\n"
                         "• 🏢 Демо AmoCRM\n"
                         "• 💡 Бизнес-советы\n\n"
                         "Напишите /start для начала"
                )
                print(f"✅ Сообщение отправлено админу {ADMIN_ID}")
            except Exception as e:
                print(f"⚠️  Не удалось отправить сообщение админу: {e}")

        def run(self):
            """Запуск бота"""
            application = Application.builder().token(TOKEN).post_init(self.post_init).build()

            self.setup_handlers(application)

            # Обработка ошибок
            async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                logger.error(f"Ошибка: {context.error}")
                if update and update.effective_message:
                    try:
                        await update.effective_message.reply_text(
                            "❌ Произошла ошибка. Попробуйте позже.",
                            reply_markup=get_main_menu()
                        )
                    except:
                        pass

            application.add_error_handler(error_handler)

            # Запуск
            print("🚀 Запуск рабочего бота...")
            print("📱 Откройте Telegram и найдите @ai_business_auditor_bot")
            print("👋 Для остановки нажмите Ctrl+C")
            print("=" * 50)

            application.run_polling(allowed_updates=Update.ALL_TYPES)

        # ========== ТОЧКА ВХОДА ==========
        def main():
            """Основная функция"""
            print("""
                🤖 AI BUSINESS AUDITOR - TELEGRAM BOT
                ======================================
                Версия: Рабочая с полным функционалом
                Статус: Готов к демонстрации
                ======================================
                """)

            try:
                bot = WorkingBot()
                bot.run()
            except KeyboardInterrupt:
                print("\n\n👋 Бот остановлен")
            except Exception as e:
                print(f"❌ Ошибка запуска: {e}")
                import traceback
                traceback.print_exc()

        if __name__ == "__main__":
            main()