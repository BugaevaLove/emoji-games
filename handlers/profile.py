from telegram import Update
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, ContextTypes
from database import db
from keyboards import profile_keyboard
from game_engine import get_vip_progress
from utils import format_number
from handlers.common import get_user, check_banned

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return
    user = await get_user(update)
    level, progress, _ = get_vip_progress(user["turnover"])
    bar = "█" * int(progress / 5) + "▒" * (20 - int(progress / 5))
    text = f"""
👤 *Профиль*
🆔 `{user['user_id']}`
💰 Баланс: {user['balance']:.2f} USDT
🔄 Оборот: {format_number(user['turnover'])} USDT
🎮 Игр: {user['games_played']} / Побед: {user.get('games_won',0)}
🏆 VIP {level} [{bar}] {progress:.1f}%
🎁 Кэшбек: {user.get('cashback_balance',0):.2f} USDT
💎 Рейкбек: {user.get('rakeback_balance',0):.2f} USDT
👥 Реф. баланс: {user.get('referral_balance',0):.2f} USDT
📅 {user['registered_at'][:10]}
    """
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=profile_keyboard())

async def vip_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await get_user(update)
    level, progress, reward = get_vip_progress(user["turnover"])
    from config import VIP_LEVELS
    current = VIP_LEVELS[level]
    next_lvl = VIP_LEVELS[level+1] if level+1 < len(VIP_LEVELS) else None
    text = f"🏆 VIP {level}\nКэшбек: {current['cashback']}% | Рейкбек: {current['rakeback']}%"
    if next_lvl:
        text += f"\nДо VIP {level+1}: {next_lvl['turnover'] - user['turnover']:.2f} USDT\nНаграда: {reward} USDT"
    await query.edit_message_text(text)

async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = await db.get_top_users(10)
    text = "🏆 *Топ игроков*\n"
    for i, u in enumerate(top, 1):
        name = u.get('first_name') or f"ID {u['user_id']}"
        text += f"{i}. {name} – {u['balance']:.2f} USDT (VIP {u['vip_level']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

profile_handler = MessageHandler(filters.Regex("^👤 Профиль$"), show_profile)
top_handler = MessageHandler(filters.Regex("^🏆 Топ$"), top_players)
vip_callback = CallbackQueryHandler(vip_progress, pattern="^vip_progress$")