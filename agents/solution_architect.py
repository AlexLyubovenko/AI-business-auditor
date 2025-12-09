# agents/solution_architect.py
import os
import json
import openai
from typing import Dict, Any, List

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
openai.api_key = os.getenv("OPENAI_API_KEY")

class SolutionArchitect:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def generate_solutions(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        По результатам analysis генерируем список решений.
        Каждый элемент: {title, description, steps, automations}
        """
        prompt = self._build_prompt(analysis)
        resp = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Ты — AI-консультант по автоматизации бизнес-процессов."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        text = resp['choices'][0]['message']['content']
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = {"raw_response": text}
        return parsed

    def _build_prompt(self, analysis: Dict[str, Any]) -> str:
        return (
            "На входе — JSON анализа бизнес-процессов (problems, insights, metrics).\n"
            "Сгенерируй список практических решений по автоматизации и оптимизации.\n"
            "Для каждого решения выдай:\n"
            "- title\n"
            "- description\n"
            "- steps: массив конкретных шагов (3-7)\n"
            "- automations: что можно автоматизировать (Make/Zapier/Albato шаблоны)\n\n"
            "INPUT:\n" + json.dumps(analysis, ensure_ascii=False, indent=2) + "\n\n"
            "Ответь строго в JSON формате: {\"solutions\": [ ... ]}"
        )
