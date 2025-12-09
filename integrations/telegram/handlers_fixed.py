# integrations/telegram/handlers_fixed.py
"""
Исправленные обработчики для Telegram бота с правильными импортами
"""

import os
import sys
import pandas as pd
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

# ========== НАСТРОЙКА ПУТЕЙ ==========
# Добавляем корневую директорию в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"📁 Project root: {project_root}")
print(f"📁 Current dir: {current_dir}")

# ========== ДИНАМИЧЕСКИЕ ИМПОРТЫ ==========
# Импортируем DataAnalyzer
try:
    print("1. Импорт DataAnalyzer...")
    from agents.analyzer import DataAnalyzer

    analyzer = DataAnalyzer()
    print("   ✅ Успешно")
except ImportError as e:
    print(f"   ❌ Ошибка: {e}")


    # Заглушка
    class DataAnalyzer:
        def basic_analysis(self, df):
            return {'status': 'demo', 'rows': len(df)}

        def gpt_analysis(self, df):
            return "GPT анализ доступен в веб-интерфейсе"


    analyzer = DataAnalyzer()

# Импортируем ReportGenerator
try:
    print("2. Импорт ReportGenerator...")
    from agents.reporter import ReportGenerator

    reporter = ReportGenerator()
    print("   ✅ Успешно")
except ImportError as e:
    print(f"   ❌ Ошибка: {e}")


    # Заглушка
    class ReportGenerator:
        def generate_markdown_report(self, df, analysis):
            return "# Демо отчет\n\nИспользуйте веб-интерфейс"


    reporter = ReportGenerator()

# Импортируем DemoAmoCRMClient - ВАЖНЫЙ ИСПРАВЛЕНИЕ
try:
    print("3. Импорт DemoAmoCRMClient...")

    # Пробуем несколько способов импорта
    try:
        # Способ 1: Прямой импорт из demo_client.py
        from integrations.amocrm.demo_client import DemoAmoCRMClient

        print("   ✅ Способ 1: из demo_client.py")
    except ImportError as e1:
        print(f"   ❌ Способ 1 не удался: {e1}")

        try:
            # Способ 2: Из __init__.py
            from integrations.amocrm import DemoAmoCRMClient

            print("   ✅ Способ 2: из __init__.py")
        except ImportError as e2:
            print(f"   ❌ Способ 2 не удался: {e2}")

            # Способ 3: Прямой путь
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "DemoAmoCRMClient",
                    os.path.join(project_root, "integrations/amocrm/demo_client.py")
                )
                demo_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(demo_module)
                DemoAmoCRMClient = demo_module.DemoAmoCRMClient
                print("   ✅ Способ 3: прямой импорт файла")
            except Exception as e3:
                print(f"   ❌ Способ 3 не удался: {e3}")

                # Создаем простейшую заглушку
                print("   ⚠️  Создаем заглушку")


                class DemoAmoCRMClient:
                    def __init__(self, *args, **kwargs):
                        self.is_demo = True

                    def get_leads(self, limit=5):
                        return [
                            {'id': 1, 'name': 'Тест сделка 1', 'price': 10000, 'status': 'new'},
                            {'id': 2, 'name': 'Тест сделка 2', 'price': 20000, 'status': 'won'},
                        ]

                    def get_contacts(self, limit=3):
                        return [
                            {'id': 1, 'name': 'Тест контакт', 'email': 'test@test.com'},
                        ]

    amocrm = DemoAmoCRMClient()
    print("   ✅ Экземпляр создан")

except Exception as e:
    print(f"   ❌ Критическая ошибка: {e}")


    # Создаем простую заглушку
    class DemoAmoCRMClient:
        def __init__(self, *args, **kwargs):
            self.is_demo = True

        def get_leads(self, *args, **kwargs):
            return [{'id': 1, 'name': 'Ошибка импорта', 'price': 0, 'status': 'error'}]


    amocrm = DemoAmoCRMClient()

# Импортируем клавиатуры локально
try:
    print("4. Импорт клавиатур...")
    from .keyboards import (
        get_main_menu, get_file_types_keyboard, get_analysis_options_keyboard,
        get_amocrm_menu, get_reports_menu
    )

    print("   ✅ Успешно")
