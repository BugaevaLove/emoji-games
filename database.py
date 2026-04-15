import sqlite3
import time
import random
from config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            best_dice INTEGER DEFAULT 0,
            best_darts INTEGER DEFAULT 0,
            best_bowling INTEGER DEFAULT 0,
            best_football INTEGER DEFAULT 0,
            best_basketball INTEGER DEFAULT 0,
            best_slots INTEGER DEFAULT 0,
            last_bonus_time REAL DEFAULT 0,
            task1_id INTEGER DEFAULT 0,
            task1_progress INTEGER DEFAULT 0,
            task2_id INTEGER DEFAULT 0,
            task2_progress INTEGER DEFAULT 0,
            task3_id INTEGER DEFAULT 0,
            task3_progress INTEGER DEFAULT 0,
            tasks_updated_at REAL DEFAULT 0,
            win_streak INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            goal INTEGER,
            reward INTEGER,
            type TEXT
        )
    """)
    # Предзаполняем задания
    cur.execute("SELECT COUNT(*) FROM daily_tasks")
    if cur.fetchone()[0] == 0:
        tasks = [
            ("Сыграть в кубик 3 раза", 3, 150, "dice"),
            ("Выиграть в слотах 1 раз", 1, 300, "slots_win"),
            ("Потратить 500$ в играх", 500, 200, "spend"),
            ("Сыграть в баскетбол 2 раза", 2, 150, "basketball"),
            ("Выиграть в дартс 1 раз", 1, 250, "darts_win"),
            ("Сыграть 5 игр в любые игры", 5, 200, "any_game"),
            ("Выиграть 3 игры подряд", 3, 500, "win_streak")
        ]
        cur.executemany(
            "INSERT INTO daily_tasks (description, goal, reward, type) VALUES (?, ?, ?, ?)",
            tasks
        )
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = ['user_id', 'balance', 'games_played', 'wins',
                   'best_dice', 'best_darts', 'best_bowling',
                   'best_football', 'best_basketball', 'best_slots',
                   'last_bonus_time', 'task1_id', 'task1_progress',
                   'task2_id', 'task2_progress', 'task3_id', 'task3_progress',
                   'tasks_updated_at', 'win_streak']
        user = dict(zip(columns, row))
        # Проверяем, нужно ли обновить задания (прошло > 24 часов)
        now = time.time()
        if now - user.get('tasks_updated_at', 0) > 86400:
            assign_daily_tasks(user_id, user)
        return user
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        user = {
            'user_id': user_id,
            'balance': 1000,
            'games_played': 0,
            'wins': 0,
            'best_dice': 0,
            'best_darts': 0,
            'best_bowling': 0,
            'best_football': 0,
            'best_basketball': 0,
            'best_slots': 0,
            'last_bonus_time': 0,
            'task1_id': 0, 'task1_progress': 0,
            'task2_id': 0, 'task2_progress': 0,
            'task3_id': 0, 'task3_progress': 0,
            'tasks_updated_at': 0,
            'win_streak': 0
        }
        assign_daily_tasks(user_id, user)
        return user

def assign_daily_tasks(user_id, user):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, description, goal, reward, type FROM daily_tasks ORDER BY RANDOM() LIMIT 3")
    tasks = cur.fetchall()
    conn.close()
    if tasks:
        updates = {
            'task1_id': tasks[0][0],
            'task1_progress': 0,
            'task2_id': tasks[1][0],
            'task2_progress': 0,
            'task3_id': tasks[2][0],
            'task3_progress': 0,
            'tasks_updated_at': time.time()
        }
        user.update(updates)
        update_user(user_id, **updates)

def update_user(user_id, **kwargs):
    if not kwargs:
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [user_id]
    cur.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_task_info(task_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT description, goal, reward, type FROM daily_tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return row  # (description, goal, reward, type)