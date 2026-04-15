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
    await app.run_polling(stop_signals=None)

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        asyncio.run(main())
    else:
        # В среде с уже запущенным циклом (Cloud Run) создаём задачу
        task = loop.create_task(main())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            task.cancel()
            loop.run_until_complete(task)