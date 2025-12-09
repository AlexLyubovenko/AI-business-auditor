# integrations/telegram/test_imports.py
import os
import sys

print("🔍 Тестирование импортов...")

# Добавляем корневую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")

try:
    print("1. Импорт DataAnalyzer...")
    from agents.analyzer import DataAnalyzer

    print("   ✅ Успешно")

    print("2. Импорт ReportGenerator...")
    from agents.reporter import ReportGenerator

    print("   ✅ Успешно")

    print("3. Импорт DemoAmoCRMClient...")
    from integrations.amocrm.client import DemoAmoCRMClient

    print("   ✅ Успешно")

    print("4. Создание экземпляров...")
    analyzer = DataAnalyzer()
    reporter = ReportGenerator()
    amocrm = DemoAmoCRMClient()
    print("   ✅ Все экземпляры созданы")

    print("\n🎉 ВСЕ ИМПОРТЫ УСПЕШНЫ!")
    print("Бот готов к работе с полным функционалом.")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\n🔧 Решение проблемы:")
    print("1. Убедитесь, что вы в корневой директории проекта")
    print("2. Проверьте структуру папок")
    print("3. Запустите из папки AI-business-auditor:")
    print("   python integrations/telegram/test_imports.py")