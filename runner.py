# runner.py
"""
Запускает все сервисы AI Business Auditor в одном контейнере:
1. Streamlit веб-интерфейс (порт 8501)
2. Telegram бот (фоновый процесс)
3. Health-check сервер (порт 8080)
"""

import subprocess
import time
import threading
import sys
import os
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# ДОБАВЛЯЕМ ЭТО для корректных импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """Обработчик health-check запросов"""

    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            logger.info("Health check passed")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.info(f"HTTP {format % args}")


def run_health_server():
    """Запуск health-check сервера на порту 8080"""
    logger.info("🏥 Запуск health-check сервера на порту 8080...")
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)

    def run_server():
        try:
            server.serve_forever()
        except Exception as e:
            logger.error(f"Health server error: {e}")

    health_thread = threading.Thread(target=run_server, daemon=True)
    health_thread.start()

    # Даем время на запуск
    time.sleep(2)

    # Проверяем, что сервер запустился
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        if result == 0:
            logger.info("✅ Health-check сервер запущен")
            return server
        else:
            logger.error("❌ Health-check сервер не запустился")
            return None
    except Exception as e:
        logger.error(f"❌ Ошибка проверки health сервера: {e}")
        return None


def run_streamlit():
    """Запуск Streamlit веб-интерфейса"""
    logger.info("🌐 Запуск Streamlit веб-интерфейса на порту 8501...")

    # Создаем переменные окружения для Streamlit
    env = os.environ.copy()
    env['STREAMLIT_SERVER_PORT'] = '8501'
    env['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

    cmd = [
        "streamlit", "run", "ui/streamlit_app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.serverAddress=0.0.0.0",
        "--browser.serverPort=8501",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Чтение логов в реальном времени
        def log_stream(stream, stream_type):
            for line in stream:
                if line:
                    logger.info(f"Streamlit [{stream_type}]: {line.strip()}")

        threading.Thread(target=log_stream, args=(process.stdout, "STDOUT"), daemon=True).start()
        threading.Thread(target=log_stream, args=(process.stderr, "STDERR"), daemon=True).start()

        # Даем время на запуск
        time.sleep(5)

        # Проверяем, что процесс жив
        if process.poll() is None:
            logger.info("✅ Streamlit успешно запущен")
            return process
        else:
            logger.error("❌ Streamlit завершился при запуске")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка запуска Streamlit: {e}")
        return None


def run_telegram_bot():
    """Запуск Telegram бота"""
    logger.info("🤖 Запуск Telegram бота...")

    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN не установлен, бот не будет запущен")
        return None

    cmd = [sys.executable, "integrations/telegram/gpt_bot.py"]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
        cwd="/app"  # Важно: рабочая директория должна быть корнем
    )

    # ... остальной код функции
import sys
import os
import asyncio
import logging

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Теперь импорты должны работать
        from integrations.telegram.gpt_bot import main as bot_main
        await bot_main()
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error(f"Python path: {sys.path}")
        logger.error(f"Current dir: {os.getcwd()}")
        logger.error(f"Files in integrations/: {os.listdir('integrations') if os.path.exists('integrations') else 'No integrations dir'}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")
        raise

if __name__ == "__main__":
    # Создаем event loop для этого потока
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        loop.close()
"""]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd="/app"  # Указываем рабочую директорию
        )

        def log_stream(stream, stream_type):
            for line in stream:
                if line and line.strip():
                    logger.info(f"Telegram Bot [{stream_type}]: {line.strip()}")

        threading.Thread(target=log_stream, args=(process.stdout, "STDOUT"), daemon=True).start()
        threading.Thread(target=log_stream, args=(process.stderr, "STDERR"), daemon=True).start()

        # Даем больше времени на запуск
        time.sleep(10)

        if process.poll() is None:
            logger.info("✅ Telegram бот успешно запущен")
            return process
        else:
            logger.error("❌ Telegram бот завершился при запуске")
            # Попробуем получить ошибку из stderr
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
        return None


def check_services(processes):
    """Проверка состояния всех сервисов"""
    all_ok = True
    for name, process in processes.items():
        if process is None:
            continue
        if hasattr(process, 'poll'):
            if process.poll() is not None:
                logger.error(f"❌ Сервис {name} завершился")
                all_ok = False
    return all_ok


def main():
    """Основная функция запуска"""
    print("\n" + "=" * 60)
    print("🚀 AI Business Auditor - Комбинированный запуск")
    print("=" * 60 + "\n")

    # Проверка обязательных переменных окружения
    logger.info("🔍 Проверка переменных окружения...")
    required_vars = ['OPENAI_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"❌ Отсутствуют обязательные переменные: {missing}")
        logger.info("💡 Добавьте их в настройках Render: Environment → Add Variable")
        sys.exit(1)

    logger.info("✅ Все обязательные переменные окружения установлены")

    # Словарь для хранения процессов
    processes = {}

    # Обработчик сигналов для graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n🛑 Получен сигнал завершения...")
        for name, process in processes.items():
            if process:
                logger.info(f"Остановка {name}...")
                if hasattr(process, 'terminate'):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except:
                        pass
                elif hasattr(process, 'shutdown'):
                    process.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. Запускаем health-check сервер
        health_server = run_health_server()
        processes['health_server'] = health_server

        # 2. Запускаем Streamlit
        streamlit_process = run_streamlit()
        processes['streamlit'] = streamlit_process

        # 3. Запускаем Telegram бота
        bot_process = run_telegram_bot()
        processes['telegram_bot'] = bot_process

        # Отчет о состоянии
        print("\n" + "=" * 60)
        print("📊 СТАТУС ЗАПУСКА:")
        print("=" * 60)

        status_messages = []

        # Health server
        if health_server:
            status_messages.append("✅ Health-check сервер: http://localhost:8080/healthz")
        else:
            status_messages.append("❌ Health-check сервер: не запущен")

        # Streamlit
        if streamlit_process:
            status_messages.append("✅ Веб-интерфейс: http://localhost:8501")
            # Добавляем публичный URL для Render
            public_url = os.getenv('RENDER_EXTERNAL_URL', 'https://ai-business-auditor.onrender.com')
            status_messages.append(f"🌐 Публичный URL: {public_url}")
        else:
            status_messages.append("⚠️ Веб-интерфейс: требуется проверка")

        # Telegram bot
        if bot_process:
            status_messages.append("✅ Telegram бот: запущен и работает")
        elif os.getenv('TELEGRAM_BOT_TOKEN'):
            status_messages.append("❌ Telegram бот: не запущен (проверьте логи)")
        else:
            status_messages.append("⚠️ Telegram бот: токен не установлен (опционально)")

        for message in status_messages:
            print(f"  {message}")

        print("\n🔧 Отладка:")
        print(f"  • OpenAI ключ: {'✅ установлен' if os.getenv('OPENAI_API_KEY') else '❌ отсутствует'}")
        print(
            f"  • Telegram токен: {'✅ установлен' if os.getenv('TELEGRAM_BOT_TOKEN') else '⚠️ не установлен (бот не запущен)'}")
        print(f"  • AmoCRM токен: {'✅ установлен' if os.getenv('AMOCRM_ACCESS_TOKEN') else '⚠️ не установлен'}")

        print("\n" + "=" * 60)
        print("🔄 Мониторинг запущен. Логи в реальном времени выше.")
        print("🛑 Нажмите Ctrl+C для остановки всех сервисов")
        print("=" * 60 + "\n")

        # Бесконечный цикл с проверкой состояния
        check_counter = 0
        while True:
            time.sleep(10)
            check_counter += 1

            if check_counter % 6 == 0:  # Каждую минуту
                if check_services(processes):
                    logger.info("✅ Все сервисы работают нормально")
                else:
                    logger.warning("⚠️ Некоторые сервисы могут иметь проблемы")

    except KeyboardInterrupt:
        logger.info("\n🛑 Остановка по запросу пользователя...")
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка: {e}")
    finally:
        # Остановка всех процессов
        logger.info("🛑 Завершение работы всех сервисов...")
        for name, process in processes.items():
            if process:
                logger.info(f"Останавливаю {name}...")
                try:
                    if hasattr(process, 'terminate'):
                        process.terminate()
                        process.wait(timeout=5)
                    elif hasattr(process, 'shutdown'):
                        process.shutdown()
                except Exception as e:
                    logger.error(f"Ошибка при остановке {name}: {e}")

        logger.info("✅ Все сервисы остановлены")
        print("\n👋 До свидания!\n")


if __name__ == "__main__":
    main()