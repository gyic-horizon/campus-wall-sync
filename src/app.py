"""
Flask 主入口

校园墙同步服务的HTTP入口，处理 tduck Webhook 并同步到 Halo 博客。

工作流程：
1. tduck 收到投稿 -> 触发 Webhook -> 本服务接收
2. 调用 hooks/questionnaire_parser 解析表单数据
3. 调用 hooks/content_filter 进行敏感词过滤
4. 调用 hooks/ai_review 进行AI审核（可选）
5. 审核通过 -> 调用 Halo API 发布到博客
6. 审核不通过 -> 记录日志，等待人工处理
"""

import json
import logging
from flask import Flask, request, jsonify
from src.config import config
from src.services.tduck_client import TduckClient
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
    tduck_client = TduckClient()
    halo_client = HaloClient()

    # ========================================
    # 路由定义
    # ========================================

    @app.route("/health", methods=["GET"])
    def health_check():
        """健康检查接口，供运维监控系统调用"""
        return jsonify({"status": "ok", "service": "campus-wall-sync"})

    @app.route("/webhook/tduck", methods=["POST"])
    def handle_tduck_webhook():
        """
        tduck Webhook 处理接口

        接收 tduck 的投稿数据，依次经过：
        1. 验证 Webhook 数据格式
        2. 解析表单数据（hooks/questionnaire_parser.py）
        3. 敏感词过滤（hooks/content_filter.py）
        4. AI审核（hooks/ai_review.py，可选）
        5. 发布到 Halo 博客

        tduck Webhook 配置：
        - URL: http://your-server:5000/webhook/tduck
        - Method: POST
        - Content-Type: application/json
        """
        logger.info("收到 tduck Webhook 请求")

        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                logger.warning("Webhook 请求体为空")
                return jsonify({"error": "请求体为空"}), 400

            # ========== 步骤1: 验证数据格式 ==========
            if not tduck_client.validate_webhook_payload(data):
                logger.warning("Webhook 数据格式验证失败")
                return jsonify({"error": "数据格式无效"}), 400

            logger.info(f"接收到 tduck 投稿，ID: {data.get('id')}, 序号: {data.get('serialNumber')}")

            # ========== 步骤2: 解析表单数据 ==========
            from src.hooks.questionnaire_parser import parse_questionnaire

            parsed_data = parse_questionnaire(data)
            logger.info(f"解析后的数据 - 标题: {parsed_data['title']}, 作者: {parsed_data['author']}")

            # ========== 步骤3: 敏感词过滤 ==========
            from src.hooks.content_filter import filter_content

            filtered_data = filter_content(parsed_data)
            if not filtered_data["passed"]:
                logger.warning(f"内容未通过敏感词过滤: {filtered_data['reason']}")
                return jsonify({
                    "status": "filtered",
                    "reason": filtered_data["reason"]
                }), 200

            # ========== 步骤4: AI审核（可选） ==========
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

            # ========== 步骤5: 发布到 Halo ==========
            halo_result = halo_client.create_post(
                title=filtered_data["title"],
                content=filtered_data["content"],
                tags=filtered_data.get("tags", [])
            )

            logger.info(f"成功发布到 Halo 博客，Post ID: {halo_result.get('id')}")
            return jsonify({
                "status": "success",
                "message": "投稿已成功发布",
                "halo_post_id": halo_result.get("id"),
                "title": filtered_data["title"]
            }), 200

        except ValueError as e:
            # 数据验证错误
            logger.warning(f"数据验证失败: {str(e)}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(f"处理 Webhook 时发生错误: {str(e)}", exc_info=True)
            return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

    @app.route("/api/tduck/sync", methods=["POST"])
    def sync_tduck_data():
        """
        手动触发 tduck 数据同步

        从 tduck API 获取所有表单数据并同步到 Halo 博客。
        用于首次迁移或补同步历史数据。

        Request Body (可选):
        {
            "start_time": "2026-03-01 00:00:00",
            "end_time": "2026-03-14 23:59:59"
        }
        """
        logger.info("收到手动同步请求")

        try:
            # 获取请求参数
            body = request.get_json(silent=True) or {}
            start_time = body.get("start_time")
            end_time = body.get("end_time")

            # 从 tduck API 获取数据
            if start_time or end_time:
                data = tduck_client.get_form_data(
                    page=1,
                    size=1000,
                    start_time=start_time,
                    end_time=end_time
                )
                records = data.get("records", [])
            else:
                records = tduck_client.get_all_form_data()

            logger.info(f"获取到 {len(records)} 条记录，开始同步...")

            # 解析并同步数据
            from src.hooks.questionnaire_parser import parse_questionnaire
            from src.hooks.content_filter import filter_content

            success_count = 0
            skip_count = 0
            error_count = 0

            for record in records:
                try:
                    # 解析数据
                    parsed_data = parse_questionnaire(record)

                    # 敏感词过滤
                    filtered_data = filter_content(parsed_data)
                    if not filtered_data["passed"]:
                        logger.warning(f"跳过记录 {record.get('id')}: 未通过敏感词过滤")
                        skip_count += 1
                        continue

                    # 发布到 Halo
                    halo_client.create_post(
                        title=filtered_data["title"],
                        content=filtered_data["content"],
                        tags=filtered_data.get("tags", [])
                    )

                    success_count += 1
                    logger.info(f"成功同步记录 {record.get('id')}: {filtered_data['title']}")

                except ValueError as e:
                    logger.warning(f"跳过无效记录 {record.get('id')}: {e}")
                    skip_count += 1

                except Exception as e:
                    logger.error(f"同步记录 {record.get('id')} 失败: {e}")
                    error_count += 1

            return jsonify({
                "status": "completed",
                "total": len(records),
                "success": success_count,
                "skipped": skip_count,
                "error": error_count
            }), 200

        except Exception as e:
            logger.error(f"同步数据时发生错误: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tduck/fields", methods=["GET"])
    def get_tduck_fields():
        """
        获取 tduck 表单字段定义

        用于查看表单字段ID，方便配置 questionnaire_parser.py
        """
        try:
            fields = tduck_client.get_form_fields()
            return jsonify({
                "status": "success",
                "fields": [
                    {
                        "value": f.get("value"),
                        "label": f.get("label"),
                        "type": f.get("type")
                    }
                    for f in fields
                ]
            }), 200

        except Exception as e:
            logger.error(f"获取字段定义失败: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/test/halo", methods=["GET"])
    def test_halo_connection():
        """测试 Halo 博客连接"""
        try:
            result = halo_client.test_connection()
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/test/tduck", methods=["GET"])
    def test_tduck_connection():
        """测试 tduck API 连接"""
        try:
            fields = tduck_client.get_form_fields()
            return jsonify({
                "status": "ok",
                "message": f"成功连接到 tduck API，表单包含 {len(fields)} 个字段"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # 保留旧接口兼容（可选）
    @app.route("/webhook/questionnaire", methods=["POST"])
    def handle_questionnaire_webhook_legacy():
        """兼容旧版问卷星 Webhook 接口（已弃用）"""
        logger.warning("收到旧版问卷星 Webhook 请求，请迁移到 /webhook/tduck")
        return jsonify({
            "error": "已弃用",
            "message": "请使用新的 Webhook 端点: /webhook/tduck"
        }), 410

    return app


# ========================================
# 应用启动入口
# ========================================

def main():
    """主函数，启动 Flask 应用"""
    app = create_app()
    app_config = config.app

    host = app_config.get("host", "0.0.0.0")
    port = app_config.get("port", 5000)
    debug = app_config.get("debug", False)

    print(f"[启动] 校园墙同步服务正在启动...")
    print(f"[启动] 监听地址: http://{host}:{port}")
    print(f"[启动] tduck Webhook: http://{host}:{port}/webhook/tduck")
    print(f"[启动] 健康检查: http://{host}:{port}/health")

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
