"""
Halo博客API客户端

封装与Halo博客系统的交互，包括：
- 测试连接
- 创建文章
- 更新文章
- 删除文章

Halo API文档: https://halo.run/docs/1.5.0/developer-guide/server/api
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from src.config import config


class HaloClient:
    """
    Halo博客API客户端

    使用Halo的REST API进行文章管理。
    配置信息从 config.json 的 halo 部分读取。
    """

    def __init__(self):
        """从配置初始化Halo客户端"""
        halo_config = config.halo

        # API配置
        self.api_url = halo_config.get("api_url", "")
        self.api_token = halo_config.get("api_token", "")
        self.site_name = halo_config.get("site_name", "default")

        # 请求超时设置
        self.timeout = halo_config.get("timeout", 30)

        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        self.logger = logging.getLogger(__name__)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到Halo API

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点路径
            data: 请求体数据

        Returns:
            JSON响应数据

        Raises:
            requests.RequestException: 请求失败时抛出异常
        """
        url = f"{self.api_url}{endpoint}"
        self.logger.debug(f"请求 Halo API: {method} {url}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Halo API请求失败: {str(e)}", exc_info=True)
            raise

    def test_connection(self) -> Dict[str, Any]:
        """
        测试Halo博客连接

        Returns:
            连接状态信息
        """
        try:
            # 尝试获取站点信息来验证连接
            result = self._make_request("GET", "/api/v1alpha1/sites/current")
            return {
                "status": "connected",
                "site_name": result.get("name", "unknown"),
                "api_url": self.api_url
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def create_post(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        status: str = "PUBLISHED"
    ) -> Dict[str, Any]:
        """
        创建新文章

        Args:
            title: 文章标题
            content: 文章内容（支持Markdown）
            tags: 文章标签列表
            category: 文章分类
            status: 发布状态 (PUBLISHED, DRAFT)

        Returns:
            创建的文章信息，包含id

        Raises:
            requests.RequestException: 创建失败时抛出异常
        """
        # 构建文章数据
        post_data = {
            "title": title,
            "content": {
                "raw": content,
                "html": content  # Halo会自动转换，这里可以留空
            },
            "status": status,
        }

        # 添加分类
        if category:
            post_data["category"] = {"name": category}

        # 添加标签
        if tags:
            post_data["tags"] = [{"name": tag} for tag in tags]

        self.logger.info(f"正在创建文章: {title}")

        result = self._make_request("POST", "/api/v1alpha1/posts", post_data)

        self.logger.info(f"文章创建成功，ID: {result.get('id')}")
        return result

    def update_post(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新现有文章

        Args:
            post_id: 文章ID
            title: 新标题（可选）
            content: 新内容（可选）
            status: 新状态（可选）

        Returns:
            更新后的文章信息
        """
        update_data = {}
        if title:
            update_data["title"] = title
        if content:
            update_data["content"] = {"raw": content, "html": content}
        if status:
            update_data["status"] = status

        self.logger.info(f"正在更新文章，ID: {post_id}")

        result = self._make_request(
            "PUT",
            f"/api/v1alpha1/posts/{post_id}",
            update_data
        )

        self.logger.info(f"文章更新成功，ID: {post_id}")
        return result

    def delete_post(self, post_id: str) -> bool:
        """
        删除文章

        Args:
            post_id: 文章ID

        Returns:
            是否删除成功
        """
        try:
            self._make_request("DELETE", f"/api/v1alpha1/posts/{post_id}")
            self.logger.info(f"文章删除成功，ID: {post_id}")
            return True
        except Exception as e:
            self.logger.error(f"文章删除失败: {str(e)}", exc_info=True)
            return False
