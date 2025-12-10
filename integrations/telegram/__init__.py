# Telegram bot integration
import asyncio

def run_bot():
    """Запуск Telegram бота"""
    # Импортируем и запускаем основную функцию из gpt_bot.py
    try:
        from .gpt_bot import main
        return asyncio.run(main())
    except ImportError:
        try:
            from .gpt_bot import start_bot
            return asyncio.run(start_bot())
        except ImportError:
            try:
                from .gpt_bot import run
                return asyncio.run(run())
            except ImportError:
                # Если ничего не найдено, импортируем весь модуль
                from . import gpt_bot
                # Запускаем стандартную точку входа
                if hasattr(gpt_bot, '__name__') and gpt_bot.__name__ == '__main__':
                    import sys
                    sys.argv = ['gpt_bot.py']
                    exec(open(__file__.replace('__init__.py', 'gpt_bot.py')).read())

__all__ = ["run_bot"]