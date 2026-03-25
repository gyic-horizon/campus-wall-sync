"""
AI内容审核钩子

【开发组重点修改文件】（可选功能）

这个文件使用AI对投稿内容进行进一步审核。
可以接入各种AI服务：
- OpenAI API (ChatGPT)
- 阿里云内容审核
- 百度内容审核
- 本地部署的AI模型
- ...

启用方式：在 config.json 中设置 review.enable_ai_review = true

返回格式：
{
    "approved": True/False,     # 是否通过AI审核
    "reason": "审核说明",       # 审核原因
    "confidence": 0.95,         # 置信度（可选）
    "labels": ["标签1", "标签2"] # 检测到的标签（可选）
}

【重要】这个功能默认是禁用的，如果不需要AI审核，
可以在 config.json 中设置 review.enable_ai_review = false
"""

from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


# ========================================
# AI审核配置
# 【重要】在这里配置你的AI服务
# ========================================

# 示例：使用OpenAI API
# OPENAI_API_KEY = "your-api-key"  # 从config.json读取
# OPENAI_MODEL = "gpt-3.5-turbo"

# 示例：使用阿里云内容审核
# ALIYUN_ACCESS_KEY = "your-access-key"
# ALIYUN_ACCESS_SECRET = "your-access-secret"

# ========================================
# 审核提示词（用于调用LLM）
# ========================================

REVIEW_PROMPT = """
你是一个校园墙内容审核助手。请审核以下投稿内容，判断是否适合发布。

审核标准：
1. 内容是否合法合规
2. 内容是否适合校园环境
3. 是否包含广告、垃圾信息
4. 是否包含人身攻击、恶意言论

投稿信息：
- 标题：{title}
- 内容：{content}
- 作者：{author}

请返回JSON格式的审核结果：
{{
    "approved": true/false,
    "reason": "审核原因说明",
    "confidence": 0.0-1.0之间的置信度,
    "labels": ["检测到的标签"]
}}

只返回JSON，不要其他内容。
"""


def review_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用AI审核投稿内容

    【修改这里的代码来接入你的AI服务】

    当前示例实现了：
    1. 简单的规则审核（不需要AI API）
    2. OpenAI API 接入示例（注释中）
    3. 阿里云内容审核接入示例（注释中）

    Args:
        data: 解析后的标准格式数据

    Returns:
        审核结果 {
            "approved": True/False,
            "reason": "审核原因",
            "confidence": 0.95,  # 可选
            "labels": []          # 可选
        }
    """
    logger.info("开始AI内容审核...")

    title = data.get("title", "")
    content = data.get("content", "")
    author = data.get("author", "匿名")

    # ========================================
    # 方式1：简单规则审核（免费，无需API）
    # ========================================
    # 如果不想接入AI，可以使用简单的规则审核
    result = simple_rule_review(title, content, author)
    if result:
        return result

    # ========================================
    # 方式2：使用OpenAI API（需要API Key）
    # ========================================
    # result = openai_review(title, content, author)
    # return result

    # ========================================
    # 方式3：使用阿里云内容审核
    # ========================================
    # result = aliyun_review(title, content)
    # return result

    # 默认通过
    logger.info("AI审核通过")
    return {
        "approved": True,
        "reason": "内容审核通过"
    }


def simple_rule_review(title: str, content: str, author: str) -> Dict[str, Any]:
    """
    简单的规则审核（不需要AI API）

    基于简单规则的快速审核，适合作为第一层过滤。

    Args:
        title: 标题
        content: 内容
        author: 作者

    Returns:
        审核结果，如果没有触发规则返回None
    """
    # 检查内容长度
    if len(content) < 10:
        return {
            "approved": False,
            "reason": "内容过短，不符合发布要求"
        }

    if len(content) > 10000:
        return {
            "approved": False,
            "reason": "内容过长，请精简后重试"
        }

    # 检查是否包含链接（可防止垃圾广告）
    # 如果需要允许链接，注释掉下面几行
    # if "http://" in content or "https://" in content:
    #     return {
    #         "approved": False,
    #         "reason": "投稿中不允许包含外部链接"
    #     }

    # 检查是否包含联系方式（防止私下交易）
    phone_pattern = r"1[3-9]\d{9}"
    if len(content) > 50:  # 内容较长时才检查，避免误伤
        if re.search(phone_pattern, content):
            return {
                "approved": False,
                "reason": "投稿中包含疑似电话号码，请移除后重试"
            }

    # 所有规则都通过
    return None


def openai_review(title: str, content: str, author: str) -> Dict[str, Any]:
    """
    使用OpenAI API进行内容审核

    【使用前先安装openai库: pip install openai】

    Args:
        title: 标题
        content: 内容
        author: 作者

    Returns:
        审核结果
    """
    try:
        from openai import OpenAI

        # 从配置获取API Key
        from src.config import config
        review_config = config.review
        api_key = review_config.get("openai_api_key", "")

        if not api_key:
            logger.warning("未配置OpenAI API Key，跳过AI审核")
            return {"approved": True, "reason": "未配置AI审核"}

        client = OpenAI(api_key=api_key)

        # 构建提示词
        prompt = REVIEW_PROMPT.format(
            title=title,
            content=content[:2000],  # 限制长度
            author=author
        )

        # 调用API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个严格的内容审核助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        # 解析结果
        result_text = response.choices[0].message.content.strip()

        # 尝试解析JSON
        import json
        result = json.loads(result_text)

        logger.info(f"OpenAI审核结果: {result}")
        return result

    except ImportError:
        logger.warning("未安装openai库，跳过AI审核")
        return {"approved": True, "reason": "未安装AI审核库"}
    except Exception as e:
        logger.error(f"OpenAI审核失败: {str(e)}", exc_info=True)
        return {"approved": True, "reason": f"AI审核服务异常: {str(e)}"}


def aliyun_review(title: str, content: str) -> Dict[str, Any]:
    """
    使用阿里云内容审核API

    【使用前先安装阿里云SDK: pip install aliyun-python-sdk-core aliyun-python-sdk-green】

    Args:
        title: 标题
        content: 内容

    Returns:
        审核结果
    """
    # 这里需要阿里云账号配置，请参考阿里云文档
    # 暂时返回空实现
    logger.info("阿里云内容审核功能待实现")
    return {"approved": True, "reason": "待配置"}


if __name__ == "__main__":
    # 测试代码
    test_data = {
        "title": "表白墙-测试投稿",
        "content": "这是一条测试投稿内容，用于验证审核功能是否正常工作。",
        "author": "测试用户"
    }

    result = review_content(test_data)
    print("AI审核结果:")
    print(f"  通过: {result['approved']}")
    print(f"  原因: {result['reason']}")
    if "confidence" in result:
        print(f"  置信度: {result['confidence']}")
