from telegram import Update
from database import db

async def get_user(update: Update) -> dict:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    if not user:
        user = await db.create_user(
            user_id,
            update.effective_user.username or "",
            update.effective_user.first_name or ""
        )
    return user

async def check_banned(update: Update) -> bool:
    user = await get_user(update)
    if user.get("is_banned"):
        await update.effective_message.reply_text("⛔ Вы заблокированы.")
        return True
    return False