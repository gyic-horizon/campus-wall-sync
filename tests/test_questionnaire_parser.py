"""
问卷解析钩子测试 - tduck 表单版本（使用真实 Webhook 数据）
"""

import pytest
from src.hooks.questionnaire_parser import (
    parse_questionnaire,
    parse_from_api_response,
    FIELD_CLASS,
    FIELD_NAME,
    FIELD_CONTENT,
)


def make_webhook_data(
    class_name: str = "高一十三班",
    user_name: str = "小明",
    content: str = "我喜欢小红",
    serial_number: int = 4,
    wx_nickname: str = "xiaoming",
    wx_openid: str = "888888888888-EUZO7Orkw1QnMvY",
    **kwargs
) -> dict:
    """
    构建测试用 Webhook 数据

    使用动态字段 ID，避免硬编码问题。
    """
    data = {
        FIELD_CLASS: class_name,
        FIELD_NAME: user_name,
        FIELD_CONTENT: content,
        "dataId": "22c480500000000003de288e992042b3",
        "formKey": "y0ccu2pa",
        "serialNumber": serial_number,
        "submitUa": {
            "os": {"name": "Android", "version": "15"},
            "ua": "Mozilla/5.0 (Linux; Android 15; NX733J Build/AQ3A.240812.002; wv)...",
        },
        "submitOs": "Android",
        "submitBrowser": "WeChat",
        "submitRequestIp": "111.222.0.333",
        "submitAddress": "广东省-广州市",
        "completeTime": 45527,
        "wxOpenId": wx_openid,
        "wxUserInfo": {
            "sex": 0,
            "city": "",
            "openid": wx_openid,
            "country": "",
            "unionId": "oMovy0_0h8Hqck1111111111mSIA",
            "nickname": wx_nickname,
            "province": "",
            "headImgUrl": "https://thirdwx.qlogo.cn/mmopen/vi_32/...",
            "privileges": [],
            "snapshotUser": None
        },
        "extValue": "",
        "userId": None,
        "createByName": None,
        "updateByName": None,
        "otherParam": {},
        "beginTime": "2026-03-14 00:13:19",
        "deleted": False,
        "createBy": "",
        "updateBy": None,
        "id": 623899,
        "createTime": "2026-03-14 00:14:05",
        "updateTime": "2026-03-14 00:14:05",
        "eventType": "form_data_add",
        "eventTime": 1773498073370
    }
    data.update(kwargs)
    return data


