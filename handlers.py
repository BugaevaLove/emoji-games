import telebot
from telebot import types
import time
import random
import logging

from config import TOKEN
import database as db
import games
import keyboards as kb

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

# Временное хранилище для выбора игры
user_game_choice = {}
# Антиспам
user_last_action = {}
RATE_LIMIT_SECONDS = 2
# Список админов (замените на свои ID)
ADMIN_IDS = [8746489804]

def rate_limit_check(user_id):
    now = time.time()
    last = user_last_action.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return False
    user_last_action[user_id] = now
    return True

def admin_only(func):
    def wrapper(message):
        if message.from_user.id in ADMIN_IDS:
            return func(message)
        else:
            bot.reply_to(message, "⛔ У вас нет прав для выполнения этой команды.")
    return wrapper

def update_task_progress(user_id, game_emoji, bet, is_win):
    user = db.get_user(user_id)
    tasks_updated = False
    now = time.time()

    for i in range(1, 4):
        task_id = user[f'task{i}_id']
        if task_id == 0:
            continue
        task = db.get_task_info(task_id)
        if not task:
            continue
        desc, goal, reward, ttype = task
        progress = user[f'task{i}_progress']
        if progress >= goal:
            continue

        # Логика прогресса
        if ttype == 'dice' and game_emoji == '🎲':
            progress += 1
        elif ttype == 'basketball' and game_emoji == '🏀':
            progress += 1
        elif ttype == 'slots_win' and game_emoji == '🎰' and is_win:
            progress += 1
        elif ttype == 'darts_win' and game_emoji == '🎯' and is_win:
            progress += 1
        elif ttype == 'any_game':
            progress += 1
        elif ttype == 'spend':
            progress += bet
        elif ttype == 'win_streak':
            if is_win:
                new_streak = user.get('win_streak', 0) + 1
            else:
                new_streak = 0
            db.update_user(user_id, win_streak=new_streak)
            user['win_streak'] = new_streak
            if new_streak >= goal:
                progress = goal
            else:
                progress = new_streak

        if progress > goal:
            progress = goal

        if progress != user[f'task{i}_progress']:
            user[f'task{i}_progress'] = progress
            tasks_updated = True

        # Выполнение задания
        if progress == goal:
            # Проверяем, не начисляли ли уже награду
            # (можно добавить флаг в БД, но для простоты проверим по прогрессу == goal)
            # Начислим только один раз
            if user.get(f'task{i}_completed', 0) == 0:
                user['balance'] += reward
                db.update_user(user_id, balance=user['balance'])
                user[f'task{i}_completed'] = 1
                try:
                    bot.send_message(user_id, f"🎯 Задание выполнено: {desc}\n💰 Награда: {reward}$")
                except:
                    pass

    if tasks_updated:
        updates = {f'task{i}_progress': user[f'task{i}_progress'] for i in range(1,4)}
        db.update_user(user_id, **updates)

# ------------------- Обработчики -------------------

