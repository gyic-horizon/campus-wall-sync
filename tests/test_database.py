"""
数据库模块测试

测试数据库连接、模型和基本操作。
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from src import config as config_module
from src.database import init_db, get_session, reset_db, close_db
from src.models import Post
from src.config import Config


class TestDatabase:
    """测试数据库功能"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """每个测试前后清理数据库和配置"""
        reset_db()
        Config.reset()
        yield
        reset_db()
        Config.reset()

    def _setup_test_db(self, tmpdir):
        """设置测试数据库"""
        db_path = os.path.join(tmpdir, "test.db")
        config_path = os.path.join(tmpdir, "config.json")
        with open(config_path, "w") as f:
            json.dump({"database": {"path": db_path}}, f)
        os.environ["CONFIG_PATH"] = config_path
        Config.reset()
        config_module.config = Config()
        init_db()
        return get_session()

    def _cleanup_test_db(self):
        """清理测试数据库"""
        close_db()
        if "CONFIG_PATH" in os.environ:
            del os.environ["CONFIG_PATH"]

    def test_create_post(self):
        """测试创建投稿记录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            post = Post(
                title="测试投稿",
                content="这是测试内容",
                author="测试作者",
                tags=["标签1", "标签2"],
                status="pending",
                tduck_id=123,
                tduck_serial=1
            )
            session.add(post)
            session.commit()
            
            assert post.id is not None
            assert post.title == "测试投稿"
            assert post.status == "pending"
            
            self._cleanup_test_db()

    def test_post_to_dict(self):
        """测试 Post 模型的 to_dict 方法"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            post = Post(
                title="测试投稿",
                content="这是测试内容",
                author="测试作者",
                status="pending"
            )
            session.add(post)
            session.commit()
            
            data = post.to_dict()
            
            assert data["title"] == "测试投稿"
            assert data["content"] == "这是测试内容"
            assert data["author"] == "测试作者"
            assert data["status"] == "pending"
            assert "created_at" in data
            
            self._cleanup_test_db()

    def test_query_by_status(self):
        """测试按状态查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            post1 = Post(title="待处理1", content="内容1", status="pending")
            post2 = Post(title="待处理2", content="内容2", status="pending")
            post3 = Post(title="已同步", content="内容3", status="synced")
            
            session.add_all([post1, post2, post3])
            session.commit()
            
            pending_posts = session.query(Post).filter(Post.status == "pending").all()
            assert len(pending_posts) == 2
            
            synced_posts = session.query(Post).filter(Post.status == "synced").all()
            assert len(synced_posts) == 1
            
            self._cleanup_test_db()

    def test_update_post_status(self):
        """测试更新投稿状态"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            post = Post(title="测试", content="内容", status="pending")
            session.add(post)
            session.commit()
            
            post.status = "synced"
            post.halo_post_id = "abc123"
            post.synced_at = datetime.now()
            session.commit()
            
            updated = session.query(Post).filter(Post.id == post.id).first()
            assert updated.status == "synced"
            assert updated.halo_post_id == "abc123"
            
            self._cleanup_test_db()
