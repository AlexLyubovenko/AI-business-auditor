# integrations/telegram/one_file_bot.py
"""
Telegram бот AI Business Auditor в одном файле
"""

import os
import sys
import logging
import pandas as pd
import tempfile
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ========== НАСТРОЙКА ==========
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8457812721:AAEO-db6iR0oimab8VNuMwiwG5XPMLKdQqQ")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "427861947")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== КЛАВИАТУРЫ ==========
def get_main_menu():
    keyboard = [
        [KeyboardButton("📊 Анализ файла")],
        [KeyboardButton("🤖 GPT Анализ"), KeyboardButton("📋 Отчеты")],
        [KeyboardButton("🏢 AmoCRM"), KeyboardButton("💡 Советы")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)


def get_file_types_keyboard():
    buttons = [
        [
            InlineKeyboardButton("📁 CSV", callback_data="file_csv"),
            InlineKeyboardButton("📊 Excel", callback_data="file_excel")
        ],
        [
            InlineKeyboardButton("📄 JSON", callback_data="file_json"),
            InlineKeyboardButton("📝 TXT", callback_data="file_txt")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_analysis_options_keyboard():
    buttons = [
        [
            InlineKeyboardButton("📊 Быстрый анализ", callback_data="analysis_quick"),
            InlineKeyboardButton("🤖 GPT анализ", callback_data="analysis_gpt")
        ],
        [
            InlineKeyboardButton("📈 Графики", callback_data="analysis_charts"),
            InlineKeyboardButton("📋 Полный отчет", callback_data="analysis_full")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_files")]
    ]
    return InlineKeyboardMarkup(buttons)


# ========== ДЕМО-КЛИЕНТ AMOCRM ==========
class DemoAmoCRMClient:
    """Демо-клиент AmoCRM в одном файле"""

    def __init__(self, subdomain="demo", access_token="demo_token"):
        self.subdomain = subdomain
        self.access_token = access_token
        self.is_demo = True

    def get_leads(self, limit=20):
        """Получить демо-сделки"""
        leads = []
        statuses = ['Новая', 'В работе', 'Успешная', 'Закрыта', 'Отказ']

        for i in range(1, limit + 1):
            price = random.randint(10000, 500000)
            created_days = random.randint(0, 90)
            created_at = datetime.now() - timedelta(days=created_days)

            lead = {
                'id': i,
                'name': f'Демо сделка #{i}',
                'price': price,
                'status': random.choice(statuses),
                'created_at': created_at.strftime('%Y-%m-%d'),
                'responsible_user_id': random.randint(1, 5),
                'tags': ['VIP'] if price > 300000 else ['Новый'] if i % 5 == 0 else []
            }
            leads.append(lead)

        return leads

    def get_contacts(self, limit=10):
        """Получить демо-контакты"""
        contacts = []
        first_names = ['Иван', 'Алексей', 'Мария', 'Екатерина']
        last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецов']

        for i in range(1, limit + 1):
            contacts.append({
                'id': i,
                'name': f'{random.choice(first_names)} {random.choice(last_names)}',
                'email': f'client{i}@example.com',
                'phone': f'+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}'
            })

        return contacts

    def get_account_info(self):
        """Информация об аккаунте"""
        return {
            'id': 12345,
            'name': 'Демо компания AI Business Auditor',
            'subdomain': self.subdomain,
            'users_count': 5,
            'leads_count': 50,
            'contacts_count': 30,
            'is_demo': True
        }


# ========== АНАЛИЗАТОР ДАННЫХ ==========
class SimpleDataAnalyzer:
    """Упрощенный анализатор данных"""

    def basic_analysis(self, df):
        """Базовый анализ DataFrame"""
        analysis = {
            'record_count': len(df),
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_values': df.isnull().sum().sum(),
            'numeric_summary': {}
        }

        # Анализ числовых колонок
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                analysis['numeric_summary'][col] = {
                    'mean': float(df[col].mean()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'sum': float(df[col].sum())
                }

        # Генерация рекомендаций
        recommendations = []
        if len(df) < 100:
            recommendations.append("Добавьте больше данных для точного анализа")
        if df.isnull().sum().sum() > 0:
            recommendations.append("Обработайте пропущенные значения")
        if len(numeric_cols) > 0:
            recommendations.append("Проанализируйте числовые показатели в деталях")

        analysis['recommendations'] = recommendations
        analysis['summary'] = f"Проанализировано {len(df)} записей, {len(df.columns)} колонок"

        return analysis

    def gpt_analysis(self, df):
        """GPT анализ (демо-версия)"""
        numeric_cols = df.select_dtypes(include='number').columns

        if len(numeric_cols) > 0:
            # Если есть числовые данные
            first_numeric = numeric_cols[0]
            avg_value = df[first_numeric].mean()

            analysis = f"🤖 *GPT Анализ результатов*\n\n"
            analysis += f"📊 **Ключевая метрика:** {first_numeric}\n"
            analysis += f"📈 **Среднее значение:** {avg_value:.2f}\n\n"

            if avg_value > 100000:
                analysis += "💰 *Высокие показатели!* Рекомендуется:\n"
                analysis += "• Инвестировать в развитие\n"
                analysis += "• Оптимизировать расходы\n"
                analysis += "• Масштабировать бизнес\n"
            else:
                analysis += "📉 *Есть потенциал роста!* Рекомендуется:\n"
                analysis += "• Увеличить продажи\n"
                analysis += "• Снизить издержки\n"
                analysis += "• Искать новые рынки\n"
        else:
            analysis = "🤖 *GPT Анализ*\n\n"
            analysis += "Текстовые данные. Для детального анализа загрузите файл с числовыми показателями.\n\n"
            analysis += "💡 *Совет:* Используйте CSV с финансовыми данными для лучшего анализа"

        return analysis


# ========== ГЕНЕРАТОР ОТЧЕТОВ ==========
class SimpleReportGenerator:
    """Упрощенный генератор отчетов"""

    def generate_markdown_report(self, df, analysis):
        """Генерация отчета в Markdown"""
        report = f"# 📊 Отчет AI Business Auditor\n\n"
        report += f"*Дата генерации:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        report += "## 📈 Общая информация\n\n"
        report += f"- **Записей в данных:** {len(df):,}\n"
        report += f"- **Колонок:** {len(df.columns)}\n"
        report += f"- **Пропущенных значений:** {df.isnull().sum().sum()}\n\n"

        report += "## 🔍 Статистика\n\n"
        numeric_cols = df.select_dtypes(include='number').columns

        if len(numeric_cols) > 0:
            report += "### Числовые колонки:\n"
            for col in numeric_cols[:3]:  # Показываем первые 3
                report += f"- **{col}:**\n"
                report += f"  - Среднее: {df[col].mean():.2f}\n"
                report += f"  - Мин/Макс: {df[col].min():.2f} / {df[col].max():.2f}\n"
                report += f"  - Сумма: {df[col].sum():,.2f}\n\n"

        if 'recommendations' in analysis:
            report += "## 💡 Рекомендации\n\n"
            for i, rec in enumerate(analysis['recommendations'], 1):
                report += f"{i}. {rec}\n"

        report += "\n---\n"
        report += "*Сгенерировано AI Business Auditor Telegram Bot*\n"

        return report


# ========== ОСНОВНОЙ КЛАСС БОТА ==========
class OneFileBusinessBot:
    """Telegram бот в одном файле"""

    def __init__(self):
        self.analyzer = SimpleDataAnalyzer()
        self.reporter = SimpleReportGenerator()
        self.amocrm = DemoAmoCRMClient()
        self.user_sessions = {}

        print("=" * 50)
        print("🤖 AI BUSINESS AUDITOR TELEGRAM BOT")
        print("   Версия в одном файле")
        print("=" * 50)
        print(f"✅ Токен: {TOKEN[:10]}...")
        print(f"✅ Admin ID: {ADMIN_ID}")
        print("=" * 50)

    # ========== КОМАНДЫ ==========
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start"""
        welcome_text = """
🤖 *AI Business Auditor Bot*

*Полнофункциональный AI-ассистент для бизнес-анализа*

🎯 *Доступные функции:*
• 📊 Анализ CSV/Excel файлов
• 🤖 GPT-анализ с рекомендациями
• 📋 Профессиональные отчеты
• 🏢 Интеграция с AmoCRM (демо)
• 💡 Бизнес-советы

*Отправьте файл или используйте меню:*
        """
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /help"""
        help_text = """
❓ *Помощь по боту*

*Как использовать:*
1. Нажмите 📊 Анализ файла
2. Отправьте CSV или Excel файл
3. Выберите тип анализа
4. Получите результат

*Поддерживаемые форматы:*
• CSV (табличные данные)
• Excel (.xlsx, .xls)
• JSON (ограниченно)

*Пример файла:*
Дата,Выручка,Расходы,Прибыль
2024-01,100000,70000,30000
2024-02,120000,80000,40000
                """
        await update.message.reply_text(
            help_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

        # ========== ОБРАБОТКА СООБЩЕНИЙ ==========

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        text = update.message.text

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "📤 *Загрузите файл для анализа*\n\nПоддерживаемые форматы: CSV, Excel\n\n"
                "Просто отправьте мне файл!",
                reply_markup=get_file_types_keyboard(),
                parse_mode='Markdown'
            )

        elif text == "🤖 GPT Анализ":
            await update.message.reply_text(
                "🤖 *GPT Анализ*\n\nЗагрузите файл и выберите 'GPT анализ' в меню.",
                parse_mode='Markdown'
            )

        elif text == "📋 Отчеты":
            await update.message.reply_text(
                "📄 *Генерация отчетов*\n\nЗагрузите файл для создания отчета.",
                parse_mode='Markdown'
            )

        elif text == "🏢 AmoCRM":
            leads = self.amocrm.get_leads(5)

            response = "🏢 *AmoCRM (демо-режим):*\n\n"
            response += "*Последние сделки:*\n"
            for lead in leads:
                response += f"• {lead['name']}: {lead['price']:,} руб. ({lead['status']})\n"

            response += "\n*Для реальной интеграции:*\n"
            response += "1. Создайте интеграцию в AmoCRM\n"
            response += "2. Добавьте токен в .env файл\n"
            response += "3. Перезапустите бота"

            await update.message.reply_text(
                response,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif text == "💡 Советы":
            tips = [
                "💰 *Увеличьте средний чек*: Добавьте сопутствующие товары",
                "📈 *Анализируйте метрики*: Отслеживайте LTV и CAC",
                "🤝 *Улучшите сервис*: Снижение оттока на 5% = рост прибыли на 25%",
                "📊 *Автоматизируйте отчеты*: Экономия 5+ часов в неделю"
            ]

            import random
            tip = random.choice(tips)

            await update.message.reply_text(
                f"💡 *Бизнес-совет:*\n\n{tip}\n\n"
                f"Хотите еще совет? Нажмите кнопку снова!",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif text == "❓ Помощь":
            await self.help_command(update, context)

        # ========== ОБРАБОТКА ФАЙЛОВ ==========

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженных файлов"""
        user_id = update.effective_user.id

        # Создаем сессию
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}

        # Скачиваем файл
        document = update.message.document
        file = await document.get_file()
        file_name = document.file_name
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

        # Сохраняем временный файл
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}')
        await file.download_to_drive(temp_file.name)

        try:
            # Загружаем данные
            df = self._load_dataframe(temp_file.name, file_ext)

            # Сохраняем данные
            self.user_sessions[user_id]['dataframe'] = df
            self.user_sessions[user_id]['filename'] = file_name

            # Удаляем временный файл
            os.unlink(temp_file.name)

            # Отправляем подтверждение
            await update.message.reply_text(
                f"✅ *Файл загружен успешно!*\n\n"
                f"📁 *{file_name}*\n"
                f"📊 *Записей:* {len(df):,}\n"
                f"📈 *Колонок:* {len(df.columns)}\n\n"
                f"Выберите тип анализа:",
                reply_markup=get_analysis_options_keyboard(),
                parse_mode='Markdown'
            )

        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."

            await update.message.reply_text(
                f"❌ *Ошибка загрузки:*\n{error_msg}\n\n"
                f"Проверьте формат файла.",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    def _load_dataframe(self, file_path, file_ext):
        """Загрузка DataFrame"""
        if file_ext == 'csv':
            return pd.read_csv(file_path)
        elif file_ext in ['xlsx', 'xls']:
            return pd.read_excel(file_path)
        elif file_ext == 'json':
            return pd.read_json(file_path)
        elif file_ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return pd.DataFrame({'content': [content]})
        else:
            # Пробуем определить автоматически
            try:
                return pd.read_csv(file_path)
            except:
                try:
                    return pd.read_excel(file_path)
                except:
                    raise ValueError(f"Неподдерживаемый формат: {file_ext}")

        # ========== ОБРАБОТКА CALLBACK ==========

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка inline-кнопок"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        data = query.data

        # Навигация
        if data == "back_main":
            await query.edit_message_text(
                "🏠 *Главное меню*",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )
            return

        elif data == "back_to_files":
            await query.edit_message_text(
                "📤 *Загрузите файл для анализа*",
                reply_markup=get_file_types_keyboard(),
                parse_mode='Markdown'
            )
            return

        # Обработка анализа
        if data.startswith("analysis_"):
            await self._handle_analysis(query, user_id, data, context)

    async def _handle_analysis(self, query, user_id, action, context):
        """Обработка анализа"""
        if user_id not in self.user_sessions or 'dataframe' not in self.user_sessions[user_id]:
            await query.edit_message_text(
                "❌ *Нет данных для анализа*",
                reply_markup=get_main_menu()
            )
            return

        df = self.user_sessions[user_id]['dataframe']
        filename = self.user_sessions[user_id]['filename']

        if action == "analysis_quick":
            # Быстрый анализ
            await query.edit_message_text(
                "🔍 *Выполняю быстрый анализ...*",
                parse_mode='Markdown'
            )

            analysis = self.analyzer.basic_analysis(df)
            response = self._format_analysis_response(df, analysis, filename)

            await query.edit_message_text(
                response,
                reply_markup=get_analysis_options_keyboard(),
                parse_mode='Markdown'
            )

        elif action == "analysis_gpt":
            # GPT анализ
            await query.edit_message_text(
                "🤖 *Запускаю GPT-анализ...*",
                parse_mode='Markdown'
            )

            gpt_result = self.analyzer.gpt_analysis(df)

            await query.edit_message_text(
                gpt_result,
                reply_markup=get_analysis_options_keyboard(),
                parse_mode='Markdown'
            )

        elif action == "analysis_full":
            # Полный отчет
            await query.edit_message_text(
                "📄 *Генерирую отчет...*",
                parse_mode='Markdown'
            )

            analysis = self.analyzer.basic_analysis(df)
            report = self.reporter.generate_markdown_report(df, analysis)

            # Сохраняем временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(report)
                temp_path = f.name

            # Отправляем файл
            await context.bot.send_document(
                chat_id=user_id,
                document=open(temp_path, 'rb'),
                filename=f"report_{filename}.md",
                caption=f"📄 Отчет по анализу {filename}",
                reply_markup=get_main_menu()
            )

            # Удаляем временный файл
            os.unlink(temp_path)

            await query.edit_message_text(
                "✅ *Отчет сгенерирован!*\n\nПроверьте файл в чате.",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    def _format_analysis_response(self, df, analysis, filename):
        """Форматирование ответа"""
        response = f"📊 *Анализ: {filename}*\n\n"
        response += f"📈 *Общие метрики:*\n"
        response += f"• Записей: {len(df):,}\n"
        response += f"• Колонок: {len(df.columns)}\n"
        response += f"• Пропущенных значений: {df.isnull().sum().sum()}\n\n"

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            response += f"📊 *Числовые данные ({len(numeric_cols)} колонок):*\n"
            for col in numeric_cols[:3]:
                response += f"• {col}: {df[col].mean():.2f} (среднее)\n"

        if 'recommendations' in analysis and analysis['recommendations']:
            response += f"\n💡 *Рекомендации:*\n"
            for i, rec in enumerate(analysis['recommendations'][:3], 1):
                response += f"{i}. {rec}\n"

        return response

        # ========== ЗАПУСК БОТА ==========

    def setup_handlers(self, application: Application):
        """Настройка обработчиков"""
        # Команды
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))

        # Callback
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

    async def post_init(self, application: Application):
        """После инициализации"""
        logger.info("Бот запущен!")

        # Отправляем сообщение админу
        try:
            await application.bot.send_message(
                chat_id=int(ADMIN_ID),
                text="🤖 AI Business Auditor Bot запущен!\n"
                     "✅ Версия в одном файле\n"
                     "✅ Готов к работе"
            )
        except:
            pass

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
        print("🚀 Запуск бота...")
        print("📱 Откройте Telegram и найдите бота")
        print("👋 Для остановки нажмите Ctrl+C")
        print("=" * 50)

        application.run_polling(allowed_updates=Update.ALL_TYPES)

    # ========== ТОЧКА ВХОДА ==========
    def main():
        """Основная функция"""
        print("""
            🤖 AI BUSINESS AUDITOR - TELEGRAM BOT
            ======================================
            Версия: Все в одном файле
            Статус: Готов к работе
            ======================================
            """)

        try:
            bot = OneFileBusinessBot()
            bot.run()
        except KeyboardInterrupt:
            print("\n\n👋 Бот остановлен")
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        main()