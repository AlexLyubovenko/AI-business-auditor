import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import warnings

# Опциональный импорт scipy
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ SciPy не установлен. Некоторые статистические функции будут использовать numpy.")


class DataAnalyzer:
    """Анализатор данных для бизнес-аналитики с AI анализом через OpenAI GPT"""

    def __init__(self):
        self.warnings = []

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Основной анализ данных"""
        try:
            results = {
                'metrics': self._calculate_metrics(df),
                'trends': self._detect_trends(df),
                'patterns': self._find_patterns(df),
                'anomalies': self._detect_anomalies(df),
                'recommendations': self._generate_recommendations(df),
                'summary': self._create_summary(df)
            }
            return results
        except Exception as e:
            return {'error': str(e)}

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Расчет ключевых метрик"""
        metrics = {}

        # Базовые метрики
        metrics['total_records'] = len(df)
        metrics['total_columns'] = len(df.columns)

        # Числовые метрики
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            metrics['numeric_columns'] = len(numeric_cols)

            for col in numeric_cols[:5]:  # Ограничиваем первыми 5 колонками
                metrics[f'{col}_mean'] = float(df[col].mean())
                metrics[f'{col}_median'] = float(df[col].median())
                metrics[f'{col}_std'] = float(df[col].std())
                metrics[f'{col}_sum'] = float(df[col].sum())
                metrics[f'{col}_min'] = float(df[col].min())
                metrics[f'{col}_max'] = float(df[col].max())

        # Процент пропущенных значений
        missing_total = df.isnull().sum().sum()
        metrics['missing_values'] = missing_total
        metrics['missing_percentage'] = float(missing_total / (len(df) * len(df.columns)) * 100)

        return metrics

    def _detect_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Обнаружение трендов"""
        trends = []

        # Ищем колонки с датами
        date_cols = df.select_dtypes(include=['datetime64']).columns

        if len(date_cols) > 0:
            date_col = date_cols[0]
            numeric_cols = df.select_dtypes(include=[np.number]).columns

            for col in numeric_cols:
                if len(df) > 1:
                    try:
                        # Используем numpy если scipy недоступен
                        if SCIPY_AVAILABLE:
                            slope, intercept, r_value, p_value, std_err = stats.linregress(
                                range(len(df)), df[col].fillna(df[col].mean())
                            )
                        else:
                            # Простая линейная регрессия через numpy
                            x = np.arange(len(df))
                            y = df[col].fillna(df[col].mean()).values
                            A = np.vstack([x, np.ones(len(x))]).T
                            slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
                            r_value = np.corrcoef(x, y)[0, 1]
                            p_value = None
                            std_err = np.std(y - (slope * x + intercept))

                        direction = "рост" if slope > 0 else "снижение"
                        strength = "сильный" if abs(r_value) > 0.7 else "умеренный" if abs(r_value) > 0.3 else "слабый"

                        trends.append({
                            'Метрика': col,
                            'Направление': direction,
                            'Сила': strength,
                            'Наклон': float(slope),
                            'R-квадрат': float(r_value ** 2),
                            'Значимость': "значим" if (p_value is None or p_value < 0.05) else "незначим"
                        })
                    except Exception as e:
                        print(f"Ошибка анализа тренда для {col}: {e}")
                        continue

        return trends

    def _find_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Поиск паттернов в данных"""
        patterns = {}

        # Корреляции
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            correlations = {}
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    try:
                        if SCIPY_AVAILABLE:
                            corr, p_value = stats.pearsonr(
                                df[col1].fillna(df[col1].mean()),
                                df[col2].fillna(df[col2].mean())
                            )
                        else:
                            corr = np.corrcoef(
                                df[col1].fillna(df[col1].mean()),
                                df[col2].fillna(df[col2].mean())
                            )[0, 1]
                            p_value = None

                        if abs(corr) > 0.7:
                            correlations[f'{col1}_{col2}'] = {
                                'correlation': float(corr),
                                'strength': 'сильная',
                                'significance': 'значимая' if (p_value is None or p_value < 0.05) else 'незначимая'
                            }
                    except:
                        continue

            patterns['correlations'] = correlations

        # Сезонность
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            date_col = date_cols[0]
            patterns['has_dates'] = True
            patterns['date_range'] = {
                'start': str(df[date_col].min()),
                'end': str(df[date_col].max()),
                'duration_days': (df[date_col].max() - df[date_col].min()).days
            }

        return patterns

    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Обнаружение аномалий"""
        anomalies = {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            try:
                values = df[col].dropna()
                if len(values) > 10:
                    mean = values.mean()
                    std = values.std()

                    # Простой метод 3-сигм
                    lower_bound = mean - 3 * std
                    upper_bound = mean + 3 * std

                    outlier_count = ((values < lower_bound) | (values > upper_bound)).sum()
                    if outlier_count > 0:
                        anomalies[col] = {
                            'outlier_count': int(outlier_count),
                            'percentage': float(outlier_count / len(values) * 100),
                            'mean': float(mean),
                            'std': float(std),
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound)
                        }
            except:
                continue

        return anomalies

    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Генерация рекомендаций на основе анализа"""
        recommendations = []

        # Проверка на пропущенные значения
        missing_percentage = (df.isnull().sum() / len(df) * 100)
        high_missing = missing_percentage[missing_percentage > 20].index.tolist()

        if high_missing:
            recommendations.append({
                'type': 'data_quality',
                'priority': 'high',
                'text': f'Высокий процент пропущенных значений в колонках: {", ".join(high_missing[:3])}'
            })

        # Рекомендации по данным
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:
                if df[col].std() / df[col].mean() > 0.5:
                    recommendations.append({
                        'type': 'data_variability',
                        'priority': 'medium',
                        'text': f'Высокая волатильность в {col}. Рассмотрите нормализацию.'
                    })

        # Общие рекомендации
        if len(df) > 1000:
            recommendations.append({
                'type': 'performance',
                'priority': 'low',
                'text': 'Большой объем данных. Рассмотрите использование индексов для ускорения запросов.'
            })

        return recommendations

    def _create_summary(self, df: pd.DataFrame) -> str:
        """Создание краткого резюме"""
        summary_parts = []

        summary_parts.append(f"Данные содержат {len(df)} записей и {len(df.columns)} колонок.")

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"Найдено {len(numeric_cols)} числовых колонок.")

        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            summary_parts.append(f"Обнаружены временные ряды: {', '.join(date_cols[:3])}.")

        missing_total = df.isnull().sum().sum()
        if missing_total > 0:
            summary_parts.append(
                f"Пропущенные значения: {missing_total} ({missing_total / (len(df) * len(df.columns)) * 100:.1f}%).")

        return " ".join(summary_parts)

    def gpt_analysis(self, df: pd.DataFrame = None, data_summary=None, trends=None, financial_metrics=None) -> str:
        """Реальный AI анализ данных через OpenAI GPT"""
        try:
            # Пробуем импортировать OpenAI
            import openai

            # Проверяем наличие API ключа
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                return self._get_fallback_analysis(df, trends, financial_metrics)

            # Создаем клиент OpenAI
            client = openai.OpenAI(api_key=api_key)

            # Создаем промпт для GPT
            prompt = self._create_gpt_prompt(df, data_summary, trends, financial_metrics)

            try:
                # Отправляем запрос к GPT
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": """Ты опытный бизнес-аналитик и консультант. 
                            Твоя задача - анализировать бизнес-данные и давать практические, конкретные рекомендации.
                            Отвечай на русском языке. Используй маркдаун форматирование.
                            Будь объективным, но конструктивным. Выделяй как сильные стороны, так и области для улучшения."""
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.7,
                    top_p=0.9
                )

                # Возвращаем ответ от GPT
                return response.choices[0].message.content

            except openai.RateLimitError:
                return "⚠️ Превышен лимит запросов к OpenAI API. Попробуйте позже."
            except openai.APITimeoutError:
                return "⚠️ Таймаут при обращении к OpenAI API. Проверьте подключение к интернету."
            except Exception as e:
                error_msg = str(e)
                if "insufficient_quota" in error_msg:
                    return "⚠️ Закончился баланс на OpenAI API. Пополните счет."
                return f"⚠️ Ошибка OpenAI API: {error_msg[:200]}"

        except ImportError:
            return self._get_fallback_analysis(df, trends, financial_metrics)

    def _create_gpt_prompt(self, df: pd.DataFrame, data_summary, trends, financial_metrics) -> str:
        """Создание промпта для GPT анализа"""

        prompt_parts = ["# 🔍 АНАЛИЗ БИЗНЕС-ДАННЫХ\n\n"]

        # Информация о данных
        if df is not None:
            prompt_parts.append("## 📊 СТРУКТУРА ДАННЫХ:")
            prompt_parts.append(f"- **Объем данных:** {len(df)} записей, {len(df.columns)} колонок")

            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                prompt_parts.append(f"- **Числовые колонки ({len(numeric_cols)}):** {', '.join(numeric_cols[:5])}")
                if len(numeric_cols) > 5:
                    prompt_parts.append(f"  ... и еще {len(numeric_cols) - 5} колонок")

            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                prompt_parts.append(
                    f"- **Текстовые колонки ({len(categorical_cols)}):** {', '.join(categorical_cols[:3])}")

            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                for col in date_cols[:2]:
                    prompt_parts.append(
                        f"- **Временной ряд {col}:** с {df[col].min().date()} по {df[col].max().date()}")

        # Сводка если есть
        if data_summary:
            prompt_parts.append("\n## 📈 ОСНОВНАЯ СВОДКА:")
            if isinstance(data_summary, str):
                prompt_parts.append(data_summary)
            elif isinstance(data_summary, dict) and 'summary' in data_summary:
                prompt_parts.append(data_summary['summary'])

        # Тренды
        if trends and len(trends) > 0:
            prompt_parts.append("\n## 📈 ОБНАРУЖЕННЫЕ ТРЕНДЫ:")
            for trend in trends[:5]:
                metric = trend.get('Метрика', 'Метрика')
                direction = trend.get('Направление', 'стабильный')
                strength = trend.get('Сила', 'средний')
                r_squared = trend.get('R-квадрат', 0)
                prompt_parts.append(f"- **{metric}:** {direction} ({strength}, R²={r_squared:.3f})")

        # Финансовые метрики
        if financial_metrics:
            prompt_parts.append("\n## 💰 КЛЮЧЕВЫЕ МЕТРИКИ:")
            for key, value in list(financial_metrics.items())[:8]:
                if isinstance(value, (int, float)):
                    if abs(value) >= 1000000:
                        display_value = f"{value / 1000000:.2f} млн"
                    elif abs(value) >= 1000:
                        display_value = f"{value / 1000:.1f} тыс"
                    else:
                        display_value = f"{value:,.0f}"

                    key_display = key.replace('_', ' ').title()
                    prompt_parts.append(f"- **{key_display}:** {display_value}")

        # Примеры данных
        if df is not None and len(df) > 0:
            prompt_parts.append("\n## 🎯 ЗАДАЧА ДЛЯ AI-АНАЛИТИКА:")
        else:
            prompt_parts.append("\n## 🎯 ЗАДАЧА ДЛЯ AI-АНАЛИТИКА (на основе предоставленной информации):")

        prompt_parts.append("""
