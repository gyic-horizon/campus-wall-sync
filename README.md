# campus-wall-sync 校园墙同步服务

将 tduck 表单收到的投稿自动同步到 Halo 博客，支持人工/AI 审核。

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

**重要：开发组不需要会 Docker，只需要会 Python 和 Git！**

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
- 查看字段定义: http://localhost:5000/api/tduck/fields

## tduck 表单配置

### 1. 获取 API Key

在 tduck 后台 → 表单设置 → API 设置 中获取：
- **API Key**: 用于访问数据同步 API
- **Form Key**: 表单唯一标识

### 2. 配置 Webhook

在 tduck 后台 → 表单设置 → Webhook 推送：

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
# ========================================
# tduck 字段映射配置
# 【重要】根据你的 tduck 表单修改下面的字段ID！
# ========================================

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
    # 添加更多...
]
```

### 数据同步 API

#### 手动同步历史数据

```bash
# 同步所有数据
POST http://localhost:5000/api/tduck/sync

# 同步指定时间范围的数据
POST http://localhost:5000/api/tduck/sync
Content-Type: application/json

{
    "start_time": "2026-03-01 00:00:00",
    "end_time": "2026-03-14 23:59:59"
}
```

#### tduck 数据同步 API 说明

- **字段同步 API**: `GET /tduck-api/sync/form/fields?apiKey=xxx`
- **全量数据同步 API**: `GET /tduck-api/sync/form/data?apiKey=xxx&page=1&size=10`

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

### CI/CD 自动部署

推送到 `main` 分支自动触发部署：
1. 运行测试
2. 构建 Docker 镜像
3. 部署到服务器

## 目录结构

```
campus-wall-sync/
├── src/                      # 源代码
│   ├── app.py               # Flask 主入口
│   ├── config.py            # 配置管理
│   ├── services/            # 服务层
│   │   ├── halo_client.py   # Halo API 客户端
│   │   └── tduck_client.py  # tduck API 客户端
│   ├── hooks/               # 【业务钩子】开发组主要修改这里
│   │   ├── questionnaire_parser.py
│   │   ├── content_filter.py
│   │   └── ai_review.py
│   └── utils/               # 工具函数
│       └── logger.py
├── tests/                   # 测试代码
├── docker-compose.yml       # Docker 部署配置
├── Dockerfile               # Docker 镜像
├── requirements.txt         # Python 依赖
├── run_local.bat           # 本地启动脚本
└── config.json.example     # 配置示例
```

## API 端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/webhook/tduck` | POST | tduck Webhook 接收 |
| `/api/tduck/fields` | GET | 获取表单字段定义 |
| `/api/tduck/sync` | POST | 手动触发数据同步 |
| `/test/halo` | GET | 测试 Halo 连接 |
| `/test/tduck` | GET | 测试 tduck 连接 |

## 常见问题

**Q: 开发组需要会 Docker 吗？**
A: 不需要！开发组只需要修改 `src/hooks/` 下的业务代码，部署由运维组负责。

**Q: 如何测试我的代码修改？**
A: 本地运行 `python -m src.app`，然后用 curl 测试 webhook 接口。

**Q: 如何连接测试环境的 Halo？**
A: 修改 `config.json` 中的 `halo.api_url` 和 `halo.api_token` 即可。

**Q: tduck 的字段 ID 在哪里查看？**
A: 启动服务后访问 `http://localhost:5000/api/tduck/fields`，或查看 tduck 后台的表单设计器。

**Q: 如何从问卷星迁移到 tduck？**
A: 
1. 在 tduck 创建新表单
2. 更新 `config.json` 中的 tduck 配置
3. 修改 `questionnaire_parser.py` 中的字段映射
4. 使用 `/api/tduck/sync` 接口同步历史数据

## 技术栈

- **后端**: Python 3.11 + Flask
- **部署**: Docker + 1Panel
- **CI/CD**: GitHub Actions
- **博客系统**: Halo
- **表单系统**: tduck

## 许可证

MIT License
