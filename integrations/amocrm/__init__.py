# integrations/amocrm/__init__.py

# Экспортируем основной клиент
from .client import AmoCRMClient

# Экспортируем модели
from .models import Deal, Contact, Pipeline

# Экспортируем демо-клиент
try:
    from .demo_client import DemoAmoCRMClient
except ImportError:
    # Если демо-клиента нет, создаем простую заглушку
    class DemoAmoCRMClient:
        def __init__(self, subdomain="demo", access_token="demo_token"):
            self.subdomain = subdomain
            self.access_token = access_token
            self.is_demo = True

        def get_leads(self, limit=10, **kwargs):
            return [
                {'id': 1, 'name': 'Демо сделка 1', 'price': 100000, 'status': 'active'},
                {'id': 2, 'name': 'Демо сделка 2', 'price': 150000, 'status': 'won'},
            ]

        def get_contacts(self, limit=5, **kwargs):
            return [
                {'id': 1, 'name': 'Демо контакт 1', 'email': 'demo1@test.ru'},
                {'id': 2, 'name': 'Демо контакт 2', 'email': 'demo2@test.ru'},
            ]

__all__ = [
    'AmoCRMClient',
    'DemoAmoCRMClient',  # Важно: добавляем в список экспорта
    'Deal',
    'Contact',
    'Pipeline'
]