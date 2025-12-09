# openai_patch.py
import openai
from openai import OpenAI as OriginalOpenAI

class PatchedOpenAI(OriginalOpenAI):
    def __init__(self, *args, **kwargs):
        # Удаляем параметр proxies если он есть
        kwargs.pop('proxies', None)
        kwargs.pop('api_base', None)
        kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

# Заменяем оригинальный класс
openai.OpenAI = PatchedOpenAI