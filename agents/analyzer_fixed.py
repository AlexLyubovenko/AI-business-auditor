"""
ИСПРАВЛЕННЫЙ анализатор данных для AI Business Auditor
Полностью переписан для работы с OpenAI v1.6.1
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
import json

# Импортируем OpenAI с ПАТЧЕМ
import openai
from openai import OpenAI as OriginalOpenAI


# СОЗДАЕМ ПАТЧИРОВАННЫЙ КЛАСС OpenАI
class PatchedOpenAI(OriginalOpenAI):
    def __init__(self, api_key=None, **kwargs):
        # УДАЛЯЕМ ВСЕ проблемные параметры
        safe_kwargs = {k: v for k, v in kwargs.items()
                       if k not in ['proxies', 'api_base', 'organization',
                                    'timeout', 'max_retries', 'http_client']}
        super().__init__(api_key=api_key, **safe_kwargs)


# Заменяем оригинальный класс
openai.OpenAI = PatchedOpenAI

# Теперь импортируем исправленный OpenAI
from openai import OpenAI


class DataAnalyzer:
    """Анализатор данных с использованием LLM"""

    def __init__(self, api_key: Optional[str] = None):
        """Инициализация анализатора с исправлением проблемы proxies"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        print(f"🔧 Инициализация DataAnalyzer (ИСПРАВЛЕННАЯ). API ключ: {'указан' if self.api_key else 'не указан'}")

        if self.api_key and self.api_key.startswith("sk-"):
            try:
                # Способ 1: БЕЗ параметров вообще
                self.client = OpenAI(api_key=self.api_key)
                print("✅ OpenAI клиент инициализирован (способ 1)")

            except Exception as e1:
                print(f"⚠️ Способ 1 не сработал: {e1}")

                try:
                    # Способ 2: Устанавливаем ключ в окружение и создаем без параметров
                    os.environ["OPENAI_API_KEY"] = self.api_key
                    self.client = OpenAI()  # Без параметров
                    print("✅ OpenAI клиент инициализирован (способ 2)")

                except Exception as e2:
                    print(f"❌ Способ 2 также провалился: {e2}")

                    try:
                        # Способ 3: Ультра-минималистичный
                        self.client = OpenAI(
                            api_key=self.api_key,
                            # ТОЛЬКО обязательные параметры, никаких proxies!
                        )
                        print("✅ OpenAI клиент инициализирован (способ 3)")
                    except Exception as e3:
                        print(f"❌ Все способы провалились: {e3}")
                        self.client = None
        else:
            if self.api_key:
                print(f"⚠️ Неверный формат API ключа: {self.api_key[:10]}...")
            else:
                print("ℹ️ OpenAI клиент не инициализирован (нет ключа)")

    # ОСТАЛЬНЫЕ МЕТОДЫ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ (из предыдущей версии)
    def analyze_dataframe(self, df: pd.DataFrame, analysis_type: str = "Финансовый") -> Dict[str, Any]:
        """Анализ DataFrame с вычислением метрик"""
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "basic_stats": {},
                "financial_metrics": {},
                "trends": {},
                "anomalies": [],
                "summary": ""
            }

            # Базовая статистика
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            text_cols = df.select_dtypes(include=['object']).columns.tolist()

            if numeric_cols:
                # Описательная статистика для числовых колонок
                desc_stats = df[numeric_cols].describe().to_dict()

                simplified_stats = {}
                for col in numeric_cols[:10]:
                    if col in desc_stats:
                        simplified_stats[col] = {
                            "mean": float(desc_stats[col].get('mean', 0)),
                            "std": float(desc_stats[col].get('std', 0)),
                            "min": float(desc_stats[col].get('min', 0)),
                            "max": float(desc_stats[col].get('max', 0)),
                            "median": float(df[col].median() if not df[col].empty else 0)
                        }

                analysis["basic_stats"] = {
                    "numeric_summary": simplified_stats,
                    "total_numeric_columns": len(numeric_cols)
                }

                analysis["financial_metrics"] = self._calculate_financial_metrics(df)
                analysis["trends"] = self._detect_trends(df)
                analysis["anomalies"] = self._detect_anomalies(df)

            if text_cols:
                analysis["basic_stats"]["text_summary"] = {
                    "text_columns": text_cols,
                    "sample_values": {col: df[col].dropna().iloc[:3].tolist() if len(df[col].dropna()) > 0 else []
                                      for col in text_cols[:3]}
                }

            analysis["summary"] = self._generate_summary(analysis, len(df))
            return analysis

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "error": str(e),
                "summary": f"Ошибка анализа: {str(e)}"
            }

    def _calculate_financial_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Вычисление финансовых метрик"""
        metrics = {}

        revenue_keywords = ['выручка', 'revenue', 'доход', 'sales', 'income']
        cost_keywords = ['расход', 'cost', 'expense', 'затрат', 'издерж']
        profit_keywords = ['прибыль', 'profit', 'марж', 'margin']

        revenue_cols = []
        cost_cols = []
        profit_cols = []

        for col in df.columns:
            col_lower = str(col).lower()

            if any(keyword in col_lower for keyword in revenue_keywords):
                revenue_cols.append(col)
            elif any(keyword in col_lower for keyword in cost_keywords):
                cost_cols.append(col)
            elif any(keyword in col_lower for keyword in profit_keywords):
                profit_cols.append(col)

        if revenue_cols:
            revenue_col = revenue_cols[0]
            total_revenue = df[revenue_col].sum()
            avg_revenue = df[revenue_col].mean()

            metrics["total_revenue"] = float(total_revenue)
            metrics["avg_revenue"] = float(avg_revenue)

            if len(df) > 1:
                try:
                    growth = ((df[revenue_col].iloc[-1] - df[revenue_col].iloc[0]) /
                              df[revenue_col].iloc[0] * 100)
                    metrics["revenue_growth_percent"] = float(growth)
                except:
                    metrics["revenue_growth_percent"] = None

        if cost_cols and revenue_cols:
            cost_col = cost_cols[0]
            revenue_col = revenue_cols[0]

            total_cost = df[cost_col].sum()
            total_revenue = df[revenue_col].sum()

            metrics["total_cost"] = float(total_cost)
            metrics["gross_profit"] = float(total_revenue - total_cost)

            if total_revenue > 0:
                metrics["gross_margin_percent"] = float(
                    (total_revenue - total_cost) / total_revenue * 100
                )

        if profit_cols:
            profit_col = profit_cols[0]
            metrics["total_profit"] = float(df[profit_col].sum())
            metrics["avg_profit"] = float(df[profit_col].mean())

        return metrics

    def _detect_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Обнаружение трендов в данных"""
        trends = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in numeric_cols[:5]:
            if len(df[col]) > 2:
                try:
                    y_series = df[col].ffill()
                    y = y_series.values

                    if len(y) > 1 and not np.all(y == y[0]):
                        x = np.arange(len(y))
                        slope = np.polyfit(x, y, 1)[0]

                        if slope > 0.1:
                            trend_direction = "рост"
                        elif slope < -0.1:
                            trend_direction = "снижение"
                        else:
                            trend_direction = "стабильность"

                        trends[col] = {
                            "direction": trend_direction,
                            "slope": float(slope),
                            "strength": "сильный" if abs(slope) > 0.5 else "умеренный" if abs(slope) > 0.1 else "слабый"
                        }
                except Exception as e:
                    print(f"⚠️ Ошибка при анализе трендов для колонки {col}: {e}")
                    continue

        return trends

    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Обнаружение аномалий в данных"""
        anomalies = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in numeric_cols[:5]:
            if len(df[col]) > 10:
                try:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1

                    if IQR > 0:
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR

                        anomaly_indices = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index

                        for idx in anomaly_indices[:10]:
                            anomalies.append({
                                "column": col,
                                "row_index": int(idx) if pd.notnull(idx) else str(idx),
                                "value": float(df.loc[idx, col]),
                                "bounds": {
                                    "lower": float(lower_bound),
                                    "upper": float(upper_bound)
                                },
                                "deviation": "ниже" if df.loc[idx, col] < lower_bound else "выше"
                            })
                except Exception as e:
                    print(f"⚠️ Ошибка при обнаружении аномалий для колонки {col}: {e}")
                    continue

        return anomalies[:20]

    def _generate_summary(self, analysis: Dict, row_count: int) -> str:
        """Генерация текстового резюме анализа"""
        summary_parts = []

        summary_parts.append(f"Анализ типа: {analysis.get('analysis_type', 'Неизвестно')}")
        summary_parts.append(f"Проанализировано строк: {row_count}")

        metrics = analysis.get("financial_metrics", {})
        if metrics:
            if "total_revenue" in metrics:
                summary_parts.append(f"Общая выручка: {metrics['total_revenue']:,.0f}")
            if "gross_profit" in metrics:
                summary_parts.append(f"Валовая прибыль: {metrics['gross_profit']:,.0f}")
            if "gross_margin_percent" in metrics:
                summary_parts.append(f"Валовая маржа: {metrics['gross_margin_percent']:.1f}%")

        trends = analysis.get("trends", {})
        if trends:
            trend_count = len([t for t in trends.values() if t.get("direction") == "рост"])
            if trend_count > 0:
                summary_parts.append(f"Выявлено {trend_count} растущих трендов")

        anomalies = analysis.get("anomalies", [])
        if anomalies:
            summary_parts.append(f"Обнаружено {len(anomalies)} аномалий в данных")

        return " | ".join(summary_parts)

    def generate_llm_insights(self, analysis_results: Dict, prompt_template: str = None) -> Dict[str, Any]:
        """Генерация инсайтов с помощью LLM"""
        if not self.client:
            print("❌ OpenAI клиент не инициализирован")
            return {
                "llm_analysis": {
                    "insights": ["⚠️ API ключ OpenAI не настроен или неверен"],
                    "recommendations": ["✅ Проверьте ключ в настройках"],
                    "risks": []
                },
                "llm_used": False,
                "error": "API ключ не настроен"
            }

        try:
            print("🤖 Запускаю GPT-анализ...")

            context = {
                "analysis_type": analysis_results.get("analysis_type", "Неизвестно"),
                "financial_metrics": analysis_results.get("financial_metrics", {}),
                "trends": analysis_results.get("trends", {}),
                "anomalies_count": len(analysis_results.get("anomalies", [])),
                "summary": analysis_results.get("summary", "")
            }

            prompt = prompt_template or f"""
            Ты — опытный бизнес-аналитик. Проанализируй данные:

            Тип анализа: {context['analysis_type']}
            Количество аномалий: {context['anomalies_count']}

            Основные метрики:
            {json.dumps(context['financial_metrics'], ensure_ascii=False, indent=2)}

            Тренды:
            {json.dumps(context['trends'], ensure_ascii=False, indent=2)}

            Предоставь на русском языке:
            1. 3 ключевых вывода
            2. 2 практические рекомендации
            3. 2 потенциальных риска

            Формат ответа JSON:
            {{
                "insights": ["вывод1", "вывод2", "вывод3"],
                "recommendations": ["рекомендация1", "рекомендация2"],
                "risks": ["риск1", "риск2"]
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты опытный бизнес-аналитик. Отвечай на русском языке."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            llm_response = response.choices[0].message.content
            print(f"✅ Получен ответ от OpenAI")

            try:
                llm_data = json.loads(llm_response)

                insights = []
                for insight in llm_data.get("insights", []):
                    if isinstance(insight, str) and insight.strip():
                        insights.append(insight.strip())

                recommendations = []
                for rec in llm_data.get("recommendations", []):
                    if isinstance(rec, str) and rec.strip():
                        recommendations.append(rec.strip())

                risks = []
                for risk in llm_data.get("risks", []):
                    if isinstance(risk, str) and risk.strip():
                        risks.append(risk.strip())

                return {
                    "llm_analysis": {
                        "insights": insights[:3],
                        "recommendations": recommendations[:2],
                        "risks": risks[:2]
                    },
                    "model_used": "gpt-3.5-turbo",
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                    "llm_used": True
                }

            except json.JSONDecodeError:
                return {
                    "llm_analysis": {
                        "insights": [llm_response[:200] + "..."],
                        "recommendations": ["Ответ не в JSON формате"],
                        "risks": ["Проблема с форматом ответа"]
                    },
                    "llm_used": False,
                    "error": "Ответ не в JSON формате"
                }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка OpenAI: {error_msg}")

            return {
                "llm_analysis": {
                    "insights": [f"Ошибка: {error_msg[:100]}"],
                    "recommendations": ["Проверьте API ключ", "Повторите попытку"],
                    "risks": ["Проблема с AI-анализом"]
                },
                "llm_used": False,
                "error": error_msg
            }