# campus-wall-sync 校园墙同步服务

将问卷星收到的投稿自动同步到 Halo 博客，支持人工/AI 审核。

## 协作分工

```
┌─────────────────────────────────────────────────────────────┐
│                        项目成员                              │
├─────────────────────────┬───────────────────────────────────┤
│      开发组（学生）       │            运维组                  │
│  只改 src/hooks/ 目录    │     只管部署和基础设施              │
│  • 问卷解析逻辑           │     • Docker/1Panel               │
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
    "questionnaire": {
        "webhook_token": "问卷星Webhook Token"
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
- 问卷Webhook: http://localhost:5000/webhook/questionnaire

## 开发指南

### 修改业务逻辑

所有业务代码都在 `src/hooks/` 目录下：

| 文件 | 功能 | 修改时机 |
|------|------|----------|
| `questionnaire_parser.py` | 解析问卷数据 | 问卷题目有变化时 |
| `content_filter.py` | 敏感词过滤 | 需要调整审核规则时 |
| `ai_review.py` | AI审核 | 需要接入AI服务时 |

### 开发示例

**修改问卷解析逻辑：**

```python
# src/hooks/questionnaire_parser.py

# 修改字段映射
FIELD_TITLE = "你的标题字段名"
FIELD_CONTENT = "你的内容字段名"
```

**添加敏感词：**

```python
# src/hooks/content_filter.py

SENSITIVE_WORDS = [
    "敏感词1",
    "敏感词2",
    # 添加更多...
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
│   │   └── questionnaire.py # 问卷服务
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

## 常见问题

**Q: 开发组需要会 Docker 吗？**
A: 不需要！开发组只需要修改 `src/hooks/` 下的业务代码，部署由运维组负责。

**Q: 如何测试我的代码修改？**
A: 本地运行 `python -m src.app`，然后用 curl 测试 webhook 接口。

**Q: 如何连接测试环境的 Halo？**
A: 修改 `config.json` 中的 `halo.api_url` 和 `halo.api_token` 即可。

## 技术栈

- **后端**: Python 3.11 + Flask
- **部署**: Docker + 1Panel
- **CI/CD**: GitHub Actions
- **博客系统**: Halo
- **问卷系统**: 问卷星

## 许可证

MIT License
