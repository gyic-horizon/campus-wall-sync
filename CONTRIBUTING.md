# 贡献指南

感谢你对校园墙同步服务的关注！本文档将帮助你了解如何参与项目开发。

---

## 项目结构

```
src/
├── hooks/              # 业务钩子（开发组重点修改）
│   ├── questionnaire_parser.py   # 表单数据解析
│   ├── content_filter.py         # 敏感词过滤
│   └── ai_review.py              # AI 内容审核
├── services/           # 外部服务客户端
│   ├── tduck_client.py           # tduck API 客户端
│   ├── halo_client.py            # Halo 博客 API 客户端
│   └── questionnaire.py          # 问卷服务封装
├── utils/              # 工具模块
├── app.py              # Flask 主入口
├── config.py           # 配置管理
├── database.py         # 数据库连接
└── models.py           # 数据模型
```

---

## 开发原则

### 核心设计原则：**存储原始数据，展示时再处理**

- **数据库只存原始值**，不做格式化
- **动态计算**在模型属性中完成（如 `author`）
- **格式化**在方法中完成（如 `to_markdown()`）

---

## 常见修改场景

### 场景一：数据库加字段

**需要修改三处：**

#### 1. [models.py](src/models.py) - 添加字段定义

```python
class Post(Base):
    # ... 现有字段 ...
    
    # 新增字段
    new_field = Column(String(100), comment="字段说明")
```

#### 2. [questionnaire_parser.py](src/hooks/questionnaire_parser.py) - 提取数据

```python
def parse_questionnaire(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    # ... 现有提取逻辑 ...
    
    # 新增提取
    new_field = raw_data.get("field_key", "").strip() or None
    
    return {
        # ... 现有字段 ...
        "new_field": new_field,
    }
```

#### 3. [app.py](src/app.py) - 存入数据库

找到两处创建 `Post` 的地方（Webhook 处理和手动同步），都加上新字段：

```python
post = Post(
    # ... 现有字段 ...
    new_field=filtered_data.get("new_field"),
)
```

**可选：添加到 `to_dict()` 方法**

如果需要在 API 响应中返回该字段：

```python
def to_dict(self):
    return {
        # ... 现有字段 ...
        "new_field": self.new_field,
    }
```

---

### 场景二：修改表单字段映射

**修改文件：** [questionnaire_parser.py](src/hooks/questionnaire_parser.py)

```python
# ========================================
# tduck 字段映射配置
# ========================================

FIELD_CLASS = "input1773416359370"      # 班级字段ID
FIELD_NAME = "input1773416363353"       # 姓名字段ID
FIELD_CONTENT = "textarea1773416364971" # 投稿内容字段ID
```

**如何获取字段 ID：**

1. 访问 tduck 表单设计器
2. 查看字段属性，复制字段 ID
3. 或使用 API 获取：`GET /tduck-api/sync/form/fields`

---

### 场景三：修改敏感词

**修改文件：** [content_filter.py](src/hooks/content_filter.py)

```python
SENSITIVE_WORDS = [
    # 在这里添加敏感词
    "敏感词1",
    "敏感词2",
    # ...
]
```

---

### 场景四：修改同步到 Halo 的格式

**修改文件：** [models.py](src/models.py) 中的 `to_markdown()` 方法

```python
def to_markdown(self) -> str:
    """
    转换为 Markdown 格式
    """
    meta = (
        f"**作者**：{self.author}\n"
        f"**班级**：{self.class_name or '未填写'}\n"
        # 添加你的自定义格式...
    )
    
    # ... 修改格式 ...
    
    return f"{meta}\n\n---\n\n{self.content}\n\n---\n\n{footer}"
```

---

## 开发流程

### 1. 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp config.json.example config.json

# 编辑配置
notepad config.json

# 启动服务
python -m src.app
```

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_questionnaire_parser.py -v
```

**提交前必须确保所有测试通过！**

### 3. 提交代码

```bash
# 创建分支
git checkout -b feature/your-feature

# 提交更改
git add .
git commit -m "feat: 添加 xxx 功能"

# 推送
git push origin feature/your-feature
```

---

## 代码规范

### Python 代码风格

- 遵循 PEP 8
- 使用 4 空格缩进
- 最大行长度 100 字符
- 函数和类必须有文档字符串

### 文档字符串格式

```python
def my_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    函数简要说明
    
    详细说明（如果需要）
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        返回值说明
    
    Raises:
        ValueError: 什么情况下抛出
    """
    pass
```

---

## 测试规范

### 必须写测试的场景

- 新增解析逻辑
- 新增数据库字段
- 修改核心业务流程

### 测试文件位置

```
tests/
├── test_database.py              # 数据库测试
├── test_questionnaire_parser.py  # 表单解析测试
└── test_content_filter.py        # 敏感词过滤测试（新增）
```

### 测试命名规范

```python
def test_被测试的功能_测试场景():
    """测试描述"""
    pass

# 示例
def test_parse_real_webhook_data():
    """测试真实 Webhook 数据解析"""
    pass

def test_author_property_priority():
    """测试 author 属性的优先级"""
    pass
```

---

## 常见问题

### Q: 数据库结构变了，需要迁移吗？

**A:** 不需要手动迁移。SQLite 会在启动时自动创建新表结构。但注意：

- 旧数据会保留
- 新字段在旧记录中为 `NULL`
- 如需数据迁移，请编写脚本

### Q: 如何调试 Webhook？

**A:** 

1. 使用 ngrok 暴露本地服务：
   ```bash
   ngrok http 5000
   ```

2. 配置 tduck Webhook URL 为 ngrok 地址

3. 查看日志输出

### Q: 如何查看数据库内容？

**A:** 

```bash
# 使用 SQLite CLI
sqlite3 data/campus_wall.db

# 或安装 DB Browser for SQLite（图形界面）
```

---

## 协作方式

### 开发组（学生）

- 只修改 `src/hooks/` 目录
- 修改后运行测试
- 提交 Pull Request

### 运维组

- 负责 `docker-compose.yml`、`Dockerfile`
- 负责 `.github/workflows/`
- 审核并合并 PR

---

## 联系方式

如有问题，请在 GitHub Issues 中提问。

感谢你的贡献！🎉
