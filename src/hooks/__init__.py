"""
业务钩子目录

【重要】这是开发组主要修改的目录！

这个目录包含了所有业务逻辑的「钩子」，开发同学只需要修改这些文件，
不需要了解Docker、部署、基础设施等细节。

目录结构：
- questionnaire_parser.py: 问卷数据解析（如何从问卷星数据中提取标题、内容）
- content_filter.py: 敏感词过滤（审核逻辑）
- ai_review.py: AI审核（可选，使用AI进行内容审核）

每个文件都有详细的注释和示例代码，适合学习。
"""

#新手 导出所有钩子函数，方便导入
from src.hooks.questionnaire_parser import parse_questionnaire
from src.hooks.content_filter import filter_content
from src.hooks.ai_review import review_content

__all__ = [
    "parse_questionnaire",
    "filter_content",
    "review_content",
]
