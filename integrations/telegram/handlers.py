# integrations/telegram/handlers.py
import os
import sys
import pandas as pd
import tempfile
import plotly.express as px
import plotly.io as pio
from telegram import Update
from telegram.ext import ContextTypes

# ========== НАСТРОЙКА ПУТЕЙ И ИМПОРТОВ ==========
# Добавляем корневую директорию проекта в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"📁 Project root: {project_root}")

# Импортируем клавиатуры (должны быть локальными)
try:
    from .keyboards import (
        get_main_menu, get_file_types_keyboard, get_analysis_options_keyboard,
        get_amocrm_menu, get_reports_menu, get_metrics_dashboard,
        get_tips_categories, get_settings_menu, get_confirmation_keyboard,
        get_navigation_keyboard
    )

    KEYBOARDS_IMPORTED = True
except ImportError as e:
    print(f"⚠️  Ошибка импорта клавиатур: {e}")
    KEYBOARDS_IMPORTED = False


    # Временные заглушки для клавиатур
    def get_main_menu():
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        keyboard = [[KeyboardButton("📊 Анализ файла")]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Импортируем наши агенты
ANALYZER_AVAILABLE = False
REPORTER_AVAILABLE = False
AMOCRM_AVAILABLE = False

try:
    print("🔍 Импорт DataAnalyzer...")
    from agents.analyzer import DataAnalyzer

    analyzer = DataAnalyzer()
    ANALYZER_AVAILABLE = True
    print("✅ DataAnalyzer импортирован")
except ImportError as e:
    print(f"⚠️  DataAnalyzer не найден: {e}")


    # Создаем заглушку
    class DataAnalyzer:
        def basic_analysis(self, df):
            return {
                'record_count': len(df),
                'columns': list(df.columns),
                'summary': 'Демо-анализ (полная версия в веб-интерфейсе)',
                'recommendations': ['Используйте веб-интерфейс для полного анализа']
            }

        def gpt_analysis(self, df):
            return "🤖 *GPT Анализ (демо):*\n\nДля полного GPT-анализа с AI-рекомендациями используйте веб-интерфейс Streamlit. Там доступен полный функционал с OpenAI GPT."


    analyzer = DataAnalyzer()

try:
    print("🔍 Импорт ReportGenerator...")
    from agents.reporter import ReportGenerator

    reporter = ReportGenerator()
    REPORTER_AVAILABLE = True
    print("✅ ReportGenerator импортирован")
except ImportError as e:
    print(f"⚠️  ReportGenerator не найден: {e}")


    # Создаем заглушку
    class ReportGenerator:
        def generate_markdown_report(self, df, analysis):
            report = "# 📊 Отчет AI Business Auditor (демо)\n\n"
            report += "## 📈 Краткая сводка\n\n"
            report += f"- **Записей в данных:** {len(df):,}\n"
            report += f"- **Колонок:** {len(df.columns)}\n"
            report += f"- **Типы данных:** "
            for col in df.columns:
                dtype = str(df[col].dtype)
                report += f"{col} ({dtype}), "
            report += "\n\n"
            report += "## 💡 Рекомендации\n\n"
            report += "1. Используйте веб-интерфейс для полного анализа\n"
            report += "2. Загрузите финансовые данные для детального аудита\n"
            report += "3. Включите GPT-анализ для AI-рекомендаций\n\n"
            report += "*Для полного функционала перейдите в веб-версию*"
            return report


    reporter = ReportGenerator()

# Импортируем AmoCRM клиент
try:
    print("🔍 Импорт DemoAmoCRMClient...")
    # Сначала пробуем из demo_client.py
    try:
        from integrations.amocrm.demo_client import DemoAmoCRMClient

        print("✅ DemoAmoCRMClient импортирован из demo_client.py")
    except ImportError:
        # Пробуем из __init__.py
        from integrations.amocrm import DemoAmoCRMClient

        print("✅ DemoAmoCRMClient импортирован из __init__.py")

    amocrm = DemoAmoCRMClient()
    AMOCRM_AVAILABLE = True
    print("✅ AmoCRM клиент создан")

except ImportError as e:
    print(f"⚠️  DemoAmoCRMClient не найден: {e}")
    # Создаем простую демо-версию
    from datetime import datetime, timedelta
    import random


    class DemoAmoCRMClient:
        def __init__(self):
            self.is_demo = True

        def get_leads(self, limit=10):
            leads = []
            for i in range(1, limit + 1):
                leads.append({
                    'id': i,
                    'name': f'Демо сделка #{i}',
                    'price': random.randint(10000, 500000),
                    'status': random.choice(['Новая', 'В работе', 'Успешная', 'Закрыта']),
                    'created_at': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
                })
            return leads

        def get_contacts(self, limit=5):
            contacts = []
            for i in range(1, limit + 1):
                contacts.append({
                    'id': i,
                    'name': f'Контакт #{i}',
                    'email': f'contact{i}@example.com',
                    'phone': f'+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}'
                })
            return contacts


    amocrm = DemoAmoCRMClient()
    AMOCRM_AVAILABLE = True

print("\n" + "=" * 50)
print("📊 СТАТУС ИМПОРТОВ:")
print(f"✅ DataAnalyzer: {'Доступен' if ANALYZER_AVAILABLE else 'Демо-режим'}")
print(f"✅ ReportGenerator: {'Доступен' if REPORTER_AVAILABLE else 'Демо-режим'}")
print(f"✅ AmoCRM Client: {'Доступен' if AMOCRM_AVAILABLE else 'Демо-режим'}")
print("=" * 50 + "\n")


# ========== КЛАСС ОБРАБОТЧИКОВ ==========
class MessageHandlers:
    def __init__(self):
        self.analyzer = analyzer
        self.reporter = reporter
        self.amocrm = amocrm
        self.user_sessions = {}

    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопок главного меню"""
        if not KEYBOARDS_IMPORTED:
            await update.message.reply_text(
                "❌ Ошибка загрузки меню. Пожалуйста, перезапустите бота.",
                parse_mode='Markdown'
            )
            return

        text = update.message.text

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "📤 *Загрузите файл для анализа*\n\n"
                "Поддерживаемые форматы:\n"
                "• CSV (табличные данные)\n"
                "• Excel (.xlsx, .xls)\n"
                "• JSON (структурированные данные)\n\n"
                "Просто отправьте мне файл!",
                reply_markup=get_file_types_keyboard(),
                parse_mode='Markdown'
            )

        elif text == "🤖 GPT Анализ":
            info_text = "🤖 *GPT Анализ*\n\n"
            if ANALYZER_AVAILABLE:
                info_text += "Загрузите файл и выберите 'GPT анализ' в меню.\n"
                info_text += "Для работы нужен OpenAI API ключ в .env файле."
            else:
                info_text += "⚠️ GPT анализ доступен только в веб-интерфейсе.\n"
                info_text += "Перейдите в Streamlit версию для полного функционала."

            await update.message.reply_text(
                info_text,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif text == "📋 Отчеты":
            await update.message.reply_text(
                "📄 *Генерация отчетов*\n\n"
                "Выберите формат отчета:",
                reply_markup=get_reports_menu(),
                parse_mode='Markdown'
            )

        elif text == "📈 Метрики":
            quick_metrics = self._get_quick_metrics(update.effective_user.id)
            await update.message.reply_text(
                f"📊 *Ключевые метрики*\n\n{quick_metrics}\n\n"
                "Выберите категорию для детального анализа:",
                reply_markup=get_metrics_dashboard(),
                parse_mode='Markdown'
            )

        elif text == "🏢 AmoCRM":
            status_info = "✅ Полная интеграция" if AMOCRM_AVAILABLE else "⚠️ Демо-режим"
            await update.message.reply_text(
                f"🏢 *AmoCRM интеграция*\n\n"
                f"Статус: {status_info}\n\n"
                "Выберите действие:",
                reply_markup=get_amocrm_menu(),
                parse_mode='Markdown'
            )

        elif text == "💡 Советы":
            await update.message.reply_text(
                "💡 *Бизнес-советы*\n\n"
                "Выберите категорию советов:",
                reply_markup=get_tips_categories(),
                parse_mode='Markdown'
            )

        elif text == "❓ Помощь":
            help_text = """
🤖 *AI Business Auditor Bot - Помощь*

*Основные функции:*
• 📊 **Анализ файлов** - загрузите CSV/Excel/JSON
• 🤖 **GPT Анализ** - AI рекомендации (в веб-версии)
• 📋 **Отчеты** - генерация в разных форматах
• 📈 **Метрики** - ключевые показатели бизнеса
• 🏢 **AmoCRM** - интеграция с CRM

*Как использовать:*
1. Нажмите 📊 Анализ файла
2. Отправьте файл с данными
3. Выберите тип анализа
4. Получите результат

*Поддержка:* @alex_lyubovenko

*Веб-версия:* Запустите `streamlit run ui/streamlit_app.py`
            """
            await update.message.reply_text(
                help_text,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif text == "⚙️ Настройки":
            await update.message.reply_text(
                "⚙️ *Настройки бота*\n\n"
                "Выберите параметр для настройки:",
                reply_markup=get_settings_menu(),
                parse_mode='Markdown'
            )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженных файлов"""
        user_id = update.effective_user.id

        # Создаем сессию для пользователя
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}

        # Скачиваем файл
        document = update.message.document
        file = await document.get_file()
        file_name = document.file_name
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

        # Показываем статус загрузки
        await update.message.reply_text(
            f"📥 *Загружаю файл...*\n\n{file_name}",
            parse_mode='Markdown'
        )

        # Сохраняем временный файл
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}')
        await file.download_to_drive(temp_file.name)

        try:
            # Загружаем данные
            df = self._load_dataframe(temp_file.name, file_ext)

            # Сохраняем данные в сессию
            self.user_sessions[user_id]['dataframe'] = df
            self.user_sessions[user_id]['filename'] = file_name
            self.user_sessions[user_id]['filepath'] = temp_file.name

            # Показываем успешную загрузку
            stats = self._get_file_stats(df)

            await update.message.reply_text(
                f"✅ *Файл загружен успешно!*\n\n"
                f"📁 Имя файла: {file_name}\n"
                f"📊 Записей: {stats['rows']:,}\n"
                f"📋 Колонок: {stats['columns']}\n"
                f"📝 Типы данных: {stats['dtypes']}\n"
                f"⚠️  Пропуски: {stats['missing']}\n\n"
                f"Выберите тип анализа:",
                reply_markup=get_analysis_options_keyboard(),
                parse_mode='Markdown'
            )

            # Удаляем временный файл
            os.unlink(temp_file.name)

        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."

            await update.message.reply_text(
                f"❌ *Ошибка загрузки файла:*\n\n{error_msg}\n\n"
                f"Проверьте формат файла и попробуйте снова.",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    def _load_dataframe(self, file_path, file_ext):
        """Загрузка DataFrame из файла"""
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
                    raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")

    def _get_file_stats(self, df):
        """Получение статистики по файлу"""
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'dtypes': ', '.join([f"{col}: {str(dtype)[:10]}"
                                 for col, dtype in df.dtypes.items()][:3]),
            'missing': df.isnull().sum().sum()
        }

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка inline-кнопок"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        data = query.data

        print(f"📨 Callback query: {data} from user {user_id}")

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
                "📤 *Загрузите файл для анализа*\n\nПоддерживаемые форматы: CSV, Excel, JSON",
                reply_markup=get_file_types_keyboard(),
                parse_mode='Markdown'
            )
            return

        # Обработка анализа
        if data.startswith("analysis_"):
            await self._handle_analysis(query, user_id, data, context)

        # Обработка AmoCRM
        elif data.startswith("amo_"):
            await self._handle_amocrm(query, user_id, data, context)

        # Обработка отчетов
        elif data.startswith("report_"):
            await self._handle_reports(query, user_id, data, context)

        # Обработка метрик
        elif data.startswith("metrics_"):
            await self._handle_metrics(query, user_id, data, context)

        # Обработка советов
        elif data.startswith("tips_"):
            await self._handle_tips(query, user_id, data, context)

        # Обработка настроек
        elif data.startswith("settings_"):
            await self._handle_settings(query, user_id, data, context)

        # Навигация
        elif data.startswith("nav_"):
            await self._handle_navigation(query, user_id, data, context)

        # Подтверждение
        elif data.startswith("confirm_"):
            await self._handle_confirmation(query, user_id, data, context)

    async def _handle_analysis(self, query, user_id, action, context):
        """Обработка выбора анализа"""
        # Проверяем наличие данных
        if user_id not in self.user_sessions or 'dataframe' not in self.user_sessions[user_id]:
            await query.edit_message_text(
                "❌ *Нет данных для анализа*\n\n"
                "Сначала загрузите файл через меню 📊 Анализ файла",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )
            return

        df = self.user_sessions[user_id]['dataframe']
        filename = self.user_sessions[user_id].get('filename', 'файл')

        if action == "analysis_quick":
            # Быстрый анализ
            await query.edit_message_text(
                "🔍 *Выполняю быстрый анализ...*",
                parse_mode='Markdown'
            )

            try:
                analysis = self.analyzer.basic_analysis(df)
                response = self._format_quick_analysis(df, analysis, filename)

                await query.edit_message_text(
                    response,
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

            except Exception as e:
                await query.edit_message_text(
                    f"❌ *Ошибка анализа:*\n{str(e)[:200]}",
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

        elif action == "analysis_gpt":
            # GPT анализ
            await query.edit_message_text(
                "🤖 *Запускаю GPT-анализ...*\n\n"
                "AI анализирует данные... Это займет 10-30 секунд.",
                parse_mode='Markdown'
            )

            try:
                gpt_result = self.analyzer.gpt_analysis(df)

                response = f"🤖 *GPT Анализ: {filename}*\n\n"
                response += gpt_result
                response += "\n\n📊 *Что можно сделать дальше:*\n"
                response += "• Сгенерировать полный отчет\n"
                response += "• Проанализировать в веб-интерфейсе\n"
                response += "• Интегрировать с AmoCRM\n"

                await query.edit_message_text(
                    response,
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

            except Exception as e:
                error_msg = str(e)
                if "API" in error_msg or "key" in error_msg.lower():
                    error_msg = "Не настроен OpenAI API ключ. Добавьте OPENAI_API_KEY в .env файл"

                await query.edit_message_text(
                    f"❌ *Ошибка GPT-анализа:*\n\n{error_msg[:300]}\n\n"
                    f"Проверьте настройки OpenAI API.",
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

        elif action == "analysis_charts":
            # Создание графиков
            await query.edit_message_text(
                "📈 *Создаю визуализации...*",
                parse_mode='Markdown'
            )

            try:
                await self._send_charts(query, user_id, df, context)
            except Exception as e:
                await query.edit_message_text(
                    f"❌ *Ошибка создания графиков:*\n{str(e)[:200]}",
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

        elif action == "analysis_full":
            # Полный анализ
            await query.edit_message_text(
                "📋 *Генерация полного отчета...*",
                parse_mode='Markdown'
            )

            try:
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
                    caption=f"📋 *Полный отчет: {filename}*\n\nСгенерировано AI Business Auditor",
                    reply_markup=get_main_menu()
                )

                # Удаляем временный файл
                os.unlink(temp_path)

                await query.edit_message_text(
                    "✅ *Отчет сгенерирован и отправлен!*\n\n"
                    "Проверьте файл в чате.",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

            except Exception as e:
                await query.edit_message_text(
                    f"❌ *Ошибка генерации отчета:*\n{str(e)[:200]}",
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

    def _format_quick_analysis(self, df, analysis, filename):
        """Форматирование быстрого анализа"""
        response = f"📊 *Быстрый анализ: {filename}*\n\n"
        response += f"📈 *Общие метрики:*\n"
        response += f"• Записей: {len(df):,}\n"
        response += f"• Колонок: {len(df.columns)}\n"

        if 'record_count' in analysis:
            response += f"• Анализировано: {analysis['record_count']}\n"

        if 'summary' in analysis and analysis['summary']:
            response += f"\n📝 *Сводка:*\n{analysis['summary'][:300]}...\n"

        if 'recommendations' in analysis and analysis['recommendations']:
            response += f"\n🎯 *Рекомендации:*\n"
            for i, rec in enumerate(analysis['recommendations'][:3], 1):
                response += f"{i}. {rec}\n"

        response += f"\n🔍 *Следующие шаги:*\n"
        response += f"1. Выберите 🤖 GPT анализ для AI-рекомендаций\n"
        response += f"2. Сгенерируйте 📋 полный отчет\n"
        response += f"3. Загрузите в веб-интерфейс для продвинутого анализа"

        return response

    async def _send_charts(self, query, user_id, df, context):
        """Отправка графиков"""
        try:
            # Пробуем создать разные типы графиков
            numeric_cols = df.select_dtypes(include='number').columns

            if len(numeric_cols) > 0:
                # Если есть дата, строим временной ряд
                date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]

                if date_cols and len(numeric_cols) > 0:
                    date_col = date_cols[0]
                    try:
                        df[date_col] = pd.to_datetime(df[date_col])
                        fig = px.line(df, x=date_col, y=numeric_cols[0],
                                      title=f'Тренд: {numeric_cols[0]}')
                    except:
                        fig = px.histogram(df, x=numeric_cols[0],
                                           title=f'Распределение: {numeric_cols[0]}')
                else:
                    # Гистограмма для первого числового столбца
                    fig = px.histogram(df, x=numeric_cols[0],
                                       title=f'Распределение: {numeric_cols[0]}')

                # Сохраняем график
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    pio.write_image(fig, f.name, format='png', width=800, height=600)
                    temp_path = f.name

                # Отправляем фото
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=open(temp_path, 'rb'),
                    caption="📈 *Визуализация данных*\n\nГрафик создан автоматически",
                    reply_markup=get_analysis_options_keyboard()
                )

                # Удаляем временный файл
                os.unlink(temp_path)

                await query.edit_message_text(
                    "✅ *График создан и отправлен!*\n\n"
                    "Проверьте изображение в чате.",
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ *Нет числовых данных для визуализации*\n\n"
                    "В ваших данных нет числовых колонок для построения графиков.",
                    reply_markup=get_analysis_options_keyboard(),
                    parse_mode='Markdown'
                )

        except Exception as e:
            raise Exception(f"Ошибка создания графика: {str(e)}")

    async def _handle_amocrm(self, query, user_id, action, context):
        """Обработка AmoCRM меню"""
        try:
            if action == "amo_leads":
                # Список сделок
                leads = self.amocrm.get_leads(10)

                response = "🏢 *AmoCRM - Последние сделки:*\n\n"
                for i, lead in enumerate(leads[:5], 1):
                    response += f"{i}. #{lead['id']}: {lead['name']}\n"
                    response += f"   💰 {lead.get('price', 0):,} руб. | 📊 {lead.get('status', 'Н/Д')}\n\n"

                if len(leads) > 5:
                    response += f"... и еще {len(leads) - 5} сделок\n\n"

                response += "Выберите действие:"

                await query.edit_message_text(
                    response,
                    reply_markup=get_amocrm_menu(),
                    parse_mode='Markdown'
                )

            elif action == "amo_stats":
                # Статистика
                try:
                    if hasattr(self.amocrm, 'get_lead_stats'):
                        stats = self.amocrm.get_lead_stats()
                        response = "📊 *AmoCRM Статистика:*\n\n"
                        response += f"📈 Всего сделок: {stats.get('total_leads', 'Н/Д')}\n"
                        response += f"✅ Выиграно: {stats.get('won_leads', 'Н/Д')}\n"
                        response += f"❌ Проиграно: {stats.get('lost_leads', 'Н/Д')}\n"
                        response += f"🔄 В работе: {stats.get('in_progress', 'Н/Д')}\n"
                        response += f"🎯 Конверсия: {stats.get('conversion_rate', 0):.1f}%\n"
                        response += f"💰 Общая сумма: {stats.get('total_value', 0):,} руб.\n"
                        response += f"📊 Средний чек: {stats.get('avg_deal_size', 0):,.0f} руб.\n"
                    else:
                        leads = self.amocrm.get_leads(50)
                        total = len(leads)
                        won = len([l for l in leads if l.get('status') in ['Успешная', 'Закрыта']])
                        total_value = sum(l.get('price', 0) for l in leads)

                        response = "📊 *AmoCRM Статистика (базовая):*\n\n"
                        response += f"📈 Всего сделок: {total}\n"
                        response += f"✅ Выиграно: {won}\n"
                        response += f"🎯 Конверсия: {(won / total * 100 if total > 0 else 0):.1f}%\n"
                        response += f"💰 Общая сумма: {total_value:,} руб.\n"
                        response += f"📊 Средний чек: {(total_value / total if total > 0 else 0):,.0f} руб.\n"

                    response += "\nВыберите действие:"

                    await query.edit_message_text(
                        response,
                        reply_markup=get_amocrm_menu(),
                        parse_mode='Markdown'
                    )

                except Exception as e:
                    await query.edit_message_text(
                        f"❌ *Ошибка получения статистики:*\n{str(e)[:200]}",
                        reply_markup=get_amocrm_menu(),
                        parse_mode='Markdown'
                    )

        except Exception as e:
            await query.edit_message_text(
                f"❌ *Ошибка работы с AmoCRM:*\n{str(e)[:200]}",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    def _get_quick_metrics(self, user_id):
        """Получение быстрых метрик"""
        if user_id in self.user_sessions and 'dataframe' in self.user_sessions[user_id]:
            df = self.user_sessions[user_id]['dataframe']
            filename = self.user_sessions[user_id].get('filename', 'текущий файл')

            return (
                f"📊 *Текущие данные:*\n"
                f"• Файл: {filename}\n"
                f"• Записей: {len(df):,}\n"
                f"• Колонок: {len(df.columns)}\n"
                f"• Память: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB\n\n"
                f"Для анализа выберите '📊 Анализ файла'"
            )
        else:
            return "📊 *Нет загруженных данных*\n\nЗагрузите файл через меню 📊 Анализ файла"

    async def _handle_reports(self, query, user_id, action, context):
        """Обработка генерации отчетов"""
        if user_id not in self.user_sessions or 'dataframe' not in self.user_sessions[user_id]:
            await query.edit_message_text(
                "❌ *Нет данных для отчета*\n\n"
                "Сначала загрузите файл через меню 📊 Анализ файла",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )
            return

        await query.edit_message_text(
            f"📄 *Генерация отчета...*\n\nФормат: {action.replace('report_', '').upper()}",
            parse_mode='Markdown'
        )

        df = self.user_sessions[user_id]['dataframe']
        filename = self.user_sessions[user_id].get('filename', 'report')

        try:
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
                filename=f"{filename}_report.md",
                caption=f"📄 *Ваш бизнес-отчет*\n\nСгенерировано AI Business Auditor",
                reply_markup=get_main_menu()
            )

            # Удаляем временный файл
            os.unlink(temp_path)

            await query.edit_message_text(
                "✅ *Отчет сгенерирован и отправлен!*",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        except Exception as e:
            await query.edit_message_text(
                f"❌ *Ошибка генерации отчета:*\n{str(e)[:200]}",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    async def _handle_metrics(self, query, user_id, action, context):
        """Обработка метрик"""
        metrics_data = {
            "metrics_finance": {
                "title": "💰 *Финансовые метрики*",
                "data": [
                    "ROI: 18.5%",
                    "Рентабельность: 22.3%",
                    "Ликвидность: 1.7",
                    "Оборачиваемость: 3.2",
                    "Маржа: 28.7%"
                ]
            },
            "metrics_clients": {
                "title": "👥 *Клиентские метрики*",
                "data": [
                    "LTV: 45,200 руб.",
                    "CAC: 8,500 руб.",
                    "Удержание: 78.3%",
                    "NPS: +42",
                    "CSI: 4.2/5.0"
                ]
            },
            "metrics_sales": {
                "title": "📊 *Метрики продаж*",
                "data": [
                    "Конверсия: 3.2%",
                    "Средний чек: 12,500 руб.",
                    "Цикл продаж: 14 дней",
                    "Коэф. воронки: 0.32",
                    "Время отклика: 2.1 ч"
                ]
            },
            "metrics_efficiency": {
                "title": "⏱️ *Метрики эффективности*",
                "data": [
                    "Продуктивность: 85%",
                    "Время обработки: 2.4 ч",
                    "SLA: 98.7%",
                    "Автоматизация: 67%",
                    "Ошибки: 0.8%"
                ]
            }
        }

        if action == "metrics_refresh":
            await query.edit_message_text(
                "🔄 *Обновление метрик...*",
                parse_mode='Markdown'
            )
            # Здесь можно добавить реальное обновление данных

        metric_info = metrics_data.get(action)
        if metric_info:
            response = f"{metric_info['title']}\n\n"
            for item in metric_info['data']:
                response += f"• {item}\n"
        else:
            response = "📊 *Общие метрики*\n\nВыберите категорию для деталей"

        response += "\n\nВыберите другую категорию или обновите данные:"

        await query.edit_message_text(
            response,
            reply_markup=get_metrics_dashboard(),
            parse_mode='Markdown'
        )

    async def _handle_tips(self, query, user_id, action, context):
        """Обработка советов"""
        tips_categories = {
            "finance": [
                "💰 *Оптимизируйте налоги*: Используйте все доступные вычеты и льготы по НДС, налогу на прибыль и УСН",
                "📈 *Диверсифицируйте доходы*: Стремитесь к соотношению 30/30/40 между основными продуктами",
                "💳 *Создайте финансовую подушку*: 6 месяцев операционных расходов на отдельном счете",
                "📊 *Внедрите управленческий учет*: Отслеживайте EBIT, EBITDA и операционную маржу"
            ],
            "sales": [
                "🎯 *Увеличьте средний чек*: Добавьте up-sell (допродажи) и cross-sell (сопутствующие товары)",
                "🤝 *Улучшите воронку продаж*: Автоматизируйте follow-up (напоминания) через 1, 3, 7 дней",
                "📞 *Обучите менеджеров*: Внедрите скрипты продаж для разных возражений клиентов",
                "📊 *Анализируйте причины отказов*: Каждая 5-я потерянная сделка может быть возвращена"
            ],
            "marketing": [
                "📱 *Используйте социальные сети*: Контент-маркетинг дает ROI 380% при правильной стратегии",
                "🎯 *Сегментируйте аудиторию*: Персонализируйте предложения по RFM-анализу (Recency, Frequency, Monetary)",
                "📊 *Измеряйте CAC*: Знайте точную стоимость привлечения клиента по каждому каналу",
                "🔍 *Оптимизируйте сайт*: Увеличьте скорость загрузки на 1 секунду → +7% конверсии"
            ],
            "operations": [
                "⚡ *Автоматизируйте рутину*: Высвободите 20% времени сотрудников на стратегические задачи",
                "📋 *Стандартизируйте процессы*: Создайте базу знаний с чек-листами и шаблонами",
                "🔄 *Внедрите обратную связь*: Собирайте отзывы после каждой завершенной сделки",
                "📈 *Измеряйте эффективность*: Внедрите KPI для каждого отдела и сотрудника"
            ]
        }

        import random

        if action == "tips_random":
            all_tips = [tip for category in tips_categories.values() for tip in category]
            selected_tip = random.choice(all_tips)
            category = "разные категории"
        else:
            category = action.replace("tips_", "")
            category_tips = tips_categories.get(category, ["💡 Совет обновляется..."])
            selected_tip = random.choice(category_tips)

        await query.edit_message_text(
            f"💡 *Бизнес-совет ({category}):*\n\n{selected_tip}\n\n"
            f"Хотите еще совет? Выберите категорию:",
            reply_markup=get_tips_categories(),
            parse_mode='Markdown'
        )

    async def _handle_settings(self, query, user_id, action, context):
        """Обработка настроек"""
        settings_info = {
            "settings_notify": {
                "title": "🔔 *Настройки уведомлений*",
                "desc": "Выберите частоту уведомлений:"
            },
            "settings_theme": {
                "title": "🌙 *Тема интерфейса*",
                "desc": "Выберите тему интерфейса:"
            },
            "settings_auto": {
                "title": "🔄 *Автообновление*",
                "desc": "Настройте автоматическое обновление данных:"
            },
            "settings_email": {
                "title": "📧 *Email отчеты*",
                "desc": "Настройте отправку отчетов на email:"
            },
            "settings_clear": {
                "title": "🧹 *Очистка данных*",
                "desc": "⚠️ Вы уверены, что хотите удалить все данные? Это действие нельзя отменить."
            }
        }

        setting = settings_info.get(action)
        if setting:
            response = f"{setting['title']}\n\n{setting['desc']}"
        else:
            response = "⚙️ *Настройки*\n\nВыберите параметр для настройки:"

        if action == "settings_clear":
            markup = get_confirmation_keyboard()
        else:
            markup = get_settings_menu()

        await query.edit_message_text(
            response,
            reply_markup=markup,
            parse_mode='Markdown'
        )

    async def _handle_navigation(self, query, user_id, action, context):
        """Обработка навигации"""
        if action == "nav_home":
            await query.edit_message_text(
                "🏠 *Главное меню*",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    async def _handle_confirmation(self, query, user_id, action, context):
        """Обработка подтверждения"""
        if action == "confirm_yes":
            if user_id in self.user_sessions:
                self.user_sessions[user_id] = {}

            await query.edit_message_text(
                "✅ *Данные очищены!*\n\nВсе загруженные файлы удалены.",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )
        elif action == "confirm_no":
            await query.edit_message_text(
                "❌ *Действие отменено*\n\nДанные сохранены.",
                reply_markup=get_settings_menu(),
                parse_mode='Markdown'
            )