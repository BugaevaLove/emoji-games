# games.py
GAME_COEFFICIENTS = {
    "🎲": {
        "name": "dice",
        "win_condition": lambda value: value in [1, 3, 5],
        "multiplier": lambda value: 2
    },
    "🎯": {
        "name": "darts",
        "win_condition": lambda value: value == 6,
        "multiplier": lambda value: 3
    },
    "🎳": {
        "name": "bowling",
        "win_condition": lambda value: value == 6,
        "multiplier": lambda value: 2
    },
    "⚽": {
        "name": "football",
        "win_condition": lambda value: value in [4, 5],
        "multiplier": lambda value: 2
    },
    "🏀": {
        "name": "basketball",
        "win_condition": lambda value: value in [4, 5],
        "multiplier": lambda value: 2
    },
    "🎰": {
        "name": "slots",
        "win_condition": lambda value: value in [1, 22, 43, 64],
        "multiplier": lambda value: {
            64: 20,
            43: 6,
            22: 3,
            1: 2
        }.get(value, 0)
    }
}

def calculate_win(emoji, value, bet):
    """Возвращает сумму выигрыша (0, если проигрыш)"""
    game = GAME_COEFFICIENTS.get(emoji)
    if not game:
        return 0
    if game["win_condition"](value):
        mult = game["multiplier"](value)
        if isinstance(mult, dict):
            mult = mult.get(value, 0)
        return bet * mult
    return 0

def update_best_score(user, game_emoji, value):
    """Обновляет лучший результат в конкретной игре"""
    game_name = GAME_COEFFICIENTS[game_emoji]["name"]
    best_field = f"best_{game_name}"
    current_best = user.get(best_field, 0)
    if value > current_best:
        user[best_field] = value
        return True
    return False