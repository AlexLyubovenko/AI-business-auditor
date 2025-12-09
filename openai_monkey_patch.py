"""
МОЩНЫЙ ПАТЧ для OpenAI API
Удаляет все проблемные параметры из всех вызовов OpenAI
"""

import openai
from openai import OpenAI as OriginalOpenAI
import warnings

# Игнорируем все предупреждения
warnings.filterwarnings('ignore')

# Сохраняем оригинальный класс
_original_openai_init = OriginalOpenAI.__init__


# Создаем патчированную версию
def _patched_openai_init(self, *args, **kwargs):
    """Удаляем ВСЕ проблемные параметры"""

    # Список параметров, которые нужно удалить
    bad_params = [
        'proxies', 'api_base', 'organization',
        'timeout', 'max_retries', 'http_client',
        'base_url', 'default_headers', 'default_query',
        '_strict_response_validation'
    ]

    # Удаляем проблемные параметры
    cleaned_kwargs = {}
    for key, value in kwargs.items():
        if key not in bad_params:
            cleaned_kwargs[key] = value
        else:
            print(f"⚠️ Удален проблемный параметр: {key}")

    # Вызываем оригинальный init с очищенными параметрами
    try:
        return _original_openai_init(self, *args, **cleaned_kwargs)
    except TypeError as e:
        # Если все еще ошибка, пробуем только с api_key
        if 'api_key' in cleaned_kwargs:
            try:
                print("🔄 Пробую только с api_key...")
                return _original_openai_init(self, api_key=cleaned_kwargs['api_key'])
            except:
                print("❌ Не удалось создать клиент даже с одним параметром")
                raise e


# Применяем патч
OriginalOpenAI.__init__ = _patched_openai_init

# Также патчим openai.OpenAI для совместимости
openai.OpenAI = OriginalOpenAI

print("✅ Применен МОЩНЫЙ патч для OpenAI - все проблемные параметры удалены")