from enum import Enum
from typing import Dict, Tuple, Optional

class GameType(str, Enum):
    DICE = "dice"
    DARTS = "darts"
    BOWLING = "bowling"
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    SLOTS = "slots"

class GameMode(str, Enum):
    NORMAL = "normal"
    TELEGRAM = "telegram"

GAME_EMOJIS = {
    GameType.DICE: "🎲",
    GameType.DARTS: "🎯",
    GameType.BOWLING: "🎳",
    GameType.FOOTBALL: "⚽",
    GameType.BASKETBALL: "🏀",
    GameType.SLOTS: "🎰",
}

# Множители для ОБЫЧНОГО режима (значение → множитель)
# Вероятности определены так, чтобы RTP был строго 95%
NORMAL_MULTIPLIERS: Dict[GameType, Dict[int, float]] = {
    GameType.DICE: {
        1: 0.0, 2: 0.0, 3: 0.0,
        4: 1.5, 5: 1.5, 6: 1.5
    },
    GameType.DARTS: {
        1: 0.0, 2: 0.0, 3: 0.0,
        4: 0.15, 5: 0.38, 6: 3.75
    },
    GameType.BOWLING: {
        1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0,
        6: 3.75
    },
    GameType.FOOTBALL: {
        1: 0.0, 2: 0.0, 3: 0.0,
        4: 1.13, 5: 1.31
    },
    GameType.BASKETBALL: {
        1: 0.0, 2: 0.0, 3: 0.0,
        4: 1.31, 5: 2.25
    },
    GameType.SLOTS: {
        **{i: 0.0 for i in range(1, 65)},
        1: 43.0, 2: 35.0, 3: 28.0, 4: 22.0,
        5: 18.0, 6: 15.0, 7: 12.0, 8: 10.0
    }
}

# Множители для TELEGRAM режима (используется send_dice, вероятности равномерные)
TELEGRAM_MULTIPLIERS: Dict[GameType, Dict[int, float]] = {
    GameType.DICE: {i: (1.5 if i >= 4 else 0.0) for i in range(1, 7)},
    GameType.DARTS: {i: 4.2 for i in range(1, 7)},
    GameType.BOWLING: {i: 4.2 for i in range(1, 7)},
    GameType.FOOTBALL: {
        1: 1.8, 2: 1.8, 3: 1.8,
        4: 3.5, 5: 3.5
    },
    GameType.BASKETBALL: {i: 3.5 for i in range(1, 6)},
    GameType.SLOTS: {
        **{i: 0.0 for i in range(1, 65)},
        1: 43.0, 2: 35.0, 3: 28.0, 4: 22.0
    }
}

def calculate_win(game_type: GameType, value: int, bet: float, mode: GameMode) -> Tuple[float, float]:
    mult_dict = TELEGRAM_MULTIPLIERS if mode == GameMode.TELEGRAM else NORMAL_MULTIPLIERS
    mult = mult_dict[game_type].get(value, 0.0)
    return bet * mult, mult

def get_vip_level(turnover: float) -> int:
    from config import VIP_LEVELS
    level = 0
    for i, lvl in enumerate(VIP_LEVELS):
        if turnover >= lvl["turnover"]:
            level = i
        else:
            break
    return level

def get_vip_progress(turnover: float) -> Tuple[int, float, float]:
    level = get_vip_level(turnover)
    from config import VIP_LEVELS
    current = VIP_LEVELS[level]["turnover"]
    if level + 1 < len(VIP_LEVELS):
        next_turnover = VIP_LEVELS[level + 1]["turnover"]
        progress = ((turnover - current) / (next_turnover - current)) * 100 if next_turnover > current else 100.0
        reward = VIP_LEVELS[level + 1]["reward"]
    else:
        progress = 100.0
        reward = 0.0
    return level, min(progress, 100.0), reward