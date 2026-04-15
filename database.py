import aiosqlite
from contextlib import asynccontextmanager
from config import DB_NAME

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()

    async def init(self):
        async with self.get_connection() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance REAL DEFAULT 0.0,
                    total_deposits REAL DEFAULT 0.0,
                    total_withdrawals REAL DEFAULT 0.0,
                    turnover REAL DEFAULT 0.0,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    vip_level INTEGER DEFAULT 0,
                    cashback_balance REAL DEFAULT 0.0,
                    rakeback_balance REAL DEFAULT 0.0,
                    referral_balance REAL DEFAULT 0.0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned INTEGER DEFAULT 0,
                    referrer_id INTEGER,
                    last_game_time REAL DEFAULT 0,
                    game_count_minute INTEGER DEFAULT 0,
                    best_dice INTEGER DEFAULT 0,
                    best_darts INTEGER DEFAULT 0,
                    best_bowling INTEGER DEFAULT 0,
                    best_football INTEGER DEFAULT 0,
                    best_basketball INTEGER DEFAULT 0,
                    best_slots INTEGER DEFAULT 0,
                    FOREIGN KEY(referrer_id) REFERENCES users(user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_type TEXT,
                    mode TEXT,
                    bet REAL,
                    result_value INTEGER,
                    win_amount REAL,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    amount REAL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            await db.commit()

    async def get_user(self, user_id: int):
        async with self.get_connection() as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_user(self, user_id: int, username: str, first_name: str, referrer_id: int = None):
        async with self.get_connection() as db:
            await db.execute(
                "INSERT INTO users (user_id, username, first_name, referrer_id) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, referrer_id)
            )
            await db.commit()
        return await self.get_user(user_id)

    async def update_user(self, user_id: int, **kwargs):
        if not kwargs:
            return
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]
        async with self.get_connection() as db:
            await db.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
            await db.commit()

    async def add_transaction(self, user_id: int, tx_type: str, amount: float, description: str = ""):
        async with self.get_connection() as db:
            await db.execute(
                "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
                (user_id, tx_type, amount, description)
            )
            await db.commit()

    async def add_game_history(self, user_id: int, game_type: str, mode: str, bet: float, result_value: int, win_amount: float):
        async with self.get_connection() as db:
            await db.execute(
                "INSERT INTO game_history (user_id, game_type, mode, bet, result_value, win_amount) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, game_type, mode, bet, result_value, win_amount)
            )
            await db.commit()

    async def get_top_users(self, limit: int = 10):
        async with self.get_connection() as db:
            async with db.execute(
                "SELECT user_id, username, first_name, balance, vip_level FROM users WHERE is_banned = 0 ORDER BY balance DESC LIMIT ?",
                (limit,)
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def search_users(self, query: str):
        async with self.get_connection() as db:
            async with db.execute(
                """SELECT user_id, username, first_name, balance, turnover, vip_level, is_banned
                   FROM users
                   WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ?
                   LIMIT 20""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_total_stats(self):
        async with self.get_connection() as db:
            async with db.execute(
                "SELECT COUNT(*) as total_users, SUM(balance) as total_balance, SUM(turnover) as total_turnover FROM users"
            ) as cursor:
                row = await cursor.fetchone()
                return {
                    "total_users": row["total_users"] or 0,
                    "total_balance": row["total_balance"] or 0.0,
                    "total_turnover": row["total_turnover"] or 0.0
                }

db = Database(DB_NAME)