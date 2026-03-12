"""
问卷数据解析钩子

【开发组重点修改文件】

这个文件负责将问卷星的原始数据转换为标准格式。
当问卷星的题目或选项有变化时，只需要修改这个文件。

标准输出格式：
{
    "title": "投稿标题",
    "content": "投稿内容（支持Markdown）",
    "author": "作者昵称",
    "tags": ["标签1", "标签2"],  # 可选
    "category": "分类名称"       # 可选
}

使用示例：
    raw_data = {
        "title": "表白墙-我想对小明说",
        "content": "小明，我喜欢你很久了...",
        "author": "匿名",
        "submit_time": "2024-01-01 12:00:00"
    }
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def parse_questionnaire(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析问卷星提交的原始数据

    【修改这里的代码来适配你的问卷】

    问卷星的数据格式可能因问卷配置不同而有差异。
    请根据你实际的问卷题目，修改字段映射关系。

    常见问卷星字段：
    - submit_time: 提交时间
    - respondent_id: 答题者ID
    - 题目1: 题目答案
    - 题目2: 题目答案
    ...

    Args:
        raw_data: 问卷星Webhook发送的原始数据

    Returns:
        标准格式的解析结果

    Raises:
        ValueError: 必要字段缺失
    """
    logger.info("开始解析问卷数据...")

    # ========================================
    # 字段映射配置
    # 【重要】根据你的问卷修改下面的字段名！
    # ========================================

    # 问卷题目对应的字段名（从问卷星后台查看具体字段）
    FIELD_TITLE = "标题"           # 你的问卷中「标题」题目的字段名
    FIELD_CONTENT = "内容"         # 你的问卷中「内容」题目的字段名
    FIELD_AUTHOR = "昵称"          # 你的问卷中「昵称」题目的字段名
    FIELD_TAGS = "标签"            # 你的问卷中「标签」题目的字段名（可选）

    # ========================================
    # 数据提取
    # ========================================

    # 提取标题
    title = raw_data.get(FIELD_TITLE, "")
    if not title:
        # 如果没有标题，用默认格式
        title = f"投稿-{raw_data.get('submit_time', '未知时间')}"

    # 提取内容
    content = raw_data.get(FIELD_CONTENT, "")
    if not content:
        raise ValueError("投稿内容不能为空")

    # 提取作者（可选，默认匿名）
    author = raw_data.get(FIELD_AUTHOR, "匿名")

    # 提取标签（可选）
    tags = []
    raw_tags = raw_data.get(FIELD_TAGS, "")
    if raw_tags:
        # 标签可能是逗号分隔的字符串，转换为列表
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        elif isinstance(raw_tags, list):
            tags = raw_tags

    # ========================================
    # 内容格式化（可选）
    # ========================================

    # 可以在这里对内容进行额外的处理
    # 例如：添加作者信息、转换Markdown、添加水印等

    # 示例：给投稿内容加上作者信息
    formatted_content = f"""
**作者**: {author}

---

{content}

---

> 投稿时间: {raw_data.get('submit_time', '未知')}
> 来源: 问卷星投稿
"""

    # ========================================
    # 返回标准格式
    # ========================================

    result = {
        "title": title,
        "content": formatted_content,
        "author": author,
        "tags": tags,
    }

    logger.info(f"解析完成 - 标题: {title}, 作者: {author}")
    return result


# ========================================
# 调试/测试用
# ========================================

if __name__ == "__main__":
    # 测试解析函数
    test_data = {
        "标题": "表白墙-喜欢上一个女孩",
        "内容": "大家好，我喜欢班里的一个女孩，她叫小红...",
        "昵称": "小明",
        "标签": "表白,情感",
        "submit_time": "2024-01-01 12:00:00"
    }

    result = parse_questionnaire(test_data)
    print("解析结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
