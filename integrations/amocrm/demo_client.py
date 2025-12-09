# integrations/amocrm/demo_client.py
from .client import AmoCRMClient
from .auth import AmoCRMAuth
from datetime import datetime, timedelta
import random


class DemoAmoCRMClient:
    """Демо-версия клиента AmoCRM, которая работает без реального API"""

    def __init__(self, subdomain="demo", access_token="demo_token"):
        self.subdomain = subdomain
        self.access_token = access_token
        self.is_demo = True
        print("✅ DemoAmoCRMClient инициализирован (демо-режим)")

    def get_leads(self, limit=50):
        """Получение демо-сделок"""
        leads = []
        statuses = ['Новая', 'В работе', 'Успешная', 'Закрыта', 'Отказ']
        status_weights = {
            'Новая': 30,
            'В работе': 40,
            'Успешная': 20,
            'Закрыта': 5,
            'Отказ': 5
        }

        # Взвешенный выбор статусов
        weighted_statuses = []
        for status, weight in status_weights.items():
            weighted_statuses.extend([status] * weight)

        for i in range(1, limit + 1):
            price = random.randint(10000, 500000)
            days_ago = random.randint(0, 90)
            created_date = datetime.now() - timedelta(days=days_ago)

            lead = {
                'id': i,
                'name': f'Демо сделка #{i}',
                'price': price,
                'status': random.choice(weighted_statuses),
                'created_at': created_date.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': (created_date + timedelta(days=random.randint(0, days_ago))).strftime(
                    '%Y-%m-%d %H:%M:%S'),
                'responsible_user_id': random.randint(1, 5),
                'pipeline_id': random.randint(1, 3),
                'pipeline_name': f'Воронка {random.randint(1, 3)}',
                'stage_id': random.randint(1, 7),
                'stage_name': f'Этап {random.randint(1, 7)}',
                'tags': ['VIP'] if price > 300000 else ['Новый'] if i % 5 == 0 else [],
                'company': f'Компания {random.randint(1, 20)}',
                'contact': f'Контакт {random.randint(1, 50)}'
            }

            # Если сделка завершена, добавляем дату закрытия
            if lead['status'] in ['Успешная', 'Закрыта', 'Отказ']:
                closed_days = random.randint(1, min(days_ago, 30))
                lead['closed_at'] = (created_date + timedelta(days=closed_days)).strftime('%Y-%m-%d %H:%M:%S')
                lead['days_to_close'] = closed_days

            leads.append(lead)

        # Сортируем по дате создания (новые первые)
        leads.sort(key=lambda x: x['created_at'], reverse=True)
        return leads[:limit]

    def get_contacts(self, limit=30):
        """Получение демо-контактов"""
        contacts = []
        first_names = ['Иван', 'Алексей', 'Мария', 'Екатерина', 'Дмитрий', 'Ольга', 'Сергей', 'Анна', 'Павел',
                       'Наталья']
        last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецов', 'Смирнов', 'Попов', 'Васильев', 'Михайлов', 'Федоров']
        positions = ['Директор', 'Менеджер', 'Бухгалтер', 'Маркетолог', 'Разработчик', 'Аналитик', 'Консультант']

        for i in range(1, limit + 1):
            contact = {
                'id': i,
                'name': f'{random.choice(first_names)} {random.choice(last_names)}',
                'first_name': random.choice(first_names),
                'last_name': random.choice(last_names),
                'position': random.choice(positions),
                'company': f'ООО "{"".join(random.choices("АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ", k=6))}"',
                'email': f'client{i}@example.com',
                'phone': f'+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}',
                'created_at': (datetime.now() - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
                'leads_count': random.randint(1, 10),
                'total_leads_value': random.randint(50000, 500000),
                'last_activity': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
            }
            contacts.append(contact)

        return contacts

    def get_deals(self, *args, **kwargs):
        """Алиас для get_leads для совместимости"""
        return self.get_leads(*args, **kwargs)

    def get_account_info(self):
        """Информация об аккаунте"""
        return {
            'id': 12345,
            'name': 'Демо компания AI Business Auditor',
            'subdomain': self.subdomain,
            'created_at': '2024-01-01',
            'plan': 'Профессиональный',
            'users_count': 8,
            'leads_count': 127,
            'contacts_count': 89,
            'companies_count': 45,
            'is_demo': True,
            'monthly_revenue': 1250000,
            'conversion_rate': 23.4
        }

    def get_lead_stats(self):
        """Статистика по сделкам"""
        leads = self.get_leads(100)

        total_value = sum(lead['price'] for lead in leads)
        won_leads = [l for l in leads if l['status'] in ['Успешная', 'Закрыта']]
        lost_leads = [l for l in leads if l['status'] == 'Отказ']
        in_progress = [l for l in leads if l['status'] == 'В работе']
        new_leads = [l for l in leads if l['status'] == 'Новая']

        avg_deal_size = total_value / len(leads) if leads else 0
        conversion_rate = (len(won_leads) / len(leads) * 100) if leads else 0

        # Среднее время закрытия
        closed_deals = [l for l in leads if 'days_to_close' in l]
        avg_close_time = sum(l['days_to_close'] for l in closed_deals) / len(closed_deals) if closed_deals else 0

        return {
            'total_leads': len(leads),
            'won_leads': len(won_leads),
            'lost_leads': len(lost_leads),
            'in_progress': len(in_progress),
            'new_leads': len(new_leads),
            'total_value': total_value,
            'avg_deal_size': avg_deal_size,
            'conversion_rate': conversion_rate,
            'avg_close_time': avg_close_time,
            'revenue_by_month': self._generate_revenue_by_month(),
            'top_managers': self._generate_top_managers()
        }

    def _generate_revenue_by_month(self):
        """Генерация данных о выручке по месяцам"""
        months = []
        current = datetime.now()

        for i in range(6, -1, -1):  # Последние 6 месяцев
            month_date = current - timedelta(days=30 * i)
            month_name = month_date.strftime('%b %Y')
            revenue = random.randint(500000, 1500000) * (1 + i * 0.1)  # Рост
            months.append({
                'month': month_name,
                'revenue': revenue,
                'leads': random.randint(15, 40),
                'conversion': random.randint(20, 35)
            })

        return months

    def _generate_top_managers(self):
        """Генерация данных о топ-менеджерах"""
        managers = [
            {'id': 1, 'name': 'Иванов Иван', 'leads': 24, 'value': 1250000, 'conversion': 32.5},
            {'id': 2, 'name': 'Петрова Мария', 'leads': 18, 'value': 980000, 'conversion': 28.7},
            {'id': 3, 'name': 'Сидоров Алексей', 'leads': 15, 'value': 875000, 'conversion': 25.4},
            {'id': 4, 'name': 'Кузнецова Анна', 'leads': 12, 'value': 650000, 'conversion': 22.1},
            {'id': 5, 'name': 'Васильев Дмитрий', 'leads': 8, 'value': 420000, 'conversion': 18.9},
        ]
        return managers

    def get_pipelines(self):
        """Получение воронок"""
        return [
            {'id': 1, 'name': 'Основная воронка продаж', 'stages': 5, 'active': True},
            {'id': 2, 'name': 'Воронка партнеров', 'stages': 4, 'active': True},
            {'id': 3, 'name': 'Воронка повторных продаж', 'stages': 3, 'active': False},
        ]

    def analyze_sales_funnel(self, days=30):
        """Анализ воронки продаж"""
        leads = self.get_leads(200)

        # Группируем по статусам
        stages = {}
        for lead in leads:
            status = lead['status']
            if status not in stages:
                stages[status] = {'count': 0, 'value': 0, 'leads': []}
            stages[status]['count'] += 1
            stages[status]['value'] += lead['price']
            stages[status]['leads'].append(lead['id'])

        # Расчет метрик
        total_leads = len(leads)
        won_leads = sum(1 for l in leads if l['status'] in ['Успешная', 'Закрыта'])
        conversion = (won_leads / total_leads * 100) if total_leads > 0 else 0

        return {
            'period_days': days,
            'total_leads': total_leads,
            'won_leads': won_leads,
            'conversion_rate': conversion,
            'total_value': sum(l['price'] for l in leads),
            'stages': stages,
            'avg_deal_size': sum(l['price'] for l in leads) / total_leads if total_leads > 0 else 0,
            'recommendations': [
                'Увеличить конверсию на этапе "Новая" → "В работе"',
                'Сократить время обработки новых заявок',
                'Внедрить скрипты продаж для этапа "В работе"'
            ]
        }