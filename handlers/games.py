import time
from telegram import Update
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes
)
import database as db
from game_engine import (
    GameType, GameMode, GAME_EMOJIS, calculate_win, get_vip_level
)
from keyboards import (
    main_menu, game_mode_keyboard, bet_keyboard, play_again_keyboard
)
from utils import validate_bet, check_rate_limit
from handlers.common import get_user, check_banned
from config import REF_TURNOVER_BONUS, VIP_LEVELS

SELECT_MODE, SELECT_BET = range(2)

async def game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    text = update.message.text
    game_map = {
        "🎲 Кубик": GameType.DICE,
        "🎯 Дартс": GameType.DARTS,
        "🎳 Боулинг": GameType.BOWLING,
        "⚽ Футбол": GameType.FOOTBALL,
        "🏀 Баскетбол": GameType.BASKETBALL,
        "🎰 Слоты": GameType.SLOTS
    }
    game_type = game_map.get(text)
    if not game_type:
        return
    context.user_data["game_type"] = game_type
    await update.message.reply_text(
        f"Выбрана игра: {text}\nВыберите режим:",
        reply_markup=game_mode_keyboard(game_type.value)
    )
    return SELECT_MODE

async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    game_type = GameType(data[1])
    mode = GameMode(data[2])
    context.user_data["game_type"] = game_type
    context.user_data["mode"] = mode
    user = await get_user(update)
    await query.edit_message_text(
        f"🎮 {GAME_EMOJIS[game_type]} Режим: {mode.value.capitalize()}\n"
        f"💰 Баланс: {user['balance']:.2f} USDT\n"
        "Выберите ставку:",
        reply_markup=bet_keyboard(game_type.value, mode.value)
    )
    return SELECT_BET

async def bet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    game_type = GameType(data[1])
    mode = GameMode(data[2])
    bet = float(data[3])

    user = await get_user(update)
    user_id = user["user_id"]

    valid, err = validate_bet(bet, user["balance"])
    if not valid:
        await query.edit_message_text(f"❌ {err}")
        return ConversationHandler.END

    if not check_rate_limit(user):
        await query.edit_message_text("⏳ Слишком много игр! Подождите минуту.")
        return ConversationHandler.END

    # Списываем ставку
    new_balance = user["balance"] - bet
    await db.update_user(user_id, balance=new_balance)
    await db.add_transaction(user_id, "bet", -bet, f"Ставка {game_type.value} {mode.value}")

    # Отправляем dice
    emoji = GAME_EMOJIS[game_type]
    msg = await query.message.chat.send_dice(emoji=emoji)
    value = msg.dice.value

    win_amount, mult = calculate_win(game_type, value, bet, mode)
    final_balance = new_balance + win_amount

    new_turnover = user["turnover"] + bet
    old_level = user["vip_level"]
    new_level = get_vip_level(new_turnover)

    updates = {
        "balance": final_balance,
        "turnover": new_turnover,
        "games_played": user["games_played"] + 1,
        "vip_level": new_level,
        "last_game_time": time.time(),
        "game_count_minute": user.get("game_count_minute", 0) + 1
    }
    if win_amount > 0:
        updates["games_won"] = user.get("games_won", 0) + 1

    best_field = f"best_{game_type.value}"
    if value > user.get(best_field, 0):
        updates[best_field] = value

    await db.update_user(user_id, **updates)
    await db.add_game_history(user_id, game_type.value, mode.value, bet, value, win_amount)

    if user.get("referrer_id"):
        ref_bonus = bet * REF_TURNOVER_BONUS
        ref_user = await db.get_user(user["referrer_id"])
        if ref_user:
            await db.update_user(
                user["referrer_id"],
                referral_balance=ref_user["referral_balance"] + ref_bonus
            )
            await db.add_transaction(user["referrer_id"], "referral", ref_bonus, f"Оборот реферала {user_id}")

    vip_reward = 0.0
    if new_level > old_level:
        vip_reward = VIP_LEVELS[new_level]["reward"]
        await db.update_user(user_id, balance=final_balance + vip_reward)
        final_balance += vip_reward
        await db.add_transaction(user_id, "vip_reward", vip_reward, f"Достигнут VIP {new_level}")

    result_text = f"{emoji} Выпало: {value}\n"
    if win_amount > 0:
        result_text += f"🎉 Выигрыш: {win_amount:.2f} USDT (x{mult:.2f})\n"
    else:
        result_text += "😢 Проигрыш\n"
    result_text += f"💰 Баланс: {final_balance:.2f} USDT"
    if vip_reward > 0:
        result_text += f"\n\n🏆 Новый VIP {new_level}! Награда: {vip_reward:.2f} USDT"

    await query.edit_message_text(result_text)
    await query.message.reply_text(
        "Хотите сыграть ещё?",
        reply_markup=play_again_keyboard(game_type.value, mode.value)
    )
    return ConversationHandler.END

async def play_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    game_type = GameType(data[1])
    mode = GameMode(data[2])
    user = await get_user(update)
    await query.edit_message_text(
        f"🎮 {GAME_EMOJIS[game_type]} Режим: {mode.value.capitalize()}\n"
        f"💰 Баланс: {user['balance']:.2f} USDT\n"
        "Выберите ставку:",
        reply_markup=bet_keyboard(game_type.value, mode.value)
    )
    return SELECT_BET

async def back_to_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Назад' при выборе ставки."""
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    game_type = data[2]  # формат: back_to_game_dice
    await query.edit_message_text(
        f"Выбрана игра: {game_type}\nВыберите режим:",
        reply_markup=game_mode_keyboard(game_type)
    )
    return SELECT_MODE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено", reply_markup=main_menu())
    return ConversationHandler.END

# ConversationHandler с per_message=True и обработчиком back_to_game_
games_conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^(🎲 Кубик|🎯 Дартс|🎳 Боулинг|⚽ Футбол|🏀 Баскетбол|🎰 Слоты)$"), game_selected),
        CallbackQueryHandler(play_again, pattern=r"^again_")
    ],
    states={
        SELECT_MODE: [
            CallbackQueryHandler(mode_selected, pattern=r"^game_"),
            CallbackQueryHandler(back_to_mode_selection, pattern=r"^back_to_game_")
        ],
        SELECT_BET: [
            CallbackQueryHandler(bet_selected, pattern=r"^bet_"),
            CallbackQueryHandler(back_to_mode_selection, pattern=r"^back_to_game_")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
    per_message=True   # ← добавлено для устранения предупреждения
)
