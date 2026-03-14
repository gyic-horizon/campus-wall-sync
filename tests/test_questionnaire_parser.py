"""
问卷解析钩子测试 - tduck 表单版本（使用真实 Webhook 数据）
"""

import pytest
from src.hooks.questionnaire_parser import parse_questionnaire, parse_from_api_response


# 模拟 Webhook 数据
REAL_WEBHOOK_DATA = {
    "input1773416359370": "高一十三班",
    "input1773416363353": "小明",
    "textarea1773416364971": "我喜欢小红",
    "dataId": "22c480500000000003de288e992042b3",
    "formKey": "y0ccu2pa",
    "serialNumber": 4,
    "submitUa": {
        "os": {"name": "Android", "version": "15"},
        "ua": "Mozilla/5.0 (Linux; Android 15; NX733J Build/AQ3A.240812.002; wv)...",
    },
    "submitOs": "Android",
    "submitBrowser": "WeChat",
    "submitRequestIp": "111.222.0.333",
    "submitAddress": "广东省-广州市",
    "completeTime": 45527,
    "wxOpenId": "888888888888-EUZO7Orkw1QnMvY",
    "wxUserInfo": {
        "sex": 0,
        "city": "",
        "openid": "888888888888-EUZO7Orkw1QnMvY",
        "country": "",
        "unionId": "oMovy0_0h8Hqck1111111111mSIA",
        "nickname": "xiaoming",
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


class TestQuestionnaireParser:
    """测试 tduck 表单解析功能"""

    def test_parse_real_webhook_data(self):
        """测试真实 Webhook 数据解析"""
        result = parse_questionnaire(REAL_WEBHOOK_DATA)

        assert result["title"] == "高一十三班-小明的投稿"
        assert "我喜欢小红" in result["content"]
        assert result["author"] == "xiaoming"  # 微信昵称
        assert "高一十三班" in result["tags"]
        assert "广东省-广州市" in result["content"]  # 提交地点

    def test_parse_without_wx_nickname(self):
        """测试没有微信昵称时使用姓名"""
        test_data = REAL_WEBHOOK_DATA.copy()
        test_data["wxUserInfo"] = {}  # 空微信信息

        result = parse_questionnaire(test_data)

        assert result["author"] == "小明"  # 使用姓名
        assert "小明的投稿" in result["title"]

    def test_parse_minimal_data(self):
        """测试最小数据（只有内容）"""
        test_data = {
            "serialNumber": 5,
            "createTime": "2026-03-14 11:00:00",
            "textarea1773416364971": "匿名投稿内容",
            "wxUserInfo": {"nickname": ""}
        }

        result = parse_questionnaire(test_data)

        assert "投稿-5" in result["title"]  # 使用序号
        assert result["author"] == "匿名"
        assert result["tags"] == []

    def test_empty_content_raises_error(self):
        """测试空内容应该抛出异常"""
        test_data = REAL_WEBHOOK_DATA.copy()
        test_data["textarea1773416364971"] = ""

        with pytest.raises(ValueError, match="投稿内容不能为空"):
            parse_questionnaire(test_data)

    def test_parse_api_response_format(self):
        """测试 API 响应格式（有 originalData 嵌套）"""
        api_format_data = {
            "id": 623900,
            "serialNumber": 5,
            "createTime": "2026-03-14 10:00:00",
            "originalData": {
                "input1773416359370": "高二(3)班",
                "input1773416363353": "李四",
                "textarea1773416364971": "API格式测试投稿"
            },
            "wxUserInfo": {
                "nickname": "李四同学"
            }
        }

        result = parse_questionnaire(api_format_data)

        assert result["title"] == "高二(3)班-李四的投稿"
        assert "API格式测试投稿" in result["content"]
        assert result["author"] == "李四同学"

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
                        "input1773416359370": "高一(1)班",
                        "input1773416363353": "学生A",
                        "textarea1773416364971": "第一条投稿",
                        "wxUserInfo": {"nickname": "学生A昵称"}
                    },
                    {
                        "id": 2,
                        "serialNumber": 2,
                        "createTime": "2026-03-14 09:00:00",
                        "input1773416359370": "高一(2)班",
                        "input1773416363353": "学生B",
                        "textarea1773416364971": "第二条投稿",
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
                        "textarea1773416364971": "有效投稿",
                        "wxUserInfo": {}
                    },
                    {
                        "id": 2,
                        "serialNumber": 2,
                        "createTime": "2026-03-14 09:00:00",
                        "textarea1773416364971": "",  # 空内容，无效
                        "wxUserInfo": {}
                    }
                ]
            }
        }

        results = parse_from_api_response(api_response)

        assert len(results) == 1  # 只保留有效记录
        assert results[0]["title"] == "投稿-1"

    def test_event_type_field(self):
        """测试 eventType 字段被正确处理"""
        result = parse_questionnaire(REAL_WEBHOOK_DATA)
        
        # 确保解析成功，eventType 不影响解析
        assert result["title"] == "高一十三班-小明的投稿"
        assert "form_data_add" not in result["content"]  # eventType 不应该出现在内容中
