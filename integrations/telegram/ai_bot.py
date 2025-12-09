# integrations/telegram/ai_bot.py
"""
Telegram бот AI Business Auditor с AI анализом и красивым оформлением
"""

print("=" * 60)
print("🚀 ЗАПУСК AI BUSINESS AUDITOR BOT")
print("🤖 Версия с AI анализом и красивым оформлением")
print("=" * 60)

try:
    import os
    import logging
    import pandas as pd
    import tempfile
    import random
    import json
    from datetime import datetime, timedelta
    from textwrap import dedent

    print("✅ Базовые библиотеки загружены")
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    exit(1)

try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

    print("✅ Telegram библиотеки загружены")
except Exception as e:
    print(f"❌ Ошибка Telegram: {e}")
    exit(1)

# ========== КОНСТАНТЫ ==========
TOKEN = "8457812721:AAEO-db6iR0oimab8VNuMwiwG5XPMLKdQqQ"
ADMIN_ID = "427861947"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== КРАСИВЫЕ КЛАВИАТУРЫ ==========
def get_main_menu():
    """Главное меню с эмодзи"""
    keyboard = [
        [KeyboardButton("📊 Анализ файла"), KeyboardButton("🤖 AI Анализ")],
        [KeyboardButton("📈 Графики"), KeyboardButton("📋 Отчет")],
        [KeyboardButton("🏢 AmoCRM"), KeyboardButton("💡 Советы")],
        [KeyboardButton("⚙️ Настройки"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)


def get_analysis_menu():
    """Меню после загрузки файла"""
    buttons = [
        [
            InlineKeyboardButton("📊 Быстрый анализ", callback_data="quick"),
            InlineKeyboardButton("🤖 AI Анализ", callback_data="ai")
        ],
        [
            InlineKeyboardButton("📈 Графики", callback_data="charts"),
            InlineKeyboardButton("📋 Полный отчет", callback_data="report")
        ],
        [
            InlineKeyboardButton("💡 Рекомендации", callback_data="tips"),
            InlineKeyboardButton("📤 Экспорт", callback_data="export")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


# ========== AI АНАЛИЗАТОР ==========
class AIAnalyzer:
    """Класс для AI анализа данных"""

    def analyze_data(self, df):
        """Основной AI анализ данных"""

        # Получаем базовую статистику
        numeric_cols = df.select_dtypes(include='number').columns

        if len(numeric_cols) == 0:
            return self._analyze_text_data(df)

        # Анализируем числовые данные
        analysis = {
            'overview': self._get_overview(df),
            'trends': self._detect_trends(df, numeric_cols),
            'anomalies': self._find_anomalies(df, numeric_cols),
            'recommendations': self._generate_recommendations(df, numeric_cols),
            'metrics': self._calculate_metrics(df, numeric_cols),
            'forecast': self._make_forecast(df, numeric_cols)
        }

        return analysis

    def _get_overview(self, df):
        """Обзор данных"""
        overview = f"""
📊 *ОБЗОР ДАННЫХ*

• 📁 Записей: {len(df):,}
• 📋 Колонок: {len(df.columns)}
• 📅 Период: {self._get_date_range(df)}
• 💾 Размер: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB

📈 *Структура данных:*
{self._get_structure_summary(df)}
        """
        return dedent(overview).strip()

    def _get_date_range(self, df):
        """Определение временного диапазона"""
        date_cols = [col for col in df.columns if any(
            word in col.lower() for word in ['date', 'year', 'month', 'day', 'время', 'дата', 'год', 'месяц'])]

        if date_cols:
            date_col = date_cols[0]
            try:
                if pd.api.types.is_numeric_dtype(df[date_col]):
                    min_val = df[date_col].min()
                    max_val = df[date_col].max()
                    return f"{min_val:.0f} - {max_val:.0f}"
                else:
                    return "разные даты"
            except:
                pass

        return "не определен"

    def _get_structure_summary(self, df):
        """Сводка по структуре данных"""
        summary = ""
        numeric_count = len(df.select_dtypes(include='number').columns)
        text_count = len(df.select_dtypes(include='object').columns)

        summary += f"• 🔢 Числовых: {numeric_count}\n"
        summary += f"• 📝 Текстовых: {text_count}\n"

        # Показываем примеры колонок
        if len(df.columns) <= 5:
            for col in df.columns[:3]:
                dtype = str(df[col].dtype)
                summary += f"• `{col}` ({dtype[:10]})\n"
        else:
            summary += f"• Примеры: `{df.columns[0]}`, `{df.columns[1]}`, `{df.columns[2]}`...\n"

        return summary

    def _detect_trends(self, df, numeric_cols):
        """Обнаружение трендов"""
        trends = []

        if len(df) >= 3:
            for col in numeric_cols[:3]:  # Анализируем первые 3 числовые колонки
                try:
                    # Простой анализ тренда
                    values = df[col].dropna()
                    if len(values) >= 3:
                        first_third = values.iloc[:len(values) // 3].mean()
                        last_third = values.iloc[-len(values) // 3:].mean()

                        change = ((last_third - first_third) / abs(first_third)) * 100 if first_third != 0 else 0

                        if abs(change) > 10:
                            direction = "📈 рост" if change > 0 else "📉 снижение"
                            trends.append(f"• `{col}`: {direction} на {abs(change):.1f}%")
                except:
                    pass

        if trends:
            return "🎯 *ОБНАРУЖЕННЫЕ ТРЕНДЫ:*\n" + "\n".join(trends[:5])
        else:
            return "📊 *ТРЕНДЫ:* Не обнаружено значительных изменений"

    def _find_anomalies(self, df, numeric_cols):
        """Поиск аномалий"""
        anomalies = []

        for col in numeric_cols[:3]:
            try:
                # Простой поиск выбросов через IQR
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]

                if len(outliers) > 0:
                    anomalies.append(f"• `{col}`: {len(outliers)} выбросов ({len(outliers) / len(df) * 100:.1f}%)")
            except:
                pass

        if anomalies:
            return "⚠️ *АНОМАЛИИ:*\n" + "\n".join(anomalies[:3])
        else:
            return "✅ *АНОМАЛИИ:* Значительных отклонений не обнаружено"

    def _calculate_metrics(self, df, numeric_cols):
        """Расчет ключевых метрик"""
        metrics = []

        for col in numeric_cols[:3]:
            try:
                mean = df[col].mean()
                median = df[col].median()
                std = df[col].std()

                metrics.append(f"""
📊 *{col}:*
   Среднее: {mean:,.2f}
   Медиана: {median:,.2f}
   Станд. отклонение: {std:,.2f}
   Диапазон: {df[col].min():,.2f} - {df[col].max():,.2f}
                """.strip())
            except:
                pass

        return "\n\n".join(metrics[:2])

    def _generate_recommendations(self, df, numeric_cols):
        """Генерация рекомендаций на основе данных"""
        recommendations = []

        # Анализ распределения
        for col in numeric_cols[:2]:
            try:
                skewness = df[col].skew()

                if abs(skewness) > 1:
                    rec = f"• Данные в `{col}` сильно смещены (skew={skewness:.2f}). Рассмотрите трансформацию."
                    recommendations.append(rec)
            except:
                pass

        # Анализ пропусков
        missing_total = df.isnull().sum().sum()
        if missing_total > 0:
            missing_pct = missing_total / (len(df) * len(df.columns)) * 100
            recommendations.append(
                f"• Обнаружено {missing_total} пропусков ({missing_pct:.1f}%). Рекомендуется обработка.")

        # Общие рекомендации
        if len(df) < 100:
            recommendations.append("• 📈 Для более точного анализа соберите больше данных (рекомендуется >100 записей)")

        if len(numeric_cols) >= 3:
            recommendations.append("• 🤖 Используйте веб-интерфейс для многомерного анализа и визуализации")

        recommendations.append("• 🏢 Интегрируйте данные с AmoCRM для CRM-аналитики")
        recommendations.append("• 📊 Настройте автоматические отчеты для регулярного мониторинга")

        return "💡 *РЕКОМЕНДАЦИИ:*\n" + "\n".join(recommendations[:6])

    def _make_forecast(self, df, numeric_cols):
        """Простой прогноз"""
        if len(df) >= 6 and len(numeric_cols) > 0:
            col = numeric_cols[0]
            try:
                # Простая линейная экстраполяция
                x = list(range(len(df)))
                y = df[col].values

                # Коэффициент линейного тренда
                if len(y) >= 2:
                    trend = (y[-1] - y[0]) / len(y) if len(y) > 0 else 0

                    if abs(trend) > 0:
                        direction = "роста" if trend > 0 else "снижения"
                        return f"📈 *ПРОГНОЗ:* Тенденция {direction} `{col}` на {abs(trend):.2f} за период"
            except:
                pass

        return "🔮 *ПРОГНОЗ:* Для точного прогноза требуется больше данных"

    def _analyze_text_data(self, df):
        """Анализ текстовых данных"""
        return {
            'overview': f"📝 *ТЕКСТОВЫЕ ДАННЫЕ*\n\nЗаписей: {len(df)}\nКолонок: {len(df.columns)}",
            'trends': "📊 Анализ текста требует NLP обработки",
            'anomalies': "✅ Аномалий не обнаружено",
            'recommendations': "💡 Загрузите числовые данные для детального анализа",
            'metrics': "📈 Метрики недоступны для текстовых данных",
            'forecast': "🔮 Прогноз требует числовых показателей"
        }


# ========== ОСНОВНОЙ КЛАСС БОТА ==========
class AITelegramBot:
    def __init__(self):
        self.analyzer = AIAnalyzer()
        self.user_data = {}
        print("✅ AI анализатор инициализирован")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start с красивым оформлением"""
        welcome = """
✨ *ДОБРО ПОЖАЛОВАТЬ В AI BUSINESS AUDITOR!* ✨

🤖 *Умный помощник для анализа бизнеса*

🎯 *ЧТО Я УМЕЮ:*
• 📊 *Анализировать* CSV/Excel файлы
• 🤖 *Давать AI-рекомендации* на основе данных  
• 📈 *Строить графики* и визуализации
• 📋 *Генерировать* профессиональные отчеты
• 🏢 *Интегрировать* с AmoCRM
• 💡 *Предлагать* бизнес-советы

📁 *ПРОСТО ОТПРАВЬТЕ МНЕ ФАЙЛ И ПОЛУЧИТЕ:*
1. 📊 Детальный анализ данных
2. 🤖 AI рекомендации
3. 📈 Визуализации трендов
4. 📋 Готовый отчет

👇 *Используйте меню для навигации:*
        """

        await update.message.reply_text(
            dedent(welcome),
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        text = update.message.text
        user_id = update.effective_user.id

        print(f"📨 [{user_id}] Нажата кнопка: {text}")

        if text == "📊 Анализ файла":
            await update.message.reply_text(
                "📤 *ЗАГРУЗКА ФАЙЛА*\n\n"
                "Отправьте мне файл в формате:\n"
                "• 📁 CSV (разделитель запятая)\n"
                "• 📊 Excel (.xlsx, .xls)\n"
                "• 📄 JSON (структурированные данные)\n\n"
                "💡 *Пример структуры:*\n"
                "```\n"
                "Дата,Выручка,Расходы,Прибыль\n"
                "2024-01,100000,70000,30000\n"
                "2024-02,120000,80000,40000\n"
                "```",
                parse_mode='Markdown'
            )

        elif text == "🤖 AI Анализ":
            if user_id in self.user_data and 'df' in self.user_data[user_id]:
                await self.perform_ai_analysis(update, user_id)
            else:
                await update.message.reply_text(
                    "🤖 *AI АНАЛИЗ*\n\n"
                    "Сначала загрузите файл через 📊 Анализ файла\n\n"
                    "После загрузки я проведу:\n"
                    "• 📊 Анализ структуры данных\n"
                    "• 📈 Обнаружение трендов\n"
                    "• ⚠️ Выявление аномалий\n"
                    "• 💡 Генерация рекомендаций\n"
                    "• 🔮 Прогноз на основе данных",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )

        elif text == "📈 Графики":
            await update.message.reply_text(
                "📈 *ВИЗУАЛИЗАЦИЯ ДАННЫХ*\n\n"
                "Функция графиков доступна в веб-интерфейсе:\n\n"
                "```bash\n"
                "streamlit run ui/streamlit_app.py\n"
                "```\n\n"
                "Там вы найдете:\n"
                "• 📊 Интерактивные графики Plotly\n"
                "• 📈 Трендовые анализы\n"
                "• 🎯 Дашборды метрик",
                parse_mode='Markdown'
            )

        elif text == "📋 Отчет":
            if user_id in self.user_data and 'df' in self.user_data[user_id]:
                await self.generate_report(update, context, user_id)
            else:
                await update.message.reply_text(
                    "📋 *ГЕНЕРАЦИЯ ОТЧЕТА*\n\n"
                    "Сначала загрузите файл для анализа",
                    reply_markup=get_main_menu()
                )

        elif text == "🏢 AmoCRM":
            await self.show_amocrm_demo(update)

        elif text == "💡 Советы":
            await self.show_business_tips(update)

        elif text == "⚙️ Настройки":
            await update.message.reply_text(
                "⚙️ *НАСТРОЙКИ*\n\n"
                "*Текущий режим:* Демо-версия\n\n"
                "*Доступные настройки:*\n"
                "• 🔑 OpenAI API ключ (для GPT анализа)\n"
                "• 🏢 AmoCRM интеграция\n"
                "• 📧 Email уведомления\n"
                "• 🌐 Язык интерфейса\n\n"
                "*Для настройки:* Отредактируйте `.env` файл",
                parse_mode='Markdown'
            )

        elif text == "❓ Помощь":
            await self.show_help(update)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженных файлов"""
        user_id = update.effective_user.id
        document = update.message.document
        file_name = document.file_name

        print(f"📁 [{user_id}] Загрузка файла: {file_name}")

        # Показываем статус загрузки
        status_msg = await update.message.reply_text(
            f"🔄 *Загружаю файл...*\n\n"
            f"📁 `{file_name}`\n"
            f"⏳ Обработка...",
            parse_mode='Markdown'
        )

        # Скачиваем файл
        file = await document.get_file()
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}')
        await file.download_to_drive(temp_file.name)

        try:
            # Загружаем данные
            df = self.load_dataframe(temp_file.name, file_ext)

            # Сохраняем данные пользователя
            self.user_data[user_id] = {
                'df': df,
                'filename': file_name,
                'uploaded_at': datetime.now()
            }

            # Удаляем временный файл
            os.unlink(temp_file.name)

            # Обновляем статус
            await status_msg.edit_text(
                f"✅ *ФАЙЛ УСПЕШНО ЗАГРУЖЕН!*\n\n"
                f"📁 `{file_name}`\n"
                f"📊 *{len(df):,}* записей\n"
                f"📋 *{len(df.columns)}* колонок\n\n"
                f"🎯 *ДОСТУПНЫЕ ДЕЙСТВИЯ:*",
                reply_markup=get_analysis_menu(),
                parse_mode='Markdown'
            )

            print(f"✅ [{user_id}] Файл обработан: {len(df)} строк")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ [{user_id}] Ошибка: {error_msg}")

            await status_msg.edit_text(
                f"❌ *ОШИБКА ЗАГРУЗКИ*\n\n"
                f"Файл: `{file_name}`\n\n"
                f"*Причина:* {error_msg[:150]}\n\n"
                f"💡 *Проверьте:*\n"
                f"• Формат файла (CSV/Excel)\n"
                f"• Кодировку (UTF-8)\n"
                f"• Структуру данных",
                parse_mode='Markdown'
            )

    def load_dataframe(self, file_path, file_ext):
        """Загрузка DataFrame с обработкой ошибок"""
        if file_ext == 'csv':
            return pd.read_csv(file_path)
        elif file_ext in ['xlsx', 'xls']:
            return pd.read_excel(file_path)
        elif file_ext == 'json':
            return pd.read_json(file_path)
        else:
            # Пробуем автоматически определить
            try:
                return pd.read_csv(file_path)
            except:
                try:
                    return pd.read_excel(file_path)
                except:
                    raise ValueError(f"Неподдерживаемый формат: .{file_ext}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback кнопок"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        action = query.data

        print(f"🔘 [{user_id}] Callback: {action}")

        if action == "quick":
            await self.perform_quick_analysis(query, user_id)
        elif action == "ai":
            await self.perform_ai_analysis_callback(query, user_id)
        elif action == "report":
            await self.generate_report_callback(query, context, user_id)
        elif action == "tips":
            await self.show_data_tips(query, user_id)

    async def perform_quick_analysis(self, query, user_id):
        """Быстрый анализ данных"""
        if user_id not in self.user_data or 'df' not in self.user_data[user_id]:
            await query.edit_message_text("❌ Нет данных для анализа")
            return

        df = self.user_data[user_id]['df']
        filename = self.user_data[user_id]['filename']

        await query.edit_message_text(
            "🔍 *ВЫПОЛНЯЮ БЫСТРЫЙ АНАЛИЗ...*",
            parse_mode='Markdown'
        )

        # Базовая статистика
        numeric_cols = df.select_dtypes(include='number').columns

        response = f"📊 *БЫСТРЫЙ АНАЛИЗ: {filename}*\n\n"
        response += f"📈 *ОСНОВНЫЕ МЕТРИКИ:*\n"
        response += f"• 📁 Записей: `{len(df):,}`\n"
        response += f"• 📋 Колонок: `{len(df.columns)}`\n"
        response += f"• 🔢 Числовых колонок: `{len(numeric_cols)}`\n"
        response += f"• 📝 Текстовых колонок: `{len(df.columns) - len(numeric_cols)}`\n"
        response += f"• ⚠️ Пропущенных значений: `{df.isnull().sum().sum()}`\n\n"

        if len(numeric_cols) > 0:
            response += f"📈 *СТАТИСТИКА ПО ЧИСЛОВЫМ ДАННЫМ:*\n"
            for col in numeric_cols[:2]:
                response += f"• `{col}`:\n"
                response += f"  📊 Среднее: `{df[col].mean():.2f}`\n"
                response += f"  📈 Сумма: `{df[col].sum():,.2f}`\n"
                response += f"  📉 Мин/Макс: `{df[col].min():.2f}` / `{df[col].max():.2f}`\n\n"

        response += "💡 *СЛЕДУЮЩИЕ ШАГИ:*\n"
        response += "1. Нажмите `🤖 AI Анализ` для детального анализа\n"
        response += "2. Сгенерируйте полный отчет\n"
        response += "3. Используйте веб-интерфейс для визуализации"

        await query.edit_message_text(
            response,
            reply_markup=get_analysis_menu(),
            parse_mode='Markdown'
        )

    async def perform_ai_analysis(self, update, user_id):
        """AI анализ через сообщение"""
        if user_id not in self.user_data or 'df' not in self.user_data[user_id]:
            await update.message.reply_text("❌ Сначала загрузите файл")
            return

        await update.message.reply_text(
            "🤖 *ЗАПУСКАЮ AI АНАЛИЗ...*\n\n"
            "Искусственный интеллект анализирует ваши данные...\n"
            "⏳ Это займет несколько секунд",
            parse_mode='Markdown'
        )

        await self._send_ai_analysis(update.message, user_id)

    async def perform_ai_analysis_callback(self, query, user_id):
        """AI анализ через callback"""
        if user_id not in self.user_data or 'df' not in self.user_data[user_id]:
            await query.edit_message_text("❌ Нет данных для анализа")
            return

        await query.edit_message_text(
            "🤖 *ЗАПУСКАЮ AI АНАЛИЗ...*\n\n"
            "AI анализирует структуру, тренды и аномалии...",
            parse_mode='Markdown'
        )

        await self._send_ai_analysis(query, user_id, is_callback=True)

    async def _send_ai_analysis(self, message_obj, user_id, is_callback=False):
        """Отправка AI анализа"""
        df = self.user_data[user_id]['df']
        filename = self.user_data[user_id]['filename']

        # Выполняем AI анализ
        analysis = self.analyzer.analyze_data(df)

        # Формируем красивый ответ с пагинацией
        response_parts = []

        # Часть 1: Обзор
        part1 = f"✨ *AI АНАЛИЗ: {filename}* ✨\n\n"
        part1 += analysis['overview'] + "\n\n"
        part1 += "=" * 40 + "\n\n"
        part1 += analysis['trends']

        # Часть 2: Аномалии и метрики
        part2 = analysis['anomalies'] + "\n\n"
        part2 += "=" * 40 + "\n\n"
        part2 += analysis['metrics']

        # Часть 3: Рекомендации и прогноз
        part3 = analysis['recommendations'] + "\n\n"
        part3 += "=" * 40 + "\n\n"
        part3 += analysis['forecast'] + "\n\n"
        part3 += "🎯 *ДЛЯ ПРОДВИНУТОГО АНАЛИЗА:*\n"
        part3 += "• Запустите веб-интерфейс `streamlit run ui/streamlit_app.py`\n"
        part3 += "• Настройте OpenAI GPT для AI рекомендаций\n"
        part3 += "• Интегрируйте с AmoCRM для CRM аналитики"

        if is_callback:
            # Для callback отправляем первую часть
            await message_obj.edit_message_text(
                part1[:4000],  # Telegram ограничение 4096 символов
                reply_markup=get_analysis_menu(),
                parse_mode='Markdown'
            )

            # Отправляем остальные части как новые сообщения
            try:
                await message_obj.bot.send_message(
                    chat_id=user_id,
                    text=part2[:4000],
                    parse_mode='Markdown'
                )

                await message_obj.bot.send_message(
                    chat_id=user_id,
                    text=part3[:4000],
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            # Для обычного сообщения отправляем все части
            await message_obj.reply_text(
                part1[:4000],
                parse_mode='Markdown'
            )

            await message_obj.reply_text(
                part2[:4000],
                parse_mode='Markdown'
            )

            await message_obj.reply_text(
                part3[:4000],
                reply_markup=get_analysis_menu(),
                parse_mode='Markdown'
            )

    async def generate_report(self, update, context, user_id):
        """Генерация отчета через сообщение"""
        await self._generate_report_internal(update.message, context, user_id)

    async def generate_report_callback(self, query, context, user_id):
        """Генерация отчета через callback"""
        await self._generate_report_internal(query, context, user_id, is_callback=True)

    async def _generate_report_internal(self, message_obj, context, user_id, is_callback=False):
        """Внутренняя функция генерации отчета"""
        if user_id not in self.user_data or 'df' not in self.user_data[user_id]:
            if is_callback:
                await message_obj.edit_message_text("❌ Нет данных для отчета")
            else:
                await message_obj.reply_text("❌ Нет данных для отчета")
            return

        df = self.user_data[user_id]['df']
        filename = self.user_data[user_id]['filename']

        if is_callback:
            await message_obj.edit_message_text(
                "📋 *ГЕНЕРАЦИЯ ОТЧЕТА...*\n\n"
                "Создаю профессиональный отчет...",
                parse_mode='Markdown'
            )

        # Генерируем отчет
        report_content = self._create_report_content(df, filename)

        # Сохраняем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(report_content)
            temp_path = f.name

        try:
            # Отправляем файл
            await context.bot.send_document(
                chat_id=user_id,
                document=open(temp_path, 'rb'),
                filename=f"AI_Audit_Report_{filename}.md",
                caption=f"📋 *ОТЧЕТ AI BUSINESS AUDITOR*\n\nФайл: {filename}\nДата: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                reply_markup=get_main_menu()
            )

            if is_callback:
                await message_obj.edit_message_text(
                    "✅ *ОТЧЕТ УСПЕШНО СОЗДАН!*\n\n"
                    "Проверьте файл в чате 📎",
                    reply_markup=get_main_menu(),
                    parse_mode='Markdown'
                )
            else:
                await message_obj.reply_text(
                    "✅ Отчет отправлен! Проверьте файл в чате 📎",
                    reply_markup=get_main_menu()
                )

        except Exception as e:
            error_msg = str(e)[:100]
            if is_callback:
                await message_obj.edit_message_text(f"❌ Ошибка отправки отчета: {error_msg}")
            else:
                await message_obj.reply_text(f"❌ Ошибка отправки отчета: {error_msg}")

        finally:
            # Удаляем временный файл
            try:
                os.unlink(temp_path)
            except:
                pass

    def _create_report_content(self, df, filename):
        """Создание содержимого отчета"""
        analysis = self.analyzer.analyze_data(df)

        report = f"""# 📊 ОТЧЕТ AI BUSINESS AUDITOR

## 📋 ИНФОРМАЦИЯ ОБ АНАЛИЗЕ
- **Файл:** {filename}
- **Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Записей:** {len(df):,}
- **Колонок:** {len(df.columns)}

## 📈 РЕЗУЛЬТАТЫ АНАЛИЗА

### Обзор данных
{analysis['overview'].replace('*', '**')}

### Обнаруженные тренды
{analysis['trends'].replace('*', '**')}

### Аномалии и выбросы
{analysis['anomalies'].replace('*', '**')}

### Ключевые метрики
{analysis['metrics'].replace('*', '**')}

### AI рекомендации
{analysis['recommendations'].replace('*', '**')}

### Прогноз и выводы
{analysis['forecast'].replace('*', '**')}

## 🎯 ПЛАН ДЕЙСТВИЙ

### Высокий приоритет:
1. Внедрить систему мониторинга ключевых метрик
2. Настроить регулярные аналитические отчеты
3. Интегрировать с CRM-системой (AmoCRM)

### Средний приоритет:
4. Автоматизировать сбор и обработку данных
5. Внедрить систему оповещений об аномалиях
6. Настроить дашборды для визуализации

### Долгосрочные цели:
7. Внедрить предиктивную аналитику
8. Настроить AI-рекомендательную систему
9. Оптимизировать бизнес-процессы на основе данных

---
*Отчет сгенерирован автоматически системой AI Business Auditor*
*Версия: 2.0 | AI-Powered Business Analytics*
"""

        return report

    async def show_data_tips(self, query, user_id):
        """Советы по данным"""
        if user_id not in self.user_data or 'df' not in self.user_data[user_id]:
            await query.edit_message_text("❌ Нет данных для советов")
            return

        df = self.user_data[user_id]['df']

        tips = [
            "💡 *СОВЕТ 1:* Для временных рядов добавьте колонку с датой",
            "📊 *СОВЕТ 2:* Числовые данные лучше анализировать в веб-интерфейсе",
            "🤖 *СОВЕТ 3:* Включите GPT анализ для AI-рекомендаций",
            "📈 *СОВЕТ 4:* Регулярно обновляйте данные для актуальности анализа",
            "🏢 *СОВЕТ 5:* Интегрируйте с AmoCRM для полной картины бизнеса"
        ]

        response = "🎯 *СОВЕТЫ ПО ВАШИМ ДАННЫМ*\n\n"
        response += f"📊 На основе {len(df)} записей:\n\n"
        response += "\n".join(tips[:3])

        await query.edit_message_text(
            response,
            reply_markup=get_analysis_menu(),
            parse_mode='Markdown'
        )

    async def show_amocrm_demo(self, update):
        """Демо AmoCRM"""
        # Генерация демо-данных
        leads = []
        for i in range(1, 6):
            leads.append({
                'id': i,
                'name': f'Сделка #{i}',
                'price': random.randint(10000, 500000),
                'status': random.choice(['Новая', 'В работе', 'Успешна', 'Закрыта']),
                'created': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%d.%m.%Y')
            })

        response = "🏢 *AMOCRM ИНТЕГРАЦИЯ (ДЕМО)*\n\n"
        response += "📊 *ПОСЛЕДНИЕ СДЕЛКИ:*\n\n"

        for lead in leads:
            emoji = "🟢" if lead['status'] == 'Успешна' else "🟡" if lead['status'] == 'В работе' else "🔵"
            response += f"{emoji} *{lead['name']}*\n"
            response += f"   💰 {lead['price']:,} руб.\n"
            response += f"   📊 {lead['status']}\n"
            response += f"   📅 {lead['created']}\n\n"

        response += "🔧 *ДЛЯ РЕАЛЬНОЙ ИНТЕГРАЦИИ:*\n"
        response += "1. Получите access_token в AmoCRM\n"
        response += "2. Добавьте в .env файл:\n"
        response += "   AMOCRM_ACCESS_TOKEN=ваш_токен\n"
        response += "   AMOCRM_SUBDOMAIN=ваш_домен\n"
        response += "3. Перезапустите бота\n\n"
        response += "*Готовые интеграции в веб-интерфейсе!*"

        await update.message.reply_text(
            response,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def show_business_tips(self, update):
        """Бизнес-советы"""
        tips_categories = {
            '💰 Финансы': [
                "Оптимизируйте налоговую нагрузку через легальные схемы",
                "Создайте финансовую подушку на 6 месяцев операционных расходов",
                "Диверсифицируйте источники дохода"
            ],
            '📈 Продажи': [
                "Внедрите систему сквозной аналитики",
                "Оптимизируйте воронку продаж на основе данных",
                "Увеличьте средний чек через up-sell и cross-sell"
            ],
            '👥 Клиенты': [
                "Внедрите программу лояльности",
                "Снижайте CAC через реферальную программу",
                "Увеличивайте LTV через качественный сервис"
            ],
            '⚙️ Операции': [
                "Автоматизируйте рутинные процессы",
                "Внедрите KPI для каждого сотрудника",
                "Оптимизируйте цепочки поставок"
            ]
        }

        category = random.choice(list(tips_categories.keys()))
        tip = random.choice(tips_categories[category])

        response = f"💡 *БИЗНЕС-СОВЕТ ({category})*\n\n"
        response += f"{tip}\n\n"
        response += "🎯 *ХОТИТЕ БОЛЬШЕ СОВЕТОВ?*\n"
        response += "1. Загрузите ваши данные\n"
        response += "2. Используйте AI анализ\n"
        response += "3. Получите персонализированные рекомендации"

        await update.message.reply_text(
            response,
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    async def show_help(self, update):
        """Помощь"""
        help_text = """
❓ *ПОМОЩЬ ПО БОТУ AI BUSINESS AUDITOR*

🎯 *ОСНОВНЫЕ ВОЗМОЖНОСТИ:*
• 📊 *Анализ файлов* – CSV, Excel, JSON
• 🤖 *AI Анализ* – автоматические рекомендации
• 📈 *Визуализация* – графики и дашборды
• 📋 *Отчеты* – профессиональные аналитические отчеты
• 🏢 *AmoCRM* – интеграция с CRM системами
• 💡 *Советы* – бизнес-рекомендации

📁 *КАК НАЧАТЬ:*
1. Нажмите `📊 Анализ файла`
2. Отправьте CSV/Excel файл
3. Выберите тип анализа
4. Получите результаты

📊 *ПРИМЕР ФАЙЛА:*
        Месяц,Выручка,Расходы,Прибыль
        Январь 2024,1000000,700000,300000
        Февраль 2024,1200000,800000,400000
        Март 2024,1500000,900000,600000

        🔧 *ПРОДВИНУТЫЕ ФУНКЦИИ:*
        • Веб-интерфейс: `streamlit run ui/streamlit_app.py`
        • GPT анализ: нужен OpenAI API ключ
        • AmoCRM интеграция: нужен access_token

        📞 *ПОДДЕРЖКА:*
        • Разработчик: @alex_lyubovenko
        • Проект: AI Business Auditor
        • Статус: MVP готов на 90%
                """

        await update.message.reply_text(
            dedent(help_text),
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

        # ========== ЗАПУСК БОТА ==========

    def setup_handlers(self, application):
        """Настройка обработчиков"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.show_help))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def post_init(self, application):
        """После инициализации"""
        logger.info("✅ AI Business Auditor Bot запущен!")

        try:
            await application.bot.send_message(
                chat_id=int(ADMIN_ID),
                text="✨ *AI BUSINESS AUDITOR BOT ЗАПУЩЕН!* ✨\n\n"
                     "🤖 *Версия:* С AI анализом и красивым интерфейсом\n"
                     "📊 *Функции:* Анализ файлов, AI рекомендации, отчеты\n"
                     "🏢 *Интеграции:* AmoCRM (демо)\n\n"
                     "🎯 *Готов к работе!*\n"
                     "Напишите /start для начала",
                parse_mode='Markdown'
            )
            print(f"✅ Приветствие отправлено админу {ADMIN_ID}")
        except Exception as e:
            print(f"⚠️ Не удалось отправить приветствие: {e}")

    def run(self):
        """Запуск бота"""
        application = Application.builder().token(TOKEN).post_init(self.post_init).build()
        self.setup_handlers(application)

        # Обработка ошибок
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Ошибка бота: {context.error}")

        application.add_error_handler(error_handler)

        # Запуск
        print("\n" + "=" * 60)
        print("🎉 БОТ УСПЕШНО ЗАПУЩЕН!")
        print("=" * 60)
        print("\n📱 Откройте Telegram")
        print("🔍 Найдите вашего бота")
        print("💬 Напишите /start")
        print("📤 Отправьте файл для AI анализа")
        print("👋 Ctrl+C для остановки")
        print("\n" + "=" * 60)

        application.run_polling(allowed_updates=Update.ALL_TYPES)

    # ========== ЗАПУСК ==========
    def main():
        print("\n🚀 ИНИЦИАЛИЗАЦИЯ AI BUSINESS AUDITOR BOT...")

        try:
            bot = AITelegramBot()
            bot.run()
        except KeyboardInterrupt:
            print("\n\n👋 Бот остановлен пользователем")
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        main()