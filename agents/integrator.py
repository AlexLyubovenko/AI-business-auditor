# agents/integrator.py
from typing import Dict, Any, List
import json

class Integrator:
    """
    Генерация шаблонов интеграций в формате, понятном для Make/Zapier.
    MVP: генерируем текстовые инструкции и JSON-описания задач.
    """

    def __init__(self):
        pass

    def create_make_template(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сформировать простой JSON-шаблон сценария для Make.
        """
        template = {
            "name": f"Automation - {solution.get('title', 'untitled')}",
            "description": solution.get("description", ""),
            "steps": []
        }
        # Простой перевод steps в блоки
        for s in solution.get("steps", [])[:6]:
            template["steps"].append({
                "action": s,
                "type": "webhook_or_api",
                "notes": "Заполнить реальные параметры (URL, ключи) при деплое"
            })
        return template

    def create_google_sheet_template(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Возвращает структуру листа и набор колонок для Google Sheets.
        """
        cols = ["metric", "value", "notes"]
        rows = [{"metric": k, "value": v, "notes": ""} for k, v in (metrics or {}).items()]
        return {"columns": cols, "rows": rows}
