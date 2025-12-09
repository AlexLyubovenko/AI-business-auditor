import json
from datetime import datetime
import pandas as pd
from typing import Dict, Any
import os


class ReportGenerator:
    """Генератор отчетов"""

    def __init__(self):
        self.template = """
# 📊 Отчет бизнес-аудита
**Дата генерации:** {date}
**Тип анализа:** {analysis_type}

## 📈 Резюме анализа
{summary}

## 📊 Ключевые метрики
{metrics_table}

## 📈 Выявленные тренды
{trends_section}

## ⚠️ Обнаруженные аномалии
{anomalies_section}

## 🤖 Анализ ИИ
{ai_analysis}

## 🎯 Рекомендации
{recommendations}

---

*Отчет сгенерирован автоматически системой AI Business Auditor*
*Для детальной консультации обратитесь к специалисту*
"""

    def generate_markdown_report(self, analysis_results: Dict) -> str:
        """Генерация отчета в формате Markdown"""
        try:
            # Форматирование метрик
            metrics_table = ""
            metrics = analysis_results.get("financial_metrics", {})

            if metrics:
                metrics_table = "| Метрика | Значение |\n"
                metrics_table += "|---------|----------|\n"

                for key, value in metrics.items():
                    if value is not None:
                        # Форматирование ключа
                        key_display = key.replace('_', ' ').title()

                        # Форматирование значения
                        if isinstance(value, (int, float)):
                            if 'percent' in key.lower() or 'margin' in key.lower() or 'growth' in key.lower():
                                value_display = f"{value:.1f}%"
                            else:
                                value_display = f"{value:,.0f}"
                        else:
                            value_display = str(value)

                        metrics_table += f"| {key_display} | {value_display} |\n"

            # Форматирование трендов
            trends_section = ""
            trends = analysis_results.get("trends", {})

            if trends:
                for col, trend_info in trends.items():
                    direction = trend_info.get("direction", "неизвестно")
                    strength = trend_info.get("strength", "неизвестно")
                    trends_section += f"- **{col}**: {direction} ({strength})\n"
            else:
                trends_section = "Значимые тренды не обнаружены.\n"

            # Форматирование аномалий
            anomalies_section = ""
            anomalies = analysis_results.get("anomalies", [])

            if anomalies:
                anomalies_section = f"Обнаружено {len(anomalies)} аномалий:\n\n"
                for i, anomaly in enumerate(anomalies[:5], 1):  # Показываем первые 5
                    anomalies_section += f"{i}. **{anomaly.get('column')}** - строка {anomaly.get('row_index')}: "
                    anomalies_section += f"значение {anomaly.get('value')} ({anomaly.get('deviation', '')} нормы)\n"

                if len(anomalies) > 5:
                    anomalies_section += f"\n*... и еще {len(anomalies) - 5} аномалий*"
            else:
                anomalies_section = "Аномалии не обнаружены.\n"

            # Анализ ИИ
            ai_analysis = ""
            llm_insights = analysis_results.get("llm_insights", {})

            if llm_insights and llm_insights.get("llm_used", False):
                llm_data = llm_insights.get("llm_analysis", {})

                if "insights" in llm_data and llm_data["insights"]:
                    ai_analysis += "### 💡 Ключевые выводы ИИ:\n"
                    for insight in llm_data["insights"]:
                        ai_analysis += f"- {insight}\n"
                    ai_analysis += "\n"

                recommendations = ""
                if "recommendations" in llm_data and llm_data["recommendations"]:
                    recommendations += "### 🎯 Рекомендации ИИ:\n"
                    for rec in llm_data["recommendations"]:
                        recommendations += f"- {rec}\n"
                else:
                    recommendations = "Рекомендации не сгенерированы.\n"
            else:
                ai_analysis = "Расширенный анализ с ИИ не выполнялся.\n"
                recommendations = "Для получения рекомендаций включите GPT-анализ.\n"

            # Заполнение шаблона
            report = self.template.format(
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                analysis_type=analysis_results.get("analysis_type", "Неизвестно"),
                summary=analysis_results.get("summary", "Анализ завершен."),
                metrics_table=metrics_table if metrics_table else "Метрики не рассчитаны.\n",
                trends_section=trends_section,
                anomalies_section=anomalies_section,
                ai_analysis=ai_analysis,
                recommendations=recommendations
            )

            return report

        except Exception as e:
            return f"""# 📊 Отчет бизнес-аудита

**Дата генерации:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Статус:** Ошибка генерации отчета

## ❌ Ошибка
При генерации отчета произошла ошибка: {str(e)}

Пожалуйста, проверьте данные и повторите анализ.
"""

    def save_report(self, analysis_results: Dict, filename: str = None):
        """Сохранение отчета в файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/business_audit_{timestamp}.md"

        # Создаем директорию если её нет
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        report_content = self.generate_markdown_report(analysis_results)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return filename

    def export_to_json(self, analysis_results: Dict, filename: str = None):
        """Экспорт результатов в JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/business_audit_{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)

        return filename