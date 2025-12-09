"""
Адаптер для DataAnalyzer для совместимости с Telegram ботом
"""

import sys
from pathlib import Path

# Добавляем путь к agents
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
agents_path = project_root / "agents"
if str(agents_path) not in sys.path:
    sys.path.insert(0, str(agents_path))

try:
    from analyzer import DataAnalyzer


    class AdaptedDataAnalyzer:
        """Адаптер для DataAnalyzer для работы с Telegram ботом"""

        def __init__(self):
            self.analyzer = DataAnalyzer()

        def basic_analysis(self, df):
            """Базовый анализ с извлечением трендов и метрик"""
            try:
                # Вызываем оригинальный метод
                result = self.analyzer.basic_analysis(df)

                # Если метод возвращает только словарь, преобразуем его
                if isinstance(result, dict):
                    # Извлекаем тренды и метрики если они есть
                    trends = result.get('trends', [])
                    financial_metrics = result.get('financial_metrics', {})

                    # Добавляем если их нет
                    if 'trends' not in result:
                        result['trends'] = trends
                    if 'financial_metrics' not in result:
                        result['financial_metrics'] = financial_metrics

                return result

            except Exception as e:
                # Возвращаем структуру по умолчанию
                return {
                    'record_count': len(df),
                    'columns': list(df.columns),
                    'summary': f'Базовый анализ выполнен. {str(e)[:100]}',
                    'trends': [],
                    'financial_metrics': {},
                    'recommendations': ['Загрузите веб-версию для полного анализа']
                }

        def gpt_analysis(self, df):
            """GPT анализ с автоматическим извлечением параметров"""
            try:
                # Сначала получаем базовый анализ
                basic = self.basic_analysis(df)

                # Извлекаем тренды и метрики
                trends = basic.get('trends', [])
                financial_metrics = basic.get('financial_metrics', {})

                # Вызываем GPT анализ с параметрами
                return self.analyzer.gpt_analysis(
                    df,
                    trends=trends,
                    financial_metrics=financial_metrics
                )

            except TypeError as e:
                # Если метод не принимает параметры, пробуем без них
                if "positional argument" in str(e):
                    try:
                        return self.analyzer.gpt_analysis(df)
                    except Exception as e2:
                        return f"🤖 *GPT Анализ (адаптивный режим):*\n\nОшибка: {str(e2)[:200]}"
                else:
                    return f"🤖 *GPT Анализ:*\n\nОшибка: {str(e)[:200]}"

            except Exception as e:
                return f"🤖 *GPT Анализ:*\n\nОшибка: {str(e)[:200]}"


    # Экспортируем адаптированный анализатор
    analyzer = AdaptedDataAnalyzer()

except ImportError:
    # Демо-режим если анализатор не найден
    class DemoAnalyzer:
        def basic_analysis(self, df):
            return {
                'record_count': len(df),
                'columns': list(df.columns),
                'summary': 'Демо-анализ: используйте веб-версию для полного функционала',
                'trends': [],
                'financial_metrics': {},
                'recommendations': ['Загрузите в веб-интерфейс для GPT анализа']
            }

        def gpt_analysis(self, df):
            numeric_cols = df.select_dtypes(include='number').columns

            if len(numeric_cols) > 0:
                response = "🤖 *GPT Анализ (демо-режим)*\n\n"
                response += "📊 *Обнаруженные тренды:*\n"

                for col in numeric_cols[:2]:
                    mean_val = df[col].mean()
                    response += f"• `{col}`: среднее значение {mean_val:,.2f}\n"

                response += "\n💡 *Рекомендации:*\n"
                response += "1. Используйте веб-интерфейс для полного GPT анализа\n"
                response += "2. Добавьте OpenAI API ключ в .env файл\n"
                response += "3. Настройте интеграцию с AmoCRM\n"

                return response
            else:
                return "🤖 *GPT Анализ:* Загрузите файл с числовыми данными для анализа"


    analyzer = DemoAnalyzer()