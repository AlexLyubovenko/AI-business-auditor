# integrations/telegram/smart_bot.py
"""
Умный Telegram бот AI Business Auditor - компактная версия
"""

import os
import logging
import pandas as pd
import tempfile
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ========== КОНСТАНТЫ ==========
TOKEN = "8457812721:AAEO-db6iR0oimab8VNuMwiwG5XPMLKdQqQ"
ADMIN_ID = "427861947"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== КЛАВИАТУРЫ ==========
def get_main_menu():
    keyboard = [
        [KeyboardButton("📊 Анализ файла"), KeyboardButton("🤖 AI Анализ")],
        [KeyboardButton("📋 Отчет"), KeyboardButton("🏢 AmoCRM")],
        [KeyboardButton("💡 Советы"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_analysis_menu():
    buttons = [
        [InlineKeyboardButton("📊 Быстрый анализ", callback_data="quick")],
        [InlineKeyboardButton("🤖 AI Анализ", callback_data="ai")],
        [InlineKeyboardButton("📋 Создать отчет", callback_data="report")]
    ]
    return InlineKeyboardMarkup(buttons)


# ========== AI АНАЛИЗАТОР ==========
class SmartAnalyzer:
    def analyze(self, df):
        """Умный анализ данных"""
        analysis = {}

        # Базовые метрики
        analysis['rows'] = len(df)
        analysis['cols'] = len(df.columns)
        analysis['numeric_cols'] = df.select_dtypes(include='number').columns.tolist()

        # Детектор трендов
        trends = self._detect_trends(df)
        analysis['trends'] = trends

        # Аномалии
        anomalies = self._find_anomalies(df)
        analysis['anomalies'] = anomalies

        # Рекомендации
        recommendations = self._generate_recommendations(df)
        analysis['recommendations'] = recommendations

        return analysis

    def _detect_trends(self, df):
        """Обнаружение трендов"""
        trends = []
        numeric_cols = df.select_dtypes(include='number').columns

        for col in numeric_cols[:2]:
            try:
                if len(df) >= 3:
                    first = df[col].iloc[:len(df) // 3].mean()
                    last = df[col].iloc[-len(df) // 3:].mean()

                    if first != 0:
                        change = ((last - first) / abs(first)) * 100
                        if abs(change) > 10:
                            direction = "📈 рост" if change > 0 else "📉 снижение"
                            trends.append(f"{col}: {direction} на {abs(change):.1f}%")
            except:
                pass

        return trends if trends else ["Тренды не обнаружены"]

    def _find_anomalies(self, df):
        """Поиск аномалий"""
        anomalies = []
        numeric_cols = df.select_dtypes(include='number').columns

        for col in numeric_cols[:2]:
            try:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR

                outliers = df[(df[col] < lower) | (df[col] > upper)]

                if len(outliers) > 0:
                    pct = len(outliers) / len(df) * 100
                    anomalies.append(f"{col}: {len(outliers)} выбросов ({pct:.1f}%)")
            except:
                pass

        return anomalies if anomalies else ["Аномалий не обнаружено"]

    def _generate_recommendations(self, df):
        """Генерация рекомендаций"""
        recs = []

        if len(df) < 50:
            recs.append("📈 Соберите больше данных (>50 записей)")

        if df.isnull().sum().sum() > 0:
            recs.append("🧹 Обработайте пропущенные значения")

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) >= 2:
            recs.append("📊 Используйте веб-интерфейс для графиков")

        recs.append("🏢 Интегрируйте с AmoCRM для CRM-аналитики")
        recs.append("🤖 Включите GPT анализ в веб-версии")

        return recs


# ========== ГЛАВНЫЙ КЛАСС БОТА ==========
class SmartBusinessBot:
    def __init__(self):
        self.analyzer = SmartAnalyzer()
        self.user_data = {}
        print("🤖 Smart Business Bot инициализирован")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome = """
✨ *AI Business Auditor Bot*

🤖 *Умный помощник для анализа бизнеса*

📊 *Что умею:*
• Анализировать CSV/Excel файлы
• Давать AI рекомендации
• Создавать отчеты
• Работать с AmoCRM

📤 *Отправьте файл для анализа!*
        """
        await update.message.reply_text(
            welcome,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
❓ *Помощь*

📁 *Как использовать:*
1. Нажмите 📊 Анализ файла
2. Отправьте CSV/Excel
3. Выберите тип анализа

📊 *Пример CSV:*
Дата,Выручка,Расходы
2024-01,100000,70000
2024-02,120000,80000

🔧 *Веб-версия:*
`streamlit run ui/streamlit_app.py`
        """
        await update.message.reply_text(
            help_text,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений"""
        text = update.message.text

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "📤 *Отправьте CSV или Excel файл*\n\n"
                "Я проанализирую его и дам рекомендации!",
                parse_mode='Markdown'
            )

        elif text == "🤖 AI Анализ":
            user_id = update.effective_user.id
            if user_id in self.user_data:
                await self._perform_ai_analysis(update, user_id)
            else:
                await update.message.reply_text(
                    "🤖 *Сначала загрузите файл через 📊 Анализ файла*",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

        elif text == "📋 Отчет":
            user_id = update.effective_user.id
            if user_id in self.user_data:
                await self._generate_report(update, context, user_id)
            else:
                await update.message.reply_text(
                    "📋 *Сначала загрузите файл*",
                    reply_markup=get_main_menu()
                )

        elif text == "🏢 AmoCRM":
            await self._show_amocrm(update)

        elif text == "💡 Советы":
            await self._show_tips(update)

        elif text == "❓ Помощь":
            await self.help(update, context)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка файлов"""
        user_id = update.effective_user.id
        file = update.message.document
        file_name = file.file_name

        print(f"📁 {user_id} загрузил: {file_name}")

        # Скачиваем файл
        tg_file = await file.get_file()
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp').name
        await tg_file.download_to_drive(temp_path)

        try:
            # Читаем файл
            if file_name.endswith('.csv'):
                df = pd.read_csv(temp_path)
            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(temp_path)
            else:
                await update.message.reply_text(
                    "❌ Поддерживаются только CSV и Excel файлы",
                    reply_markup=get_main_menu()
                )
                return

            # Сохраняем данные
            self.user_data[user_id] = {
                'df': df,
                'filename': file_name,
                'time': datetime.now()
            }

            # Отправляем ответ
            response = f"✅ *{file_name} загружен!*\n\n"
            response += f"📊 Записей: {len(df):,}\n"
            response += f"📋 Колонок: {len(df.columns)}\n\n"
            response += "🎯 *Выберите анализ:*"

            await update.message.reply_text(
                response,
                reply_markup=get_analysis_menu(),
                parse_mode='Markdown'
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)[:100]}",
                reply_markup=get_main_menu()
            )
        finally:
            # Удаляем временный файл
            try:
                os.unlink(temp_path)
            except:
                pass

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback кнопок"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        action = query.data

        if user_id not in self.user_data:
            await query.edit_message_text("❌ Нет данных для анализа")
            return

        if action == "quick":
            await self._quick_analysis(query, user_id)
        elif action == "ai":
            await self._ai_analysis(query, user_id)
        elif action == "report":
            await self._create_report(query, context, user_id)

    async def _quick_analysis(self, query, user_id):
        """Быстрый анализ"""
        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        response = f"📊 *Быстрый анализ: {filename}*\n\n"
        response += f"📈 *Основные метрики:*\n"
        response += f"• Записей: {len(df):,}\n"
        response += f"• Колонок: {len(df.columns)}\n"
        response += f"• Пропусков: {df.isnull().sum().sum()}\n\n"

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            response += f"📈 *Числовые данные:*\n"
            for col in numeric_cols[:2]:
                response += f"• {col}:\n"
                response += f"  Среднее: {df[col].mean():.2f}\n"
                response += f"  Сумма: {df[col].sum():,.2f}\n\n"

        await query.edit_message_text(
            response,
            reply_markup=get_analysis_menu(),
            parse_mode='Markdown'
        )

    async def _ai_analysis(self, query, user_id):
        """AI анализ"""
        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        await query.edit_message_text(
            "🤖 *AI анализирует данные...*",
            parse_mode='Markdown'
        )

        # Выполняем анализ
        analysis = self.analyzer.analyze(df)

        # Формируем ответ
        response = f"✨ *AI Анализ: {filename}*\n\n"

        response += "🎯 *Тренды:*\n"
        for trend in analysis['trends'][:3]:
            response += f"• {trend}\n"

        response += "\n⚠️ *Аномалии:*\n"
        for anomaly in analysis['anomalies'][:2]:
            response += f"• {anomaly}\n"

        response += "\n💡 *Рекомендации:*\n"
        for rec in analysis['recommendations'][:3]:
            response += f"• {rec}\n"

        response += "\n📈 *Следующие шаги:*\n"
        response += "1. Создайте отчет\n"
        response += "2. Используйте веб-интерфейс\n"
        response += "3. Интегрируйте с AmoCRM"

        await query.edit_message_text(
            response,
            reply_markup=get_analysis_menu(),
            parse_mode='Markdown'
        )

    async def _create_report(self, query, context, user_id):
        """Создание отчета"""
        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        await query.edit_message_text(
            "📋 *Создаю отчет...*",
            parse_mode='Markdown'
        )

        # Генерируем отчет
        report = f"# Отчет AI Business Auditor\n\n"
        report += f"Файл: {filename}\n"
        report += f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        report += "## 📊 Общая информация\n\n"
        report += f"- Записей: {len(df):,}\n"
        report += f"- Колонок: {len(df.columns)}\n\n"

        report += "## 📈 Статистика\n\n"
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:
                report += f"**{col}:**\n"
                report += f"- Среднее: {df[col].mean():.2f}\n"
                report += f"- Сумма: {df[col].sum():,.2f}\n\n"

        report += "## 💡 Рекомендации\n\n"
        report += "1. Используйте веб-интерфейс для полного анализа\n"
        report += "2. Интегрируйте данные с AmoCRM\n"
        report += "3. Настройте автоматические отчеты\n\n"

        report += "---\n*Сгенерировано AI Business Auditor*"

        # Сохраняем отчет
        temp_path = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8').name
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # Отправляем файл
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(temp_path, 'rb'),
                filename=f"report_{filename}.md",
                caption=f"📋 Отчет по анализу {filename}",
                reply_markup=get_main_menu()
            )

            await query.edit_message_text(
                "✅ *Отчет создан и отправлен!*",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)[:100]}",
                reply_markup=get_main_menu()
            )
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    async def _perform_ai_analysis(self, update, user_id):
        """AI анализ через сообщение"""
        await self._ai_analysis_message(update.message, user_id)

    async def _generate_report(self, update, context, user_id):
        """Генерация отчета через сообщение"""
        await self._create_report_message(update.message, context, user_id)

    async def _ai_analysis_message(self, message_obj, user_id):
        """AI анализ для обычного сообщения"""
        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        await message_obj.reply_text(
            "🤖 *AI анализирует данные...*",
            parse_mode='Markdown'
        )

        analysis = self.analyzer.analyze(df)

        response = f"✨ *AI Анализ: {filename}*\n\n"
        response += "🎯 *Тренды:*\n"
        for trend in analysis['trends'][:2]:
            response += f"• {trend}\n"

        response += "\n💡 *Рекомендации:*\n"
        for rec in analysis['recommendations'][:3]:
            response += f"• {rec}\n"

        await message_obj.reply_text(
            response,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def _create_report_message(self, message_obj, context, user_id):
        """Создание отчета для обычного сообщения"""
        data = self.user_data[user_id]
        df = data['df']
        filename = data['filename']

        report = f"# Отчет по {filename}\n\n"
        report += f"Дата: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        report += f"📊 Записей: {len(df):,}\n"
        report += f"📋 Колонок: {len(df.columns)}\n\n"
        report += "📈 *Для полного анализа используйте веб-интерфейс*"

        temp_path = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8').name
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(report)

        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(temp_path, 'rb'),
                filename=f"report_{filename}.md",
                caption="📋 Ваш отчет",
                reply_markup=get_main_menu()
            )
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    async def _show_amocrm(self, update):
        """Показать AmoCRM демо"""
        leads = []
        for i in range(1, 6):
            leads.append({
                'name': f'Сделка #{i}',
                'price': random.randint(10000, 300000),
                'status': random.choice(['Новая', 'В работе', 'Успешна'])
            })

        response = "🏢 *AmoCRM (демо)*\n\n"
        response += "📊 *Последние сделки:*\n\n"

        for lead in leads:
            emoji = "🟢" if lead['status'] == 'Успешна' else "🟡"
            response += f"{emoji} {lead['name']}\n"
            response += f"   💰 {lead['price']:,} руб.\n"
            response += f"   📊 {lead['status']}\n\n"

        response += "🔧 *Для реальной интеграции:*\n"
        response += "Добавьте AMOCRM_ACCESS_TOKEN в .env"

        await update.message.reply_text(
            response,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def _show_tips(self, update):
        """Показать советы"""
        tips = [
            "💰 *Увеличьте средний чек* через дополнительные услуги",
            "📈 *Анализируйте CAC и LTV* для оптимизации маркетинга",
            "🤝 *Улучшайте удержание* клиентов через сервис",
            "📊 *Автоматизируйте* рутинные отчеты"
        ]

        tip = random.choice(tips)

        await update.message.reply_text(
            f"💡 *Бизнес-совет:*\n\n{tip}",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    def run(self):
        """Запуск бота"""
        app = Application.builder().token(TOKEN).build()

        # Обработчики
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Обработка ошибок
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Ошибка: {context.error}")

        app.add_error_handler(error_handler)

        # Запуск
        print("=" * 50)
        print("🚀 Smart Business Bot запускается...")
        print(f"✅ Токен: {TOKEN[:10]}...")
        print("=" * 50)
        print("\n📱 Откройте Telegram")
        print("🔍 Найдите бота")
        print("💬 Напишите /start")
        print("👋 Ctrl+C для остановки")
        print("=" * 50)

        app.run_polling()


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Инициализация Smart Business Bot...")
    try:
        bot = SmartBusinessBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")