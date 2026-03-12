"""
问卷解析钩子测试
"""

import pytest
from src.hooks.questionnaire_parser import parse_questionnaire


class TestQuestionnaireParser:
    """测试问卷解析功能"""

    def test_parse_normal_data(self):
        """测试正常数据解析"""
        test_data = {
            "标题": "表白墙-今天天气真好",
            "内容": "我想对小明说：你是我见过最可爱的人！",
            "昵称": "小红",
            "标签": "表白,情感",
            "submit_time": "2024-01-01 12:00:00"
        }

        result = parse_questionnaire(test_data)

        assert result["title"] == "表白墙-今天天气真好"
        assert "小明" in result["content"]
        assert result["author"] == "小红"
        assert "表白" in result["tags"]

    def test_empty_content_raises_error(self):
        """测试空内容应该抛出异常"""
        test_data = {
            "标题": "测试",
            "内容": "",
            "昵称": "测试用户"
        }

        with pytest.raises(ValueError):
            parse_questionnaire(test_data)

    def test_default_title(self):
        """测试没有标题时使用默认标题"""
        test_data = {
            "内容": "这是投稿内容",
            "submit_time": "2024-01-01 12:00:00"
        }

        result = parse_questionnaire(test_data)

        assert result["title"].startswith("投稿-")
