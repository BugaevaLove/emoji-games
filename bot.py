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
    # Запускаем polling без обработки сигналов остановки
    await app.run_polling(stop_signals=None)

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        # Нет активного цикла — запускаем стандартным способом
        asyncio.run(main())
    else:
        # Цикл уже запущен — создаём задачу в нём и ожидаем завершения
        task = loop.create_task(main())
        try:
            # run_forever будет работать, пока задача не завершится
            loop.run_until_complete(task)
        except KeyboardInterrupt:
            task.cancel()
            loop.run_until_complete(task)
        finally:
            # Не закрываем цикл, так как он управляется средой выполнения
            pass