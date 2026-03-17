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
                wx_nickname="测试作者",
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
            assert post.author == "测试作者"
            
            self._cleanup_test_db()

    def test_post_to_dict(self):
        """测试 Post 模型的 to_dict 方法"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            post = Post(
                title="测试投稿",
                content="这是测试内容",
                wx_nickname="测试作者",
                user_name="真实姓名",
                class_name="高一(1)班",
                status="pending"
            )
            session.add(post)
            session.commit()
            
            data = post.to_dict()
            
            assert data["title"] == "测试投稿"
            assert data["content"] == "这是测试内容"
            assert data["author"] == "测试作者"
            assert data["wx_nickname"] == "测试作者"
            assert data["user_name"] == "真实姓名"
            assert data["class_name"] == "高一(1)班"
            assert data["status"] == "pending"
            assert "created_at" in data
            
            self._cleanup_test_db()

    def test_author_property_priority(self):
        """测试 author 属性的优先级"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            # 有微信昵称
            post1 = Post(
                title="测试1",
                content="内容1",
                wx_nickname="微信昵称",
                user_name="真实姓名",
                status="pending"
            )
            session.add(post1)
            
            # 没有微信昵称，有姓名
            post2 = Post(
                title="测试2",
                content="内容2",
                wx_nickname=None,
                user_name="真实姓名",
                status="pending"
            )
            session.add(post2)
            
            # 都没有
            post3 = Post(
                title="测试3",
                content="内容3",
                status="pending"
            )
            session.add(post3)
            session.commit()
            
            assert post1.author == "微信昵称"
            assert post2.author == "真实姓名"
            assert post3.author == "匿名"
            
            self._cleanup_test_db()

    def test_post_to_markdown(self):
        """测试 Post 模型的 to_markdown 方法"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._setup_test_db(tmpdir)
            
            post = Post(
                title="测试投稿",
                content="这是投稿内容",
                wx_nickname="测试作者",
                user_name="小明",
                class_name="高一(1)班",
                submit_address="广东省-广州市",
                submit_time="2026-03-14 00:14:05",
                tduck_serial=1,
                status="pending"
            )
            session.add(post)
            session.commit()
            
            markdown = post.to_markdown()
            
            assert "**作者**：测试作者" in markdown
            assert "**班级**：高一(1)班" in markdown
            assert "**姓名**：小明" in markdown
            assert "这是投稿内容" in markdown
            assert "> 投稿序号：1" in markdown
            assert "> 提交时间：2026-03-14 00:14:05" in markdown
            assert "> 提交地点：广东省-广州市" in markdown
            
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
