import asyncio
import sys
from telegram.ext import Application
from config import BOT_TOKEN
from database import db
from handlers import handlers

async def main():
    await db.init()
    app = Application.builder().token(BOT_TOKEN).build()
    for h in handlers:
        app.add_handler(h)
    print("Бот запущен...")
    # Запускаем polling. stop_signals=None отключает обработку сигналов внутри библиотеки,
    # чтобы не конфликтовать с управлением контейнера.
    await app.run_polling(stop_signals=None)

if __name__ == "__main__":
    # Проверяем, есть ли уже активный цикл событий (как в Railway/Cloud Run)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        # Нет активного цикла – запускаем стандартно
        asyncio.run(main())
    else:
        # Цикл уже запущен – добавляем нашу корутину в него
        task = loop.create_task(main())
        try:
            # Блокируемся до завершения задачи (при остановке контейнера)
            loop.run_until_complete(task)
        except KeyboardInterrupt:
            task.cancel()
            loop.run_until_complete(task)
        finally:
            # Не закрываем цикл – это сделает сама платформа
            pass