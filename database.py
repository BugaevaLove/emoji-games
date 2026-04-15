import sqlite3
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
            best_slots INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        # Преобразуем кортеж в словарь
        columns = ['user_id', 'balance', 'games_played', 'wins',
                   'best_dice', 'best_darts', 'best_bowling',
                   'best_football', 'best_basketball', 'best_slots']
        return dict(zip(columns, row))
    else:
        # Создаём нового пользователя с балансом 1000
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return {
            'user_id': user_id,
            'balance': 1000,
            'games_played': 0,
            'wins': 0,
            'best_dice': 0,
            'best_darts': 0,
            'best_bowling': 0,
            'best_football': 0,
            'best_basketball': 0,
            'best_slots': 0
        }

def update_user(user_id, **kwargs):
    """Обновляет поля пользователя, переданные в kwargs"""
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