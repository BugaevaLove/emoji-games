from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    buttons = [
        ["🎲 Кубик", "🎯 Дартс", "🎳 Боулинг"],
        ["⚽ Футбол", "🏀 Баскетбол", "🎰 Слоты"],
        ["👤 Профиль", "👥 Рефералы", "🎁 Кэшбэк"],
        ["🏆 Топ", "📊 Статистика", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def game_mode_keyboard(game_type: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Обычный", callback_data=f"game_{game_type}_normal")],
        [InlineKeyboardButton("📡 Telegram", callback_data=f"game_{game_type}_telegram")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ])

def bet_keyboard(game_type: str, mode: str):
    bets = [0.1, 0.5, 1, 5, 10, 25, 50, 75]
    rows = []
    for i in range(0, len(bets), 3):
        rows.append([
            InlineKeyboardButton(f"{b} USDT", callback_data=f"bet_{game_type}_{mode}_{b}")
            for b in bets[i:i+3]
        ])
    rows.append([InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_game_{game_type}")])
    return InlineKeyboardMarkup(rows)

def play_again_keyboard(game_type: str, mode: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Играть ещё", callback_data=f"again_{game_type}_{mode}")],
        [InlineKeyboardButton("🎮 Меню", callback_data="back_to_menu")]
    ])

def profile_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 VIP", callback_data="vip_progress"),
         InlineKeyboardButton("📋 История", callback_data="game_history")],
        [InlineKeyboardButton("💰 Пополнить", callback_data="deposit"),
         InlineKeyboardButton("💸 Вывести", callback_data="withdraw")],
        [InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton("🔍 Поиск", callback_data="admin_search")],
        [InlineKeyboardButton("💰 Выдать", callback_data="admin_give"),
         InlineKeyboardButton("💸 Списать", callback_data="admin_take")],
        [InlineKeyboardButton("🚫 Бан", callback_data="admin_ban"),
         InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Закрыть", callback_data="back_to_menu")]
    ])