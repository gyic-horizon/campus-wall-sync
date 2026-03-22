# campus-wall-sync 校园墙同步服务

将 tduck 表单收到的投稿自动存入数据库，支持人工/AI 审核，后续可同步到 Halo 博客。

## 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        投稿处理流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  tduck 表单提交                                                  │
│      ↓                                                          │
│  Webhook 触发 → 本服务接收                                        │
│      ↓                                                          │
│  解析表单数据 (questionnaire_parser.py)                           │
│      ↓                                                          │
│  敏感词过滤 (content_filter.py)                                   │
│      ↓                                                          │
│  AI 审核 (ai_review.py，可选)                                     │
│      ↓                                                          │
│  存入数据库 (状态: pending)                                        │
│      ↓                                                          │
│  [后续] 手动/自动同步到 Halo 博客                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```


## 协作分工

```
┌─────────────────────────────────────────────────────────────┐
│                        项目成员                              │
├─────────────────────────┬───────────────────────────────────┤
│      开发组（学生）       │            运维组                  │
│  只改 src/hooks/ 目录    │     只管部署和基础设施              │
│  • 表单解析逻辑           │     • Docker/1Panel               │
│  • 敏感词过滤            │     • 服务器维护                   │
│  • AI审核配置           │     • CI/CD 流水线                 │
│  • 业务流程调整          │     • 监控告警                     │
└─────────────────────────┴───────────────────────────────────┘
```


## 快速开始

### 1. 本地开发（Windows/Mac/Linux）

```bash
# 方式一：Windows 双击运行
run_local.bat

# 方式二：命令行
pip install -r requirements.txt
python -m src.app
```

### 2. 配置服务

复制配置文件并填写配置：

```bash
cp config.json.example config.json
```

编辑 `config.json`：

```json
{
    "app": {
        "debug": true,
        "host": "0.0.0.0",
        "port": 5000
    },
    "database": {
        "path": "data/campus_wall.db",
        "echo": false
    },
    "halo": {
        "api_url": "https://你的Halo博客地址",
        "api_token": "你的API Token"
    },
    "tduck": {
        "enabled": true,
        "api_key": "你的tduck API Key",
        "form_key": "你的表单key",
        "base_url": "https://x.tduckcloud.com"
    },
    "review": {
        "enable_ai_review": false
    }
}
```

### 3. 启动服务

```bash
python -m src.app
```

服务启动后访问：
- 健康检查: http://localhost:5000/health
- tduck Webhook: http://localhost:5000/webhook/tduck
- 投稿列表: http://localhost:5000/api/posts
- 查看字段定义: http://localhost:5000/api/tduck/fields

## API 接口

### 投稿管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/posts` | GET | 获取投稿列表（支持分页、状态筛选） |
| `/api/posts/<id>` | GET | 获取单条投稿详情 |
| `/api/posts/<id>/reject` | POST | 拒绝投稿（标记为 rejected） |
| `/api/posts/sync-to-halo` | POST | 将投稿同步到 Halo 博客 |

### tduck 相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/webhook/tduck` | POST | 接收 tduck Webhook |
| `/api/tduck/sync` | POST | 手动同步 tduck 历史数据 |
| `/api/tduck/fields` | GET | 获取表单字段定义 |

### 测试接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/test/halo` | GET | 测试 Halo 连接 |
| `/test/tduck` | GET | 测试 tduck API 连接 |

## 投稿状态

| 状态 | 说明 |
|------|------|
| `pending` | 待同步到 Halo |
| `synced` | 已同步到 Halo |
| `rejected` | 已拒绝（不再同步） |

## 同步到 Halo

### 方式一：每条投稿创建一篇新文章

```bash
POST /api/posts/sync-to-halo
Content-Type: application/json

{
    "mode": "new"
}
```

### 方式二：合并多条投稿到一篇文章

```bash
POST /api/posts/sync-to-halo
Content-Type: application/json

{
    "mode": "append"
}
```

### 指定投稿 ID 同步

```bash
POST /api/posts/sync-to-halo
Content-Type: application/json

{
    "post_ids": [1, 2, 3],
    "mode": "new"
}
```

## tduck 表单配置

### 1. 获取 API Key

在 tduck 后台 → 对应表单 → 发布 → 数据推送 中获取：
- **API Key**: 用于访问数据同步 API

### 2. 配置 Webhook

在 tduck 后台 → 对应表单 → 发布 → 数据推送 中配置：

- **推送地址**: `http://your-server:5000/webhook/tduck`
- **请求方式**: POST
- **Content-Type**: application/json

### 3. 查看字段定义

启动服务后访问：
```
GET http://localhost:5000/api/tduck/fields
```

返回示例：
```json
{
    "status": "success",
    "fields": [
        {"value": "input1773416359370", "label": "班级", "type": "INPUT"},
        {"value": "input1773416363353", "label": "姓名", "type": "INPUT"},
        {"value": "textarea1773416364971", "label": "投稿内容", "type": "TEXTAREA"}
    ]
}
```

## 开发指南

### 修改业务逻辑

所有业务代码都在 `src/hooks/` 目录下：

| 文件 | 功能 | 修改时机 |
|------|------|----------|
| `questionnaire_parser.py` | 解析 tduck 表单数据 | 表单字段有变化时 |
| `content_filter.py` | 敏感词过滤 | 需要调整审核规则时 |
| `ai_review.py` | AI审核 | 需要接入AI服务时 |

### 配置表单字段映射

**修改 `src/hooks/questionnaire_parser.py`：**

```python
# tduck 表单字段ID（从 /api/tduck/fields 接口查看）
FIELD_CLASS = "input1773416359370"      # 班级字段ID
FIELD_NAME = "input1773416363353"       # 姓名字段ID
FIELD_CONTENT = "textarea1773416364971" # 投稿内容字段ID
```

### 添加敏感词

**修改 `src/hooks/content_filter.py`：**

```python
SENSITIVE_WORDS = [
    "敏感词1",
    "敏感词2",
]
```

## 部署指南（运维组）

### 使用 1Panel + Docker Compose

```bash
# 1. 克隆项目
git clone <仓库地址>
cd campus-wall-sync

# 2. 配置生产环境
cp config.json.example config.json
# 编辑 config.json 填写生产配置

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 数据持久化

数据库文件存储在 `data/campus_wall.db`，已通过 Docker Volume 持久化。

### CI/CD 自动部署

推送到 `main` 分支自动触发部署：
1. 运行测试
2. SSH 到服务器拉取代码
3. 重建 Docker 镜像
4. 重启服务

## 数据库结构

### posts 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | VARCHAR(255) | 投稿标题 |
| content | TEXT | 投稿内容（Markdown） |
| author | VARCHAR(100) | 作者 |
| tags | JSON | 标签列表 |
| status | VARCHAR(20) | 状态（pending/synced/rejected） |
| tduck_id | INTEGER | tduck 记录 ID |
| tduck_serial | INTEGER | tduck 投稿序号 |
| halo_post_id | VARCHAR(50) | Halo 文章 ID |
| created_at | DATETIME | 创建时间 |
| synced_at | DATETIME | 同步时间 |

## License

MIT License
