import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()


class AmoCRMCollector:
    """Коллектор данных из AmoCRM с улучшенным демо-режимом"""

    def __init__(self):
        self.subdomain = os.getenv('AMOCRM_SUBDOMAIN')
        self.client_id = os.getenv('AMOCRM_CLIENT_ID')
        self.client_secret = os.getenv('AMOCRM_CLIENT_SECRET')
        self.redirect_uri = os.getenv('AMOCRM_REDIRECT_URI')
        self.access_token = os.getenv('AMOCRM_ACCESS_TOKEN')
        self.refresh_token = os.getenv('AMOCRM_REFRESH_TOKEN')

        # Базовая проверка настроек
        self.demo_mode = not (self.access_token and self.access_token != "your_amocrm_access_token_here")

        if not self.demo_mode:
            self.base_url = f'https://{self.subdomain}.amocrm.ru'
            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

    def check_connection(self):
        """Проверка подключения к AmoCRM"""
        if self.demo_mode:
            return False

        try:
            url = f'{self.base_url}/api/v4/account'
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    def get_account_info(self):
        """Получение информации об аккаунте"""
        if self.demo_mode:
            return self._get_demo_account_info()

        try:
            url = f'{self.base_url}/api/v4/account'
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Ошибка получения информации об аккаунте: {e}")
            return None

    def get_leads(self, limit=50):
        """Получение списка сделок"""
        if self.demo_mode:
            return self.get_demo_data('leads')

        try:
            url = f'{self.base_url}/api/v4/leads'
            params = {
                'limit': limit,
                'with': 'contacts'
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения сделок: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка при получении сделок: {e}")
            return None

    def get_contacts(self, limit=50):
        """Получение списка контактов"""
        if self.demo_mode:
            return self.get_demo_data('contacts')

        try:
            url = f'{self.base_url}/api/v4/contacts'
            params = {'limit': limit}

            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения контактов: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка при получении контактов: {e}")
            return None

    def get_companies(self, limit=50):
        """Получение списка компаний"""
        if self.demo_mode:
            return self.get_demo_data('companies')

        try:
            url = f'{self.base_url}/api/v4/companies'
            params = {'limit': limit}

            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения компаний: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка при получении компаний: {e}")
            return None

    def get_demo_data(self, data_type='leads'):
        """Генерация реалистичных демо-данных"""

        if data_type == 'account':
            return self._get_demo_account_info()

        elif data_type == 'leads':
            return self._get_demo_leads()

        elif data_type == 'contacts':
            return self._get_demo_contacts()

        elif data_type == 'companies':
            return self._get_demo_companies()

        else:
            return {"error": "Неизвестный тип данных"}

    def _get_demo_account_info(self):
        """Демо информация об аккаунте"""
        return {
            "id": 12345,
            "name": "Демо Компания ООО",
            "subdomain": "demo",
            "created_at": "2023-01-01T00:00:00+03:00",
            "current_user_id": 1,
            "country": "RU",
            "currency": "RUB",
            "timezone": "Europe/Moscow",
            "language": "ru"
        }

    def _get_demo_leads(self):
        """Генерация демо сделок"""
        leads = []

        # Статусы сделок
        statuses = [
            {"id": 142, "name": "Первичный контакт", "color": "#FFCC00"},
            {"id": 143, "name": "Переговоры", "color": "#FF9900"},
            {"id": 144, "name": "Принимают решение", "color": "#FF6600"},
            {"id": 145, "name": "Согласование договора", "color": "#3366FF"},
            {"id": 146, "name": "Успешно реализовано", "color": "#00CC00"},
            {"id": 147, "name": "Закрыто и не реализовано", "color": "#999999"}
        ]

        # Названия сделок
        lead_names = [
            "Покупка оборудования",
            "Разработка сайта",
            "Консультационные услуги",
            "Обслуживание техники",
            "Поставка материалов",
            "Обучение персонала",
            "Маркетинговая кампания",
            "SEO продвижение",
            "Настройка CRM",
            "Бухгалтерские услуги"
        ]

        # Генерация 20 демо сделок
        for i in range(1, 21):
            status = random.choice(statuses)
            created_date = datetime.now() - timedelta(days=random.randint(1, 90))
            price = random.randint(50000, 500000)

            lead = {
                "id": i,
                "name": f"{random.choice(lead_names)} #{i}",
                "price": price,
                "status_id": status["id"],
                "pipeline_id": 123,
                "created_by": 1,
                "updated_by": 1,
                "created_at": int(created_date.timestamp()),
                "updated_at": int((created_date + timedelta(days=random.randint(1, 10))).timestamp()),
                "account_id": 12345,
                "_embedded": {
                    "contacts": [
                        {
                            "id": i,
                            "is_main": True
                        }
                    ],
                    "status": status
                }
            }
            leads.append(lead)

        return {
            "_page": 1,
            "_links": {
                "self": {"href": "/api/v4/leads?page=1&limit=20"},
                "next": {"href": "/api/v4/leads?page=2&limit=20"}
            },
            "_embedded": {
                "leads": leads
            }
        }

    def _get_demo_contacts(self):
        """Генерация демо контактов"""
        contacts = []

        # Имена и фамилии
        first_names = ["Александр", "Иван", "Мария", "Екатерина", "Дмитрий", "Ольга", "Сергей", "Анна", "Алексей",
                       "Наталья"]
        last_names = ["Иванов", "Петров", "Сидоров", "Смирнова", "Кузнецова", "Попова", "Лебедева", "Новикова",
                      "Морозова", "Волкова"]

        # Должности
        positions = ["Директор", "Менеджер", "Бухгалтер", "Аналитик", "Разработчик", "Дизайнер", "Маркетолог",
                     "Продавец", "Консультант", "Специалист"]

        # Генерация 15 демо контактов
        for i in range(1, 16):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            contact = {
                "id": i,
                "name": f"{first_name} {last_name}",
                "first_name": first_name,
                "last_name": last_name,
                "responsible_user_id": 1,
                "created_by": 1,
                "updated_by": 1,
                "created_at": int((datetime.now() - timedelta(days=random.randint(30, 365))).timestamp()),
                "updated_at": int((datetime.now() - timedelta(days=random.randint(1, 29))).timestamp()),
                "account_id": 12345,
                "custom_fields_values": [
                    {
                        "field_id": 1,
                        "field_name": "Email",
                        "field_code": "EMAIL",
                        "field_type": "text",
                        "values": [
                            {
                                "value": f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                                "enum_id": 1,
                                "enum_code": "WORK"
                            }
                        ]
                    },
                    {
                        "field_id": 2,
                        "field_name": "Телефон",
                        "field_code": "PHONE",
                        "field_type": "text",
                        "values": [
                            {
                                "value": f"+7 999 000-{i:04d}",
                                "enum_id": 1,
                                "enum_code": "WORK"
                            }
                        ]
                    },
                    {
                        "field_id": 3,
                        "field_name": "Должность",
                        "field_code": "POSITION",
                        "field_type": "text",
                        "values": [
                            {
                                "value": random.choice(positions),
                                "enum_id": 1,
                                "enum_code": "WORK"
                            }
                        ]
                    }
                ]
            }
            contacts.append(contact)

        return {
            "_page": 1,
            "_links": {
                "self": {"href": "/api/v4/contacts?page=1&limit=15"},
                "next": {"href": "/api/v4/contacts?page=2&limit=15"}
            },
            "_embedded": {
                "contacts": contacts
            }
        }

    def _get_demo_companies(self):
        """Генерация демо компаний"""
        companies = []

        # Названия компаний
        company_names = [
            "ООО 'ТехноПрофи'",
            "ИП Сидоров А.В.",
            "АО 'СтройГарант'",
            "ООО 'МаркетИнтегратор'",
            "ЗАО 'ФинансКонсалт'",
            "ООО 'ИТРешения'",
            "ИП Петрова М.И.",
            "ООО 'ЛогистикаПлюс'",
            "АО 'ТехноИнновации'",
            "ООО 'БизнесКонсалтинг'"
        ]

        # Сферы деятельности
        industries = ["IT", "Строительство", "Розничная торговля", "Услуги", "Производство", "Логистика", "Маркетинг",
                      "Консалтинг", "Образование", "Здоровье"]

        # Генерация 10 демо компаний
        for i in range(1, 11):
            company = {
                "id": i,
                "name": random.choice(company_names),
                "responsible_user_id": 1,
                "created_by": 1,
                "updated_by": 1,
                "created_at": int((datetime.now() - timedelta(days=random.randint(180, 730))).timestamp()),
                "updated_at": int((datetime.now() - timedelta(days=random.randint(1, 179))).timestamp()),
                "account_id": 12345,
                "custom_fields_values": [
                    {
                        "field_id": 1,
                        "field_name": "Сфера деятельности",
                        "field_code": "INDUSTRY",
                        "field_type": "text",
                        "values": [
                            {
                                "value": random.choice(industries),
                                "enum_id": 1,
                                "enum_code": "WORK"
                            }
                        ]
                    },
                    {
                        "field_id": 2,
                        "field_name": "Количество сотрудников",
                        "field_code": "EMPLOYEES",
                        "field_type": "text",
                        "values": [
                            {
                                "value": str(random.randint(10, 500)),
                                "enum_id": 1,
                                "enum_code": "WORK"
                            }
                        ]
                    }
                ]
            }
            companies.append(company)

        return {
            "_page": 1,
            "_links": {
                "self": {"href": "/api/v4/companies?page=1&limit=10"},
                "next": {"href": "/api/v4/companies?page=2&limit=10"}
            },
            "_embedded": {
                "companies": companies
            }
        }

    def analyze_leads(self, leads_data):
        """Анализ данных о сделках"""
        if not leads_data or '_embedded' not in leads_data:
            return {"error": "Нет данных для анализа"}

        leads = leads_data['_embedded']['leads']

        if not leads:
            return {"error": "Список сделок пуст"}

        # Преобразуем в DataFrame для анализа
        df_data = []
        for lead in leads:
            df_data.append({
                'id': lead.get('id'),
                'name': lead.get('name', ''),
                'price': lead.get('price', 0),
                'status_id': lead.get('status_id'),
                'created_at': lead.get('created_at'),
                'updated_at': lead.get('updated_at')
            })

        df = pd.DataFrame(df_data)

        # Анализ
        analysis = {
            'total_leads': len(df),
            'total_amount': df['price'].sum(),
            'avg_deal_size': df['price'].mean(),
            'max_deal': df['price'].max(),
            'min_deal': df['price'].min(),
            'status_distribution': df['status_id'].value_counts().to_dict()
        }

        # Если есть даты создания
        if 'created_at' in df.columns and df['created_at'].notna().any():
            try:
                df['created_date'] = pd.to_datetime(df['created_at'], unit='s')
                analysis['leads_last_30_days'] = len(
                    df[df['created_date'] > pd.Timestamp.now() - pd.Timedelta(days=30)])
                analysis['leads_last_7_days'] = len(df[df['created_date'] > pd.Timestamp.now() - pd.Timedelta(days=7)])
            except:
                pass

        return analysis