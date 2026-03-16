"""
数据模型定义

定义投稿数据的存储结构。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from src.database import Base


class Post(Base):
    """
    投稿数据模型

    存储从 tduck 接收并审核通过的投稿。

    状态流转：
    - pending: 待同步到 Halo
    - synced: 已同步到 Halo
    - rejected: 已拒绝（不再同步）
    """
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    title = Column(String(255), nullable=False, comment="投稿标题")
    content = Column(Text, nullable=False, comment="投稿内容（Markdown）")
    author = Column(String(100), default="匿名", comment="作者")
    tags = Column(JSON, default=list, comment="标签列表")

    status = Column(
        String(20),
        default="pending",
        index=True,
        comment="状态: pending/synced/rejected"
    )

    tduck_id = Column(Integer, comment="tduck 记录 ID")
    tduck_serial = Column(Integer, comment="tduck 投稿序号")

    halo_post_id = Column(String(50), comment="Halo 文章 ID（同步后）")
    halo_post_url = Column(String(255), comment="Halo 文章链接（同步后）")

    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    synced_at = Column(DateTime, comment="同步到 Halo 的时间")

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        """
        转换为字典

        用于 API 返回 JSON 数据。
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "tags": self.tags or [],
            "status": self.status,
            "tduck_id": self.tduck_id,
            "tduck_serial": self.tduck_serial,
            "halo_post_id": self.halo_post_id,
            "halo_post_url": self.halo_post_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }
