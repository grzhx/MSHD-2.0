# app/database.py
"""
数据库初始化模块
负责：
1. 创建 SQLAlchemy 引擎（Engine）
2. 创建 SessionLocal（数据库会话工厂）
3. 定义 Base（所有 ORM 模型的基类）
4. 提供 get_db() 依赖，给 FastAPI 注入 db 会话
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import DATABASE_URL

# 创建数据库引擎
# 注意：connect_args={"check_same_thread": False} 是 SQLite 的特殊参数，
# 允许在不同线程中操作同一个连接（开发环境方便用）。
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # 只对 SQLite 有效，换 MySQL 可以去掉
)

# SessionLocal 是一个“会话工厂”，每次通过 SessionLocal() 生成一个新的会话对象
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有 ORM 模型都要继承这个 Base
Base = declarative_base()


def get_db():
    """
    FastAPI 依赖注入函数。
    在接口函数参数列表中写：
        db: Session = Depends(get_db)
    FastAPI 就会自动创建一个数据库会话，接口执行完毕后自动关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
