from telebot import types

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["🎲 Кубик", "🎯 Дартс", "🎳 Боулинг",
               "⚽ Футбол", "🏀 Баскетбол", "🎰 Слоты"]
    markup.add(*[types.KeyboardButton(text) for text in buttons])
    markup.add("💰 Баланс", "🏆 Топ", "📊 Статистика")
    return markup

def bet_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    bets = [10, 25, 50, 100, 250, 500]
    buttons = [types.InlineKeyboardButton(text=f"{b}$", callback_data=f"bet_{b}") for b in bets]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return markup