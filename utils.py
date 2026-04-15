import time
from typing import Tuple
from config import MIN_BET, MAX_BET

def validate_bet(bet: float, balance: float) -> Tuple[bool, str]:
    if bet < MIN_BET:
        return False, f"Минимум {MIN_BET} USDT"
    if bet > MAX_BET:
        return False, f"Максимум {MAX_BET} USDT"
    if bet > balance:
        return False, f"Недостаточно средств"
    return True, ""

def format_number(num: float) -> str:
    if abs(num) >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    if abs(num) >= 1_000:
        return f"{num/1_000:.2f}K"
    return f"{num:.2f}"

def check_rate_limit(user: dict) -> bool:
    now = time.time()
    if now - user.get("last_game_time", 0) > 60:
        user["game_count_minute"] = 0
    user["game_count_minute"] = user.get("game_count_minute", 0) + 1
    user["last_game_time"] = now
    from config import MAX_GAMES_PER_MINUTE
    return user["game_count_minute"] <= MAX_GAMES_PER_MINUTE