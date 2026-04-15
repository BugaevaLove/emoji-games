import telebot
from telebot import types
from config import TOKEN
import database as db
import games
import keyboards as kb

bot = telebot.TeleBot(TOKEN)

# Временное хранилище для ожидания выбора ставки (можно заменить на redis в будущем)
user_game_choice = {}  # {user_id: game_emoji}

@bot.message_handler(commands=['start'])
def start(message):
    db.init_db()
    user = db.get_user(message.from_user.id)
    bot.send_message(message.chat.id,
                     f"Привет, {message.from_user.first_name}!\n"
                     f"Твой баланс: {user['balance']}$\n"
                     "Выбери игру:",
                     reply_markup=kb.main_menu())

@bot.message_handler(func=lambda m: m.text and m.text.split()[0] in ["🎲", "🎯", "🎳", "⚽", "🏀", "🎰"])
def game_selected(message):
    user_id = message.from_user.id
    emoji = message.text.split()[0]
    user = db.get_user(user_id)
    user_game_choice[user_id] = emoji
    bot.send_message(message.chat.id,
                     f"Выбрана игра {emoji}. Твой баланс: {user['balance']}$\n"
                     "Выбери ставку:",
                     reply_markup=kb.bet_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("bet_"))
def process_bet(call):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    emoji = user_game_choice.get(user_id)
    if not emoji:
        bot.answer_callback_query(call.id, "Сначала выбери игру!")
        return

    bet = int(call.data.split("_")[1])
    if bet > user['balance']:
        bot.answer_callback_query(call.id, "Недостаточно средств!")
        return

    # Отправляем "кости"
    msg = bot.send_dice(call.message.chat.id, emoji=emoji)
    value = msg.dice.value

    # Рассчитываем выигрыш
    win = games.calculate_win(emoji, value, bet)
    new_balance = user['balance'] - bet + win
    is_win = win > 0

    # Обновляем статистику
    updates = {
        'balance': new_balance,
        'games_played': user['games_played'] + 1
    }
    if is_win:
        updates['wins'] = user['wins'] + 1

    # Обновляем лучший результат
    game_name = games.GAME_COEFFICIENTS[emoji]["name"]
    best_field = f"best_{game_name}"
    if value > user.get(best_field, 0):
        updates[best_field] = value

    db.update_user(user_id, **updates)

    # Формируем ответ
    result_text = f"Выпало: {value}\n"
    if is_win:
        result_text += f"🎉 Поздравляем! Ты выиграл {win}$!\n"
    else:
        result_text += "😢 К сожалению, ты проиграл.\n"
    result_text += f"Текущий баланс: {new_balance}$"

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=result_text)
    bot.answer_callback_query(call.id)

    # Удаляем временный выбор игры
    user_game_choice.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_bet(call):
    user_id = call.from_user.id
    user_game_choice.pop(user_id, None)
    bot.edit_message_text("Ставка отменена.",
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    user = db.get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"Твой баланс: {user['balance']}$")

@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(message):
    top_users = db.get_top_users(10)
    if not top_users:
        bot.send_message(message.chat.id, "Пока никто не играл.")
        return
    text = "🏆 Топ-10 игроков по балансу:\n"
    for i, (uid, bal) in enumerate(top_users, 1):
        text += f"{i}. {uid} — {bal}$\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    user = db.get_user(message.from_user.id)
    text = (f"📊 Твоя статистика:\n"
            f"Игр сыграно: {user['games_played']}\n"
            f"Побед: {user['wins']}\n"
            f"Лучший кубик: {user['best_dice']}\n"
            f"Лучший дартс: {user['best_darts']}\n"
            f"Лучший боулинг: {user['best_bowling']}\n"
            f"Лучший футбол: {user['best_football']}\n"
            f"Лучший баскетбол: {user['best_basketball']}\n"
            f"Лучшие слоты: {user['best_slots']}")
    bot.send_message(message.chat.id, text)