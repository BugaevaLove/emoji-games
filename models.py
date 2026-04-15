from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_NAME

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(BigInteger, primary_key=True)
    balance = Column(Integer, default=1000)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    best_dice = Column(Integer, default=0)
    best_darts = Column(Integer, default=0)
    best_bowling = Column(Integer, default=0)
    best_football = Column(Integer, default=0)
    best_basketball = Column(Integer, default=0)
    best_slots = Column(Integer, default=0)
    last_bonus_time = Column(Float, default=0.0)
    task1_id = Column(Integer, default=0)
    task1_progress = Column(Integer, default=0)
    task2_id = Column(Integer, default=0)
    task2_progress = Column(Integer, default=0)
    task3_id = Column(Integer, default=0)
    task3_progress = Column(Integer, default=0)
    tasks_updated_at = Column(Float, default=0.0)
    win_streak = Column(Integer, default=0)

class DailyTask(Base):
    __tablename__ = 'daily_tasks'
    id = Column(Integer, primary_key=True)
    description = Column(String)
    goal = Column(Integer)
    reward = Column(Integer)
    type = Column(String)

# Пример создания сессии
# engine = create_engine(f'sqlite:///{DB_NAME}')
# Session = sessionmaker(bind=engine)
# session = Session()