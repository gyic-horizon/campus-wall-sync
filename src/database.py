"""
数据库连接和初始化模块

使用 SQLAlchemy + SQLite 存储投稿数据。
SQLite 轻量级，无需额外容器，适合中小规模应用。
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config import config

logger = logging.getLogger(__name__)

Base = declarative_base()


def reset_db():
    """
    重置数据库连接（用于测试）
    """
    global _engine, _session_factory

    if _session_factory is not None:
        _session_factory.remove()
        _session_factory = None

    if _engine is not None:
        _engine.dispose()
        _engine = None

    logger.info("数据库连接已重置")

_engine = None
_session_factory = None


def get_engine():
    """
    获取数据库引擎（单例）

    数据库文件路径从 config.json 的 database.path 读取，
    默认为 data/campus_wall.db
    """
    global _engine

    if _engine is not None:
        return _engine

    db_config = config.database
    db_path = db_config.get("path", "data/campus_wall.db")

    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{db_path}"

    _engine = create_engine(
        db_url,
        echo=db_config.get("echo", False),
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )

    logger.info(f"数据库引擎已创建: {db_url}")
    return _engine


def get_session():
    """
    获取数据库会话

    使用 scoped_session 确保线程安全。
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = scoped_session(sessionmaker(bind=engine))

    return _session_factory()


def init_db():
    """
    初始化数据库

    创建所有表结构。
    """
    from src.models import Post

    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("数据库表结构已创建")


def close_db():
    """
    关闭数据库连接

    在应用关闭时调用。
    """
    global _engine, _session_factory

    if _session_factory is not None:
        _session_factory.remove()
        _session_factory = None

    if _engine is not None:
        _engine.dispose()
        _engine = None

    logger.info("数据库连接已关闭")