except ImportError as e:
    print(f"   ❌ Ошибка: {e}")
    # Простые заглушки для клавиатур
    from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


    def get_main_menu():
        keyboard = [[KeyboardButton("📊 Анализ файла")]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


    def get_file_types_keyboard():
        buttons = [[InlineKeyboardButton("CSV", callback_data="csv")]]
        return InlineKeyboardMarkup(buttons)


    def get_analysis_options_keyboard():
        buttons = [[InlineKeyboardButton("Быстрый анализ", callback_data="quick")]]
        return InlineKeyboardMarkup(buttons)


    def get_amocrm_menu():
        buttons = [[InlineKeyboardButton("Сделки", callback_data="leads")]]
        return InlineKeyboardMarkup(buttons)


    def get_reports_menu():
        buttons = [[InlineKeyboardButton("Отчет", callback_data="report")]]
        return InlineKeyboardMarkup(buttons)

print("\n" + "=" * 50)
print("✅ ВСЕ ИМПОРТЫ ЗАВЕРШЕНЫ")
print("=" * 50 + "\n")


# ========== КЛАСС ОБРАБОТЧИКОВ ==========
class MessageHandlersFixed:
    """Исправленная версия обработчиков"""

    def __init__(self):
        self.analyzer = analyzer
        self.reporter = reporter
        self.amocrm = amocrm
        self.user_sessions = {}

    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Упрощенная версия главного меню"""
        text = update.message.text

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "📤 *Загрузите файл для анализа*\n\nCSV, Excel, JSON",
                reply_markup=get_file_types_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "🤖 *AI Business Auditor Bot*\n\nИспользуйте меню:",
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка файлов"""
        user_id = update.effective_user.id

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}

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
                        "❌ Неподдерживаемый формат файла",
                        reply_markup=get_main_menu()
                    )
                    return

            # Сохраняем данные
            self.user_sessions[user_id]['dataframe'] = df
            self.user_sessions[user_id]['filename'] = file_name

            # Анализируем
            analysis = self.analyzer.basic_analysis(df)

            # Формируем ответ
            response = f"✅ *Файл загружен: {file_name}*\n\n"
            response += f"📊 Записей: {len(df)}\n"
            response += f"📋 Колонок: {len(df.columns)}\n"

            if 'summary' in analysis:
                response += f"\n📝 {analysis['summary'][:200]}"

            await update.message.reply_text(
                response,
                reply_markup=get_analysis_options_keyboard(),
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
                os.unlink(temp_file.name)
            except:
                pass

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка inline-кнопок"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "csv" or data == "quick":
            # Простой анализ
            user_id = update.effective_user.id

            if user_id in self.user_sessions and 'dataframe' in self.user_sessions[user_id]:
                df = self.user_sessions[user_id]['dataframe']
                filename = self.user_sessions[user_id]['filename']

                # Базовый анализ
                analysis = self.analyzer.basic_analysis(df)

                # GPT анализ (если доступен)
                try:
                    gpt_result = self.analyzer.gpt_analysis(df)
                    response = f"🤖 *GPT Анализ: {filename}*\n\n{gpt_result[:500]}"
                except:
                    response = f"📊 *Анализ: {filename}*\n\n"
                    if 'summary' in analysis:
                        response += analysis['summary']

                await query.edit_message_text(
                    response,
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ Нет данных для анализа",
                    reply_markup=get_main_menu()
                )

        elif data == "leads":
            # AmoCRM демо
            leads = self.amocrm.get_leads(5)

            response = "🏢 *AmoCRM (демо):*\n\n"
            for lead in leads:
                response += f"• {lead.get('name', 'Сделка')}: {lead.get('price', 0)} руб.\n"

            await query.edit_message_text(
                response,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        elif data == "report":
            # Генерация отчета
            user_id = update.effective_user.id

            if user_id in self.user_sessions and 'dataframe' in self.user_sessions[user_id]:
                df = self.user_sessions[user_id]['dataframe']
                filename = self.user_sessions[user_id]['filename']

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
                    caption=f"📄 Отчет для {filename}"
                )

                # Удаляем временный файл
                os.unlink(temp_path)

                await query.edit_message_text(
                    "✅ Отчет отправлен!",
                    reply_markup=get_main_menu()
                )
            else:
                await query.edit_message_text(
                    "❌ Нет данных для отчета",
                    reply_markup=get_main_menu()
                )