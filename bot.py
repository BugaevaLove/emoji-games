from handlers import bot
import database

if __name__ == "__main__":
    database.init_db()
    print("Бот запущен...")
    bot.infinity_polling()