Проанализируй бизнес-данные и предоставь структурированный отчет:

### 1. КЛЮЧЕВЫЕ ВЫВОДЫ (самое важное):
- Основные сильные стороны бизнеса
- Критические проблемы и риски (если есть)
- Главные возможности для роста

### 2. ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ:
- **Краткосрочные** (1-3 месяца): конкретные, быстрые действия
- **Долгосрочные** (6-12 месяцев): стратегические улучшения
- **Метрики для отслеживания:** какие KPI отслеживать

### 3. ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ (топ-3):
1. Что сделать в первую очередь
2. Что сделать во вторую очередь
3. Что сделать в третью очередь

### 4. РИСКИ И ПРЕДУПРЕЖДЕНИЯ:
- На что обратить особое внимание
- Чего следует избегать
- Потенциальные проблемы

### 5. ВЫВОДЫ:
- Итоговое резюме анализа
- Общая оценка состояния бизнеса
- Прогноз при выполнении рекомендаций

**Формат:** Используй маркдаун с заголовками ## и ###, списки, жирный текст для акцентов.
**Тон:** Профессиональный, конструктивный, полезный для владельца бизнеса.
**Объем:** Подробный, но без воды. 800-1200 слов.
""")

        return "\n".join(prompt_parts)

    def _get_fallback_analysis(self, df, trends, financial_metrics) -> str:
        """Запасной анализ если OpenAI недоступен"""

        analysis_parts = ["# 🤖 AI АНАЛИЗ БИЗНЕС-ДАННЫХ\n"]
        analysis_parts.append("*⚠️ Режим локального анализа (OpenAI API не настроен)*\n")

        if df is not None:
            analysis_parts.append(f"## 📊 АНАЛИЗИРУЕМЫЕ ДАННЫЕ")
            analysis_parts.append(f"- **Объем:** {len(df)} записей, {len(df.columns)} колонок")

            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                analysis_parts.append(f"- **Числовые данные:** {len(numeric_cols)} колонок")
                top_numeric = numeric_cols[:3]
                for col in top_numeric:
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    analysis_parts.append(f"  • **{col}:** среднее = {mean_val:,.0f}, отклонение = {std_val:,.0f}")

            # Анализ качества данных
            missing_total = df.isnull().sum().sum()
            if missing_total > 0:
                missing_pct = missing_total / (len(df) * len(df.columns)) * 100
                analysis_parts.append(f"- **Качество данных:** {missing_pct:.1f}% пропущенных значений")

        if trends and len(trends) > 0:
            analysis_parts.append("\n## 📈 ОСНОВНЫЕ ТРЕНДЫ")
            for trend in trends[:3]:
                metric = trend.get('Метрика', 'Метрика')
                direction = trend.get('Направление', 'стабильный')
                analysis_parts.append(f"- **{metric}:** {direction}")

        analysis_parts.append("""