@bot.message_handler(commands=['start'])
def start(message):
    db.init_db()
    user = db.get_user(message.from_user.id)
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    bot.send_message(message.chat.id,
                     f"Привет, {message.from_user.first_name}!\n"
                     f"Твой баланс: {user['balance']}$\n"
                     "Выбери игру:",
                     reply_markup=kb.main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = (
        "🎰 **Emoji Games Bot — Помощь**\n\n"
        "**Игры:**\n"
        "🎲 Кубик — выигрыш при 1,3,5 (x2)\n"
        "🎯 Дартс — выигрыш при 6 (x3)\n"
        "🎳 Боулинг — выигрыш при 6 (x2)\n"
        "⚽ Футбол — выигрыш при 4,5 (x2)\n"
        "🏀 Баскетбол — выигрыш при 4,5 (x2)\n"
        "🎰 Слоты — особые комбинации:\n"
        "   64 → x20, 43 → x6, 22 → x3, 1 → x2\n\n"
        "**Команды:**\n"
        "/start — начать работу\n"
        "/balance — баланс\n"
        "/top — рейтинг игроков\n"
        "/stats — ваша статистика\n"
        "/bonus — ежедневный бонус\n"
        "/tasks — ежедневные задания\n"
        "/help — это сообщение\n\n"
        "Администраторам доступны команды управления балансом."
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text and m.text.split()[0] in ["🎲", "🎯", "🎳", "⚽", "🏀", "🎰"])
def game_selected(message):
    user_id = message.from_user.id
    emoji = message.text.split()[0]
    user = db.get_user(user_id)
    user_game_choice[user_id] = emoji
    logger.info(f"Пользователь {user_id} выбрал игру {emoji}")
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

    if not rate_limit_check(user_id):
        bot.answer_callback_query(call.id, "⏳ Слишком быстро! Подожди пару секунд.")
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

    # Логирование
    logger.info(f"User {user_id} играл в {emoji}, ставка {bet}, выпало {value}, выигрыш {win}")

    # Обновляем прогресс заданий
    update_task_progress(user_id, emoji, bet, is_win)

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

    # Предлагаем сыграть ещё раз
    bot.send_message(call.message.chat.id, "Хочешь сыграть ещё?",
                     reply_markup=kb.play_again_keyboard(emoji))

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

@bot.callback_query_handler(func=lambda call: call.data.startswith("again_"))
def play_again(call):
    emoji = call.data.split("_")[1]
    user_id = call.from_user.id
    user = db.get_user(user_id)
    user_game_choice[user_id] = emoji
    bot.edit_message_text(
        f"Выбрана игра {emoji}. Твой баланс: {user['balance']}$\nВыбери ставку:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=kb.bet_keyboard()
    )

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

@bot.message_handler(commands=['bonus'])
@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
def daily_bonus(message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    now = time.time()
    last_bonus = user.get('last_bonus_time', 0)
    cooldown = 24 * 60 * 60

    if now - last_bonus < cooldown:
        wait_time = cooldown - (now - last_bonus)
        hours = int(wait_time // 3600)
        minutes = int((wait_time % 3600) // 60)
        bot.reply_to(message, f"🎁 Бонус можно получать раз в 24 часа.\nПопробуй через {hours} ч. {minutes} мин.")
        return

    bonus_amount = random.randint(50, 500)
    new_balance = user['balance'] + bonus_amount
    db.update_user(user_id, balance=new_balance, last_bonus_time=now)

    logger.info(f"User {user_id} получил ежедневный бонус {bonus_amount}$")
    bot.reply_to(message, f"🎉 Твой ежедневный бонус: {bonus_amount}$!\nТекущий баланс: {new_balance}$")

@bot.message_handler(commands=['tasks'])
@bot.message_handler(func=lambda m: m.text == "📋 Задания")
def show_tasks(message):
    user = db.get_user(message.from_user.id)
    text = "📋 **Ежедневные задания:**\n\n"
    for i in range(1, 4):
        task_id = user[f'task{i}_id']
        if task_id:
            desc, goal, reward, _ = db.get_task_info(task_id)
            progress = user[f'task{i}_progress']
            text += f"{i}. {desc} ({progress}/{goal}) — 💰 {reward}$\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# Админские команды
@bot.message_handler(commands=['give'])
@admin_only
def give_balance(message):
    try:
        _, user_id_str, amount_str = message.text.split()
        user_id = int(user_id_str)
        amount = int(amount_str)

        user = db.get_user(user_id)
        if not user:
            bot.reply_to(message, f"❌ Пользователь с ID {user_id} не найден.")
            return

        new_balance = user['balance'] + amount
        db.update_user(user_id, balance=new_balance)
        logger.info(f"Admin {message.from_user.id} выдал {amount}$ пользователю {user_id}")
        bot.reply_to(message, f"✅ Баланс пользователя {user_id} увеличен на {amount}$.\nНовый баланс: {new_balance}$")
    except (ValueError, IndexError):
        bot.reply_to(message, "❌ Неверный формат. Используйте: /give <user_id> <amount>")

@bot.message_handler(commands=['take'])
@admin_only
def take_balance(message):
    try:
        _, user_id_str, amount_str = message.text.split()
        user_id = int(user_id_str)
        amount = int(amount_str)

        user = db.get_user(user_id)
        if not user:
            bot.reply_to(message, f"❌ Пользователь с ID {user_id} не найден.")
            return

        if amount > user['balance']:
            bot.reply_to(message, f"❌ У пользователя недостаточно средств. Баланс: {user['balance']}$")
            return

        new_balance = user['balance'] - amount
        db.update_user(user_id, balance=new_balance)
        logger.info(f"Admin {message.from_user.id} снял {amount}$ у пользователя {user_id}")
        bot.reply_to(message, f"✅ С баланса пользователя {user_id} снято {amount}$.\nНовый баланс: {new_balance}$")
    except (ValueError, IndexError):
        bot.reply_to(message, "❌ Неверный формат. Используйте: /take <user_id> <amount>")

@bot.message_handler(commands=['setbalance'])
@admin_only
def set_balance(message):
    try:
        _, user_id_str, amount_str = message.text.split()
        user_id = int(user_id_str)
        amount = int(amount_str)

        db.update_user(user_id, balance=amount)
        logger.info(f"Admin {message.from_user.id} установил баланс {amount}$ пользователю {user_id}")
        bot.reply_to(message, f"✅ Баланс пользователя {user_id} установлен на {amount}$.")
    except (ValueError, IndexError):
        bot.reply_to(message, "❌ Неверный формат. Используйте: /setbalance <user_id> <amount>")