from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from database import db
from keyboards import main_menu
from handlers.common import get_user, check_banned

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return
    user = await get_user(update)
    args = context.args
    if args and args[0].startswith("ref"):
        try:
            ref_id = int(args[0][3:])
            if ref_id != user["user_id"] and not user.get("referrer_id"):
                ref_user = await db.get_user(ref_id)
                if ref_user:
                    await db.update_user(user["user_id"], referrer_id=ref_id)
        except ValueError:
            pass

    await update.message.reply_text(
        f"🎰 Привет, {update.effective_user.first_name}!\n"
        f"💰 Баланс: {user['balance']:.2f} USDT\n"
        "Выберите игру:",
        reply_markup=main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🎰 *Помощь*

*Игры и множители (Обычный/Telegram):*
🎲 Кубик: >3 → 1.5x / 1.5x
🎯 Дартс: 6→3.75x,5→0.38x,4→0.15x / 4.2x
🎳 Боулинг: 6→3.75x / 4.2x
⚽ Футбол: 5→1.31x,4→1.13x / 5,4→3.5x, 1-3→1.8x
🏀 Баскетбол: 5→2.25x,4→1.31x / 3.5x
🎰 Слоты: комбинации до 43x

*VIP:* повышайте оборот, получайте кэшбек и рейкбек.
*Рефералы:* 10% от депозитов + 12% от оборота друга.

/admin – панель администратора
    """
    await update.message.reply_text(text, parse_mode="Markdown")

start_handler = CommandHandler("start", start)
help_handler = CommandHandler("help", help_command)