## 💡 РЕКОМЕНДАЦИИ (локальный анализ)

### 1. КЛЮЧЕВЫЕ ВЫВОДЫ:
- Проведен базовый анализ структуры данных
- Обнаружены основные метрики и тренды
- Требуется настройка OpenAI API для глубокого AI анализа

### 2. ДЕЙСТВИЯ:
1. **Настройте OpenAI API** для получения AI рекомендаций
2. **Загрузите дополнительные данные** для более полного анализа
3. **Используйте веб-интерфейс** для визуализации и отчетов

### 3. СЛЕДУЮЩИЕ ШАГИ:
- Добавьте OPENAI_API_KEY в настройках
- Перезапустите AI анализ
- Получите персонализированные рекомендации от GPT

## 🔧 КАК НАСТРОИТЬ AI АНАЛИЗ:
1. Получите API ключ на platform.openai.com
2. Добавьте в .env файл: `OPENAI_API_KEY=ваш_ключ`
3. Перезапустите приложение
""")

        return "\n".join(analysis_parts)

    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Получение сводки данных для AI анализа"""
        if df is None or df.empty:
            return {}

        return {
            'shape': df.shape,
            'dtypes': df.dtypes.astype(str).to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'date_columns': df.select_dtypes(include=['datetime64']).columns.tolist(),
            'missing_values': df.isnull().sum().to_dict(),
            'basic_stats': df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {},
            'summary': self._create_summary(df)
        }

    def basic_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Базовый анализ для Telegram бота"""
        if df is None or df.empty:
            return {"error": "Пустой DataFrame"}

        try:
            analysis = self.analyze(df)
            return analysis
        except Exception as e:
            return {"error": str(e)}