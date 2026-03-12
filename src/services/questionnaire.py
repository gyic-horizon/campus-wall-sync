"""
问卷星Webhook数据解析服务

负责接收和解析问卷星推送的数据。
这里是服务层代码，解析逻辑的具体实现放在了 hooks/ 目录下，方便业务定制。

问卷星Webhook说明：
- 问卷星会在用户提交问卷后发送POST请求到配置的URL
- 请求体包含问卷的答案数据
- 不同问卷的字段不同，需要解析
"""

import logging
from typing import Dict, Any, List
from src.config import config


class QuestionnaireService:
    """
    问卷星数据解析服务

    将问卷星的原始Webhook数据转换为标准格式，
    然后调用 hooks/questionnaire_parser.py 进行具体解析。
    """

    def __init__(self):
        """初始化问卷服务"""
        self.config = config.questionnaire
        self.logger = logging.getLogger(__name__)

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析问卷星Webhook数据

        这里做一个简单的数据验证和格式转换，
        具体的问卷字段解析逻辑在 hooks/questionnaire_parser.py 中。

        Args:
            raw_data: 问卷星发送的原始数据

        Returns:
            解析后的标准格式数据 {
                "title": "投稿标题",
                "content": "投稿内容",
                "author": "作者名",
                "tags": ["标签1", "标签2"],
                "raw": 原始数据（保留用于调试）
            }

        Raises:
            ValueError: 数据格式错误
        """
        self.logger.info("开始解析问卷数据")

        # 验证基础数据结构
        if not raw_data:
            raise ValueError("问卷数据为空")

        # 导入具体的解析逻辑（业务钩子）
        # 开发组只需要修改 hooks/questionnaire_parser.py 中的实现
        from src.hooks.questionnaire_parser import parse_questionnaire

        # 调用业务钩子进行解析
        parsed_data = parse_questionnaire(raw_data)

        # 添加原始数据（用于问题排查）
        parsed_data["raw"] = raw_data

        self.logger.info(f"问卷解析完成: {parsed_data.get('title', '无标题')}")
        return parsed_data

    def validate_signature(self, payload: str, signature: str) -> bool:
        """
        验证请求签名（安全性检查）

        问卷星会提供签名用于验证请求来源。
        这里做个示例，实际配置请参考问卷星文档。

        Args:
            payload: 请求体内容
            signature: 签名串

        Returns:
            签名是否有效
        """
        token = self.config.get("webhook_token", "")

        if not token:
            self.logger.warning("未配置Webhook Token，跳过签名验证")
            return True

        # 这里应该实现实际的签名验证逻辑
        # 问卷星的签名算法请参考其官方文档
        # 示例: import hmac, hashlib
        # expected = hmac.new(token.encode(), payload.encode(), hashlib.sha256).hexdigest()

        return True
