import pandas as pd
import numpy as np
from scipy import stats
import json
import os
from datetime import datetime, timedelta
import requests


class DataAnalyzer:
    """Анализатор данных с улучшенным AI анализом"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def analyze(self, df):
        """Основной анализ данных"""
        try:
            results = {
                'metrics': self._calculate_metrics(df),
                'trends': self._detect_trends(df),
                'summary': self.get_data_summary(df),
                'recommendations': self._generate_recommendations(df)
            }
            return results
        except Exception as e:
            print(f"Ошибка анализа: {e}")
            return None

    def _calculate_metrics(self, df):
        """Расчет основных метрик"""
        metrics = {}

        # Ищем числовые колонки
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) == 0:
            return {"error": "Нет числовых данных для анализа"}

        # Базовые статистики
        for col in numeric_cols[:10]:  # Ограничиваем количество колонок
            try:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    metrics[f'{col}_mean'] = float(col_data.mean())
                    metrics[f'{col}_median'] = float(col_data.median())
                    metrics[f'{col}_std'] = float(col_data.std())
                    metrics[f'{col}_min'] = float(col_data.min())
                    metrics[f'{col}_max'] = float(col_data.max())
            except:
                pass

        # Финансовые метрики (если есть соответствующие колонки)
        col_names_lower = [str(col).lower() for col in df.columns]

        # Выручка
        revenue_cols = [col for col in numeric_cols if any(word in str(col).lower()
                                                           for word in ['выруч', 'reven', 'доход', 'income', 'sale'])]
        if revenue_cols:
            revenue = df[revenue_cols[0]].sum()
            metrics['Total_Revenue'] = float(revenue)
            metrics['Avg_Revenue'] = float(revenue / len(df)) if len(df) > 0 else 0

        # Прибыль
        profit_cols = [col for col in numeric_cols if any(word in str(col).lower()
                                                          for word in ['прибыл', 'profit', 'марж', 'margin'])]
        if profit_cols:
            profit = df[profit_cols[0]].sum()
            metrics['Total_Profit'] = float(profit)
            metrics['Avg_Profit'] = float(profit / len(df)) if len(df) > 0 else 0

        # Расходы
        cost_cols = [col for col in numeric_cols if any(word in str(col).lower()
                                                        for word in ['расход', 'затрат', 'cost', 'expense'])]
        if cost_cols:
            cost = df[cost_cols[0]].sum()
            metrics['Total_Cost'] = float(cost)

        # Расчет маржи (если есть выручка и расходы)
        if 'Total_Revenue' in metrics and 'Total_Cost' in metrics:
            revenue = metrics['Total_Revenue']
            cost = metrics['Total_Cost']
            if revenue > 0:
                profit = revenue - cost
                metrics['Gross_Profit'] = float(profit)
                metrics['Gross_Margin_Percent'] = float((profit / revenue) * 100)

        # Рост (если есть временные данные)
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0 and len(revenue_cols) > 0:
            date_col = date_cols[0]
            revenue_col = revenue_cols[0]

            try:
                # Сортируем по дате
                df_sorted = df.sort_values(date_col)
                if len(df_sorted) >= 2:
                    first_rev = df_sorted.iloc[0][revenue_col]
                    last_rev = df_sorted.iloc[-1][revenue_col]

                    if first_rev > 0:
                        growth = ((last_rev - first_rev) / first_rev) * 100
                        metrics['Revenue_Growth_Percent'] = float(growth)
            except:
                pass

        return metrics

    def _detect_trends(self, df):
        """Обнаружение трендов в данных"""
        trends = []

        # Ищем временные данные
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) == 0:
            return trends

        date_col = date_cols[0]
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for num_col in numeric_cols[:5]:  # Анализируем первые 5 числовых колонок
            try:
                # Убираем пропуски и сортируем по дате
                temp_df = df[[date_col, num_col]].dropna()
                if len(temp_df) < 3:
                    continue

                temp_df = temp_df.sort_values(date_col)

                # Преобразуем даты в числовой формат для регрессии
                temp_df['date_numeric'] = (temp_df[date_col] - temp_df[date_col].min()).dt.days

                # Линейная регрессия
                x = temp_df['date_numeric'].values
                y = temp_df[num_col].values

                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

                # Определяем силу и направление тренда
                if abs(slope) < 0.1:
                    strength = "слабый"
                elif abs(slope) < 0.5:
                    strength = "умеренный"
                else:
                    strength = "сильный"

                direction = "рост" if slope > 0 else "снижение"

                trends.append({
                    'Метрика': num_col,
                    'Направление': direction,
                    'Сила': strength,
                    'Наклон': float(slope),
                    'R^2': float(r_value ** 2),
                    'Значимость': p_value < 0.05
                })

            except Exception as e:
                continue

        return trends

    def get_data_summary(self, df):
        """Получение сводки по данным"""
        summary = {
            'rows': len(df),
            'columns': len(df.columns),
            'missing_values': int(df.isnull().sum().sum()),
            'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
            'date_columns': len(df.select_dtypes(include=['datetime64']).columns),
            'text_columns': len(df.select_dtypes(include=['object']).columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }

        # Информация о колонках
        columns_info = []
        for col in df.columns:
            col_info = {
                'name': col,
                'type': str(df[col].dtype),
                'unique': df[col].nunique(),
                'missing': df[col].isnull().sum()
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                col_info['min'] = float(df[col].min()) if not df[col].isnull().all() else None
                col_info['max'] = float(df[col].max()) if not df[col].isnull().all() else None
                col_info['mean'] = float(df[col].mean()) if not df[col].isnull().all() else None

            columns_info.append(col_info)

        summary['columns_info'] = columns_info
        return summary

    def _generate_recommendations(self, df):
        """Генерация базовых рекомендаций"""
        recommendations = []

        # Проверка на пропущенные значения
        missing = df.isnull().sum().sum()
        if missing > 0:
            recommendations.append({
                'type': 'Данные',
                'text': f'Обнаружено {missing} пропущенных значений. Рекомендуется заполнить или удалить их.',
                'priority': 'medium'
            })

        # Проверка на выбросы в числовых колонках
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols[:3]:  # Проверяем первые 3 колонки
            try:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                if len(outliers) > 0:
                    recommendations.append({
                        'type': 'Анализ',
                        'text': f'В колонке "{col}" обнаружено {len(outliers)} выбросов.',
                        'priority': 'low'
                    })
            except:
                pass

        # Проверка на однородность данных
        for col in df.columns:
            if df[col].nunique() == 1:
                recommendations.append({
                    'type': 'Данные',
                    'text': f'Колонка "{col}" содержит только одно значение. Возможно, её можно удалить.',
                    'priority': 'low'
                })

        return recommendations

    def gpt_analysis(self, data_summary, trends, financial_metrics):
        """Улучшенный GPT анализ с подробными ответами"""

        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "⚠️ OpenAI API ключ не настроен. Добавьте ключ в .env файл."

        # Формируем подробный промпт
        prompt = self._create_detailed_prompt(data_summary, trends, financial_metrics)

        try:
            # Используем ручной запрос к OpenAI API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": """Ты - старший бизнес-аналитик с 20-летним опытом. 
                        Твоя задача - дать максимально подробный, полезный и практичный анализ бизнес-данных.
                        Используй профессиональную терминологию, но объясняй понятно.
                        Структурируй ответ с четкими разделами."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2500,
                "top_p": 0.9
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                return self._format_ai_response(analysis)
            else:
                return f"❌ Ошибка API: {response.status_code}\n{response.text}"

        except Exception as e:
            return f"❌ Ошибка подключения к OpenAI: {e}"

    def _create_detailed_prompt(self, data_summary, trends, financial_metrics):
        """Создание подробного промпта для GPT"""

        # Форматируем данные для промпта
        trends_text = ""
        if trends:
            trends_text = "## ОБНАРУЖЕННЫЕ ТРЕНДЫ:\n"
            for trend in trends:
                trends_text += f"- {trend['Метрика']}: {trend['Направление']} ({trend['Сила']}), наклон: {trend['Наклон']:.4f}\n"

        metrics_text = ""
        if financial_metrics:
            metrics_text = "## ФИНАНСОВЫЕ МЕТРИКИ:\n"
            for key, value in list(financial_metrics.items())[:15]:  # Ограничиваем количество
                if isinstance(value, (int, float)):
                    if abs(value) >= 1000000:
                        formatted = f"{value / 1000000:.2f} млн"
                    elif abs(value) >= 1000:
                        formatted = f"{value / 1000:.1f} тыс"
                    else:
                        formatted = f"{value:.2f}"

                    if 'Percent' in key or '%' in key:
                        formatted = f"{value:.1f}%"

                    metrics_text += f"- {key}: {formatted}\n"

        summary_text = f"""
        ## СВОДКА ДАННЫХ:
        - Строк: {data_summary.get('rows', 'N/A')}
        - Колонок: {data_summary.get('columns', 'N/A')}
        - Числовых колонок: {data_summary.get('numeric_columns', 'N/A')}
        - Колонок с датами: {data_summary.get('date_columns', 'N/A')}
        - Пропущенных значений: {data_summary.get('missing_values', 'N/A')}
        """

        prompt = f"""
        # ЗАДАНИЕ: ДЕТАЛЬНЫЙ БИЗНЕС-АНАЛИЗ

        ## ДАННЫЕ ДЛЯ АНАЛИЗА:

        {summary_text}

        {metrics_text}

        {trends_text}

        ## ТРЕБОВАНИЯ К АНАЛИЗУ:

        Сделай максимально подробный бизнес-анализ по следующей структуре:

        ### 1. 📊 ОБЩАЯ ОЦЕНКА БИЗНЕС-СИТУАЦИИ
        - Общее состояние бизнеса (от 1 до 10 баллов)
        - Ключевые сильные стороны
        - Основные проблемы и вызовы
        - Общая рекомендация для руководства

        ### 2. 💰 ГЛУБОКИЙ ФИНАНСОВЫЙ АНАЛИЗ
        - Анализ выручки: динамика, стабильность, сезонность
        - Анализ прибыльности: маржинальность, рентабельность
        - Анализ затрат: структура, эффективность, точки оптимизации
        - Финансовая устойчивость и риски

        ### 3. 📈 АНАЛИЗ ТРЕНДОВ И ПРОГНОЗ
        - Детальный анализ каждого тренда (причины, последствия)
        - Прогноз на 30/60/90 дней
        - Ранние индикаторы проблем
        - Точки роста и возможности

        ### 4. ⚠️ РИСКИ И ВЫЗОВЫ (ДЕТАЛЬНО)
        - Операционные риски
        - Финансовые риски
        - Рыночные риски
        - Риски, связанные с данными

        ### 5. 🎯 КОНКРЕТНЫЕ РЕКОМЕНДАЦИИ ПО ПРИОРИТЕТАМ

        #### СРОЧНЫЕ МЕРЫ (1-7 дней):
        1. ...
        2. ...
        3. ...

        #### СТРАТЕГИЧЕСКИЕ ШАГИ (1-3 месяца):
        1. ...
        2. ...
        3. ...

        #### ОПТИМИЗАЦИОННЫЕ ВОЗМОЖНОСТИ:
        1. ...
        2. ...
        3. ...

        ### 6. 📋 KPI ДЛЯ ОТСЛЕЖИВАНИЯ
        - Ежедневные метрики
        - Еженедельные отчеты
        - Критические показатели

        ### 7. 🔮 ПРОГНОЗ И СЦЕНАРИИ
        - Оптимистичный сценарий
        - Базовый сценарий
        - Пессимистичный сценарий

        ### 8. 💡 ИНСАЙТЫ И НАБЛЮДЕНИЯ
        - Неочевидные взаимосвязи
        - Скрытые возможности
        - Угрозы, которые могут быть упущены

        Дай максимально подробный, конкретный и полезный для бизнеса анализ.
        Используй числа, проценты и конкретные примеры.
        """

        return prompt

    def _format_ai_response(self, analysis_text):
        """Форматирование ответа AI для красивого отображения"""

        # Добавляем заголовки и улучшаем форматирование
        formatted = f"""
        # 🤖 AI БИЗНЕС-АНАЛИЗ

        *Анализ выполнен с помощью искусственного интеллекта на основе предоставленных данных*
        *Время анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

        ---

        {analysis_text}

        ---

        *⚠️ ВНИМАНИЕ: Данный анализ является рекомендательным. При принятии важных бизнес-решений рекомендуется консультация с экспертами.*
        """

        return formatted