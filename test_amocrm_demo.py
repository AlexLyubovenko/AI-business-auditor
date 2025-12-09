import sys
import os
sys.path.append('.')

# Включаем демо-режим
os.environ["AMOCRM_DEMO_MODE"] = "true"

from agents.amocrm_collector import create_amocrm_collector

# Создаем демо-коллектор
collector = create_amocrm_collector()

print("🧪 Тестирование демо-режима AmoCRM")
print("=" * 50)

# Проверяем аутентификацию
print(f"✅ Аутентифицирован: {collector.is_authenticated()}")

# Получаем сделки
print("\n📊 Получаем сделки за 30 дней...")
deals = collector.collect_deals(days=30)
print(f"✅ Найдено сделок: {deals['total_deals']}")
print(f"✅ Демо-режим: {deals.get('demo_mode', False)}")

# Анализируем воронку
print("\n📈 Анализируем воронку продаж...")
funnel = collector.analyze_sales_funnel(days=30)
summary = funnel['analysis']['summary']
print(f"✅ Всего сделок: {summary['total_deals']}")
print(f"✅ Конверсия: {summary['conversion_rate']}%")
print(f"✅ Общая сумма: {summary['total_value']:,.0f} руб")

# Анализируем менеджеров
print("\n👥 Анализируем менеджеров...")
managers = collector.analyze_manager_performance(days=30)
print(f"✅ Найдено менеджеров: {managers['total_managers']}")

print("\n🎉 Демо-режим работает отлично!")