class TestQuestionnaireParser:
    """测试 tduck 表单解析功能"""

    def test_parse_real_webhook_data(self):
        """测试真实 Webhook 数据解析"""
        result = parse_questionnaire(make_webhook_data())

        assert result["title"] == "高一十三班-小明的投稿"
        assert result["content"] == "我喜欢小红"
        assert result["wx_nickname"] == "xiaoming"
        assert result["wx_openid"] == "888888888888-EUZO7Orkw1QnMvY"
        assert result["class_name"] == "高一十三班"
        assert result["user_name"] == "小明"
        assert result["submit_address"] == "广东省-广州市"
        assert result["submit_time"] == "2026-03-14 00:14:05"
        assert "高一十三班" in result["tags"]
        assert result["tduck_id"] == 623899
        assert result["tduck_serial"] == 4

    def test_parse_without_wx_nickname(self):
        """测试没有微信昵称时的处理"""
        test_data = make_webhook_data(wx_nickname="")
        test_data["wxUserInfo"] = {}

        result = parse_questionnaire(test_data)

        assert result["wx_nickname"] is None
        assert result["user_name"] == "小明"
        assert "小明的投稿" in result["title"]

    def test_parse_minimal_data(self):
        """测试最小数据（只有内容）"""
        test_data = {
            "serialNumber": 5,
            "createTime": "2026-03-14 11:00:00",
            FIELD_CONTENT: "匿名投稿内容",
            "wxUserInfo": {"nickname": ""}
        }

        result = parse_questionnaire(test_data)

        assert "投稿-5" in result["title"]
        assert result["content"] == "匿名投稿内容"
        assert result["wx_nickname"] is None
        assert result["class_name"] is None
        assert result["user_name"] is None
        assert result["tags"] == []

    def test_empty_content_raises_error(self):
        """测试空内容应该抛出异常"""
        test_data = make_webhook_data(content="")

        with pytest.raises(ValueError, match="投稿内容不能为空"):
            parse_questionnaire(test_data)

    def test_parse_api_response_format(self):
        """测试 API 响应格式（有 originalData 嵌套）"""
        api_format_data = {
            "id": 623900,
            "serialNumber": 5,
            "createTime": "2026-03-14 10:00:00",
            "originalData": {
                FIELD_CLASS: "高二(3)班",
                FIELD_NAME: "李四",
                FIELD_CONTENT: "API格式测试投稿"
            },
            "wxUserInfo": {
                "nickname": "李四同学"
            }
        }

        result = parse_questionnaire(api_format_data)

        assert result["title"] == "高二(3)班-李四的投稿"
        assert result["content"] == "API格式测试投稿"
        assert result["wx_nickname"] == "李四同学"

    def test_parse_from_api_response(self):
        """测试从 API 响应解析多条记录"""
        api_response = {
            "code": 200,
            "data": {
                "records": [
                    {
                        "id": 1,
                        "serialNumber": 1,
                        "createTime": "2026-03-14 08:00:00",
                        FIELD_CLASS: "高一(1)班",
                        FIELD_NAME: "学生A",
                        FIELD_CONTENT: "第一条投稿",
                        "wxUserInfo": {"nickname": "学生A昵称"}
                    },
                    {
                        "id": 2,
                        "serialNumber": 2,
                        "createTime": "2026-03-14 09:00:00",
                        FIELD_CLASS: "高一(2)班",
                        FIELD_NAME: "学生B",
                        FIELD_CONTENT: "第二条投稿",
                        "wxUserInfo": {"nickname": "学生B昵称"}
                    }
                ]
            }
        }

        results = parse_from_api_response(api_response)

        assert len(results) == 2
        assert results[0]["title"] == "高一(1)班-学生A的投稿"
        assert results[1]["title"] == "高一(2)班-学生B的投稿"

    def test_parse_api_response_skips_invalid(self):
        """测试 API 解析时跳过无效记录"""
        api_response = {
            "code": 200,
            "data": {
                "records": [
                    {
                        "id": 1,
                        "serialNumber": 1,
                        "createTime": "2026-03-14 08:00:00",
                        FIELD_CONTENT: "有效投稿",
                        "wxUserInfo": {}
                    },
                    {
                        "id": 2,
                        "serialNumber": 2,
                        "createTime": "2026-03-14 09:00:00",
                        FIELD_CONTENT: "",
                        "wxUserInfo": {}
                    }
                ]
            }
        }

        results = parse_from_api_response(api_response)

        assert len(results) == 1
        assert results[0]["title"] == "投稿-1"

    def test_wx_openid_from_top_level(self):
        """测试从顶层获取 wx_openid"""
        test_data = {
            "serialNumber": 6,
            FIELD_CONTENT: "测试内容",
            "wxOpenId": "top-level-openid",
            "wxUserInfo": {},
            "createTime": "2026-03-14 12:00:00"
        }

        result = parse_questionnaire(test_data)

        assert result["wx_openid"] == "top-level-openid"

    def test_wx_openid_priority(self):
        """测试 wx_openid 优先从 wxUserInfo 获取"""
        test_data = {
            "serialNumber": 7,
            FIELD_CONTENT: "测试内容",
            "wxOpenId": "top-level-openid",
            "wxUserInfo": {"openid": "userinfo-openid"},
            "createTime": "2026-03-14 12:00:00"
        }

        result = parse_questionnaire(test_data)

        assert result["wx_openid"] == "userinfo-openid"
