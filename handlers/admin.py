import asyncio
from telegram import Update
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes
)
import database as db
from keyboards import admin_panel_keyboard
from config import ADMIN_IDS

SEARCH, GIVE, TAKE, BAN, BROADCAST = range(5)

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.effective_message.reply_text("⛔ Доступ запрещён")
            return
        return await func(update, context)
    return wrapper

@admin_only
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 *Админ‑панель*", parse_mode="Markdown", reply_markup=admin_panel_keyboard())

@admin_only
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stats = await db.get_total_stats()
    text = f"👥 {stats['total_users']} | 💰 {stats['total_balance']:.2f} | 🔄 {stats['total_turnover']:.2f}"
    await query.edit_message_text(f"📊 *Статистика*\n{text}", parse_mode="Markdown", reply_markup=admin_panel_keyboard())

@admin_only
async def admin_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔍 Введите ID, username или имя:")
    return SEARCH

@admin_only
async def admin_search_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = await db.search_users(update.message.text)
    if not users:
        await update.message.reply_text("Ничего не найдено")
    else:
        resp = "\n".join(
            f"{'🚫' if u['is_banned'] else '✅'} {u['user_id']} @{u.get('username','-')} | {u['balance']:.2f}$ | VIP {u['vip_level']}"
            for u in users[:10]
        )
        await update.message.reply_text(resp)
    return ConversationHandler.END

@admin_only
async def admin_give_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("💰 Введите ID и сумму: `123456 100`", parse_mode="Markdown")
    return GIVE

@admin_only
async def admin_give_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split()
        target_id, amount = int(parts[0]), float(parts[1])
        user = await db.get_user(target_id)
        if not user:
            raise ValueError("Пользователь не найден")
        await db.update_user(target_id, balance=user["balance"] + amount)
        await db.add_transaction(target_id, "admin_give", amount, f"Выдано {update.effective_user.id}")
        await update.message.reply_text(f"✅ {target_id} +{amount} USDT")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    return ConversationHandler.END

@admin_only
async def admin_take_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("💸 Введите ID и сумму:")
    return TAKE

@admin_only
async def admin_take_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split()
        target_id, amount = int(parts[0]), float(parts[1])
        user = await db.get_user(target_id)
        if user["balance"] < amount:
            raise ValueError("Недостаточно средств")
        await db.update_user(target_id, balance=user["balance"] - amount)
        await db.add_transaction(target_id, "admin_take", -amount, f"Списано {update.effective_user.id}")
        await update.message.reply_text(f"✅ {target_id} -{amount} USDT")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
    return ConversationHandler.END

@admin_only
async def admin_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🚫 Введите ID для бана/разбана:")
    return BAN

@admin_only
async def admin_ban_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(update.message.text)
        user = await db.get_user(target_id)
        new_status = 0 if user["is_banned"] else 1
        await db.update_user(target_id, is_banned=new_status)
        await update.message.reply_text(f"{'Забанен' if new_status else 'Разбанен'} {target_id}")
    except:
        await update.message.reply_text("❌ Неверный ID")
    return ConversationHandler.END

@admin_only
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📢 Введите текст рассылки:")
    return BROADCAST

@admin_only
async def admin_broadcast_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    async with db.get_connection() as conn:
        async with conn.execute("SELECT user_id FROM users WHERE is_banned=0") as cursor:
            rows = await cursor.fetchall()
    success = 0
    for row in rows:
        try:
            await context.bot.send_message(row[0], text)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await update.message.reply_text(f"✅ Доставлено: {success}")
    return ConversationHandler.END

admin_conv = ConversationHandler(
    entry_points=[
        CommandHandler("admin", admin_start),
        CallbackQueryHandler(admin_stats, pattern="^admin_stats$"),
        CallbackQueryHandler(admin_search_start, pattern="^admin_search$"),
        CallbackQueryHandler(admin_give_start, pattern="^admin_give$"),
        CallbackQueryHandler(admin_take_start, pattern="^admin_take$"),
        CallbackQueryHandler(admin_ban_start, pattern="^admin_ban$"),
        CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$")
    ],
    states={
        SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_do)],
        GIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_give_do)],
        TAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_take_do)],
        BAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_do)],
        BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_do)]
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)