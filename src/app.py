"""
Flask 主入口

校园墙同步服务的HTTP入口，处理问卷星WebHook并同步到Halo博客。

工作流程：
1. 问卷星收到投稿 -> 触发Webhook -> 本服务接收
2. 调用 hooks/questionnaire_parser 解析问卷数据
3. 调用 hooks/content_filter 进行敏感词过滤
4. 调用 hooks/ai_review 进行AI审核（可选）
5. 审核通过 -> 调用 Halo API 发布到博客
6. 审核不通过 -> 记录日志，等待人工处理
"""

import json
import logging
from flask import Flask, request, jsonify
from src.config import config
from src.services.questionnaire import QuestionnaireService
from src.services.halo_client import HaloClient
from src.utils.logger import setup_logger


def create_app() -> Flask:
    """
    Flask应用工厂函数

    创建并配置Flask应用，注册路由和钩子。
    这里只做基础设施配置，业务逻辑都在 hooks/ 目录下。
    """
    app = Flask(__name__)

    # 从配置读取应用设置
    app_config = config.app
    app.config["DEBUG"] = app_config.get("debug", False)
    app.config["HOST"] = app_config.get("host", "0.0.0.0")
    app.config["PORT"] = app_config.get("port", 5000)

    # 设置日志
    setup_logger(app_config.get("log_level", "INFO"))
    logger = logging.getLogger(__name__)

    # 初始化服务
    questionnaire_service = QuestionnaireService()
    halo_client = HaloClient()

    # ========================================
    # 路由定义
    # ========================================

    @app.route("/health", methods=["GET"])
    def health_check():
        """健康检查接口，供运维监控系统调用"""
        return jsonify({"status": "ok", "service": "campus-wall-sync"})

    @app.route("/webhook/questionnaire", methods=["POST"])
    def handle_questionnaire_webhook():
        """
        问卷星Webhook处理接口

        接收问卷星的投稿数据，依次经过：
        1. 解析问卷数据（hooks/questionnaire_parser.py）
        2. 敏感词过滤（hooks/content_filter.py）
        3. AI审核（hooks/ai_review.py，可选）
        4. 发布到Halo博客
        """
        logger.info("收到问卷星Webhook请求")

        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求体为空"}), 400

            # ========== 步骤1: 解析问卷数据 ==========
            # 这里调用业务钩子，不同问卷格式只需要修改 parser
            parsed_data = questionnaire_service.parse(data)
            logger.info(f"解析后的数据: {parsed_data}")

            # ========== 步骤2: 敏感词过滤 ==========
            # 导入业务钩子模块
            from src.hooks.content_filter import filter_content

            filtered_data = filter_content(parsed_data)
            if not filtered_data["passed"]:
                logger.warning(f"内容未通过敏感词过滤: {filtered_data['reason']}")
                return jsonify({
                    "status": "filtered",
                    "reason": filtered_data["reason"]
                }), 200

            # ========== 步骤3: AI审核（可选） ==========
            # 只有开启AI审核时才调用
            review_config = config.review
            if review_config.get("enable_ai_review", False):
                from src.hooks.ai_review import review_content

                review_result = review_content(filtered_data["content"])
                if not review_result["approved"]:
                    logger.warning(f"内容未通过AI审核: {review_result['reason']}")
                    return jsonify({
                        "status": "pending_review",
                        "reason": review_result["reason"]
                    }), 200

            # ========== 步骤4: 发布到Halo ==========
            halo_result = halo_client.create_post(
                title=filtered_data["title"],
                content=filtered_data["content"],
                tags=filtered_data.get("tags", [])
            )

            logger.info(f"成功发布到Halo博客，Post ID: {halo_result.get('id')}")
            return jsonify({
                "status": "success",
                "halo_post_id": halo_result.get("id")
            }), 200

        except Exception as e:
            logger.error(f"处理Webhook时发生错误: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/test/halo", methods=["GET"])
    def test_halo_connection():
        """测试Halo博客连接"""
        try:
            result = halo_client.test_connection()
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# ========================================
# 应用启动入口
# ========================================

def main():
    """主函数，启动Flask应用"""
    app = create_app()
    app_config = config.app

    host = app_config.get("host", "0.0.0.0")
    port = app_config.get("port", 5000)
    debug = app_config.get("debug", False)

    print(f"[启动] 校园墙同步服务正在启动...")
    print(f"[启动] 监听地址: http://{host}:{port}")
    print(f"[启动] Webhook端点: http://{host}:{port}/webhook/questionnaire")

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
