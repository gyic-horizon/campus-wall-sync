"""
数据库连接和初始化模块

使用 SQLAlchemy + SQLite 存储投稿数据。
SQLite 轻量级，无需额外容器，适合中小规模应用。
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
import src.config

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

    db_config = src.config.config.database
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

    创建所有表结构，并自动迁移 schema（添加缺失的列）。
    """
    from src.models import Post

    engine = get_engine()
    Base.metadata.create_all(engine)

    _migrate_schema(engine)

    logger.info("数据库表结构已创建/迁移完成")


def _migrate_schema(engine):
    """
    自动迁移数据库 schema

    检查数据库表中的列，如果缺少模型中定义的列，则自动添加。
    注意：只支持添加列，不支持删除列或修改列类型。
    """
    from src.models import Post

    inspector = inspect(engine)
    table_name = Post.__table__.name
    existing_tables = inspector.get_table_names()

    if table_name not in existing_tables:
        logger.info(f"表 {table_name} 不存在，跳过迁移")
        return

    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    expected_columns = {col.name for col in Post.__table__.columns}

    missing_columns = expected_columns - existing_columns

    if missing_columns:
        logger.warning(f"检测到 {table_name} 表缺少列: {missing_columns}，正在自动迁移...")
        with engine.connect() as conn:
            for col_name in missing_columns:
                col = Post.__table__.columns[col_name]
                col_type = col.type.compile(engine.dialect)
                default_value = col.default.arg if col.default else "NULL"

                sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                if default_value and default_value != "NULL":
                    sql += f" DEFAULT {default_value}"

                logger.info(f"执行迁移: {sql}")
                try:
                    conn.execute(sql)
                    conn.commit()
                    logger.info(f"成功添加列: {col_name}")
                except Exception as e:
                    logger.error(f"添加列 {col_name} 失败: {e}")


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
