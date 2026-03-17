"""
敏感词过滤钩子

这个文件负责审核投稿内容，过滤敏感信息。
你可以：
1. 使用简单的敏感词列表
2. 接入第三方敏感词库
3. 使用正则表达式匹配

返回格式：
{
    "passed": True/False,      # 是否通过审核
    "reason": "拒绝原因",      # 如果未通过，说明原因
    "content": "过滤后的内容"   # 处理后的内容（可选）
}

敏感词示例列表（根据实际需求添加）：
- 政治敏感词
- 色情低俗词
- 暴力血腥词
- 广告推广词
- ...
"""

from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)


# ========================================
# 敏感词配置
# 【重要】在这里添加你的敏感词
# ========================================

# 简单敏感词列表（实际使用建议用第三方库或数据库）
SENSITIVE_WORDS = [
    # 政治相关（示例，实际根据需求配置）
    "敏感词1",
    "敏感词2",
    # 色情低俗
    "垃圾广告",
    "赌博",
    # 其他违规词...
]

# 是否启用敏感词替换（替换为***）还是直接拒绝
REPLACE_MODE = True  # True=替换为***, False=直接拒绝


def filter_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    过滤投稿内容中的敏感词

    【修改这里的代码来实现你的审核逻辑】

    Args:
        data: 解析后的结构化数据

    Returns:
        审核结果 {
            "passed": True/False,
            "reason": "如果未通过，说明原因",
            "data": 处理后的数据（如果启用替换）
        }
    """
    logger.info("开始敏感词过滤...")

    title = data.get("title", "")
    content = data.get("content", "")
    wx_openid = data.get("wx_openid", "")

    # 检查用户是否在黑名单（使用 wx_openid）
    if wx_openid and check_user_blacklist(wx_openid):
        logger.warning(f"用户 {wx_openid} 在黑名单中")
        return {
            "passed": False,
            "reason": "该用户已被加入黑名单"
        }

    # 检查标题
    title_check = check_sensitive_words(title)
    if not title_check["passed"]:
        logger.warning(f"标题包含敏感词: {title_check['matched']}")
        return {
            "passed": False,
            "reason": f"标题包含敏感词: {title_check['matched']}"
        }

    # 检查内容
    content_check = check_sensitive_words(content)
    if not content_check["passed"]:
        logger.warning(f"内容包含敏感词: {content_check['matched']}")
        return {
            "passed": False,
            "reason": f"内容包含敏感词: {content_check['matched']}"
        }

    # 如果启用替换模式，返回替换后的内容
    filtered_data = data.copy()
    if REPLACE_MODE:
        filtered_data["content"] = content_check.get("filtered", content)

    logger.info("敏感词过滤通过")
    return {
        "passed": True,
        "data": filtered_data
    }


def check_sensitive_words(text: str) -> Dict[str, Any]:
    """
    检查文本中的敏感词

    Args:
        text: 待检查的文本

    Returns:
        检查结果 {
            "passed": True/False,
            "matched": "匹配到的敏感词（可选）",
            "filtered": "替换后的文本（仅替换模式）"
        }
    """
    if not text:
        return {"passed": True}

    matched_words = []

    # 遍历敏感词列表
    for word in SENSITIVE_WORDS:
        if word in text:
            matched_words.append(word)

    if matched_words:
        if REPLACE_MODE:
            # 替换模式：把敏感词替换为***
            filtered_text = text
            for word in matched_words:
                filtered_text = filtered_text.replace(word, "***")
            return {
                "passed": True,  # 替换后通过
                "matched": ", ".join(matched_words),
                "filtered": filtered_text
            }
        else:
            # 拒绝模式
            return {
                "passed": False,
                "matched": ", ".join(matched_words)
            }

    return {"passed": True}


def check_user_blacklist(wx_openid: str) -> bool:
    """
    检查用户是否在黑名单

    Args:
        wx_openid: 微信 openid

    Returns:
        是否在黑名单
    """
    # 黑名单列表（可以改成从数据库读取）
    blacklist = []

    return wx_openid in blacklist


# ========================================
# 高级功能（可选）
# ========================================

def load_sensitive_words_from_file(filepath: str) -> List[str]:
    """
    从文件加载敏感词列表

    适用于敏感词词库较大的情况。
    文件格式：每行一个敏感词

    Args:
        filepath: 敏感词文件路径

    Returns:
        敏感词列表
    """
    words = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
        logger.info(f"从文件加载了 {len(words)} 个敏感词")
    except FileNotFoundError:
        logger.warning(f"敏感词文件不存在: {filepath}")

    return words


if __name__ == "__main__":
    # 测试代码
    test_data = {
        "title": "表白墙-今天天气真好",
        "content": "大家好，我想发个投稿，这是一条垃圾广告内容",
        "author": "小明"
    }

    result = filter_content(test_data)
    print("审核结果:")
    print(f"  通过: {result['passed']}")
    if not result["passed"]:
        print(f"  原因: {result['reason']}")
    if "data" in result:
        print(f"  处理后内容: {result['data'][:50]}...")
