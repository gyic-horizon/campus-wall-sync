#!/bin/bash
# ========================================
# 校园墙同步服务 - Linux 启动脚本
#
# 功能：自动检查环境、安装依赖并启动服务
# 使用：chmod +x run_local.sh && ./run_local.sh
# ========================================

set -e  # 遇到错误立即退出

echo "========================================"
echo "  校园墙同步服务 - Linux 启动脚本"
echo "========================================"

# 检查 Python 版本
echo "[1/5] 检查 Python 版本..."
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到 Python，请先安装 Python 3"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1)
if [ "$python_version" -lt 3 ]; then
    echo "错误: 需要 Python 3.x，当前版本为 $($PYTHON_CMD --version)"
    exit 1
fi
echo "  Python 版本检查通过: $($PYTHON_CMD --version)"

# 检查 pip
echo "[1.5/5] 检查 pip..."
PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "错误: 未找到 pip，请先安装 pip"
    echo "  可使用以下命令安装:"
    echo "    $PYTHON_CMD -m ensurepip --upgrade"
    echo "    或: sudo apt install python3-pip  (Debian/Ubuntu)"
    echo "    或: sudo yum install python3-pip  (CentOS/RHEL)"
    exit 1
fi
echo "  使用: $PIP_CMD"

# 获取脚本所在目录（支持软链接）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[2/5] 创建 Python 虚拟环境..."
    $PYTHON_CMD -m venv venv
    echo "  虚拟环境创建完成"
else
    echo "[2/5] 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "[3/5] 激活虚拟环境..."
source venv/bin/activate
echo "  虚拟环境已激活 ($(which python))"

# 安装项目依赖
echo "[4/5] 安装项目依赖..."
$PIP_CMD install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt -q
    echo "  依赖安装完成"
else
    echo "  警告: requirements.txt 不存在，跳过依赖安装"
fi

# 检查配置文件
echo "[5/5] 检查配置文件..."
if [ ! -f "config.json" ]; then
    if [ -f "config.json.example" ]; then
        echo "  注意: config.json 不存在，正在从示例文件创建..."
        cp config.json.example config.json
        echo "  ⚠ 请编辑 config.json 填写配置信息后再运行！"
        echo "    建议: 至少填写 tduck.api_key 和 tduck.field_ids"
        exit 0
    else
        echo "  警告: config.json 和 config.json.example 均不存在"
        echo "  请手动创建配置文件后重试"
        exit 1
    fi
fi
echo "  配置文件已存在"

# 创建数据目录（如果不存在）
if [ ! -d "data" ]; then
    mkdir -p data
    echo "  数据目录 data/ 已创建"
fi

# 启动服务
echo ""
echo "========================================"
echo "  启动服务..."
echo "========================================"
echo "  监听地址: http://0.0.0.0:5000"
echo "  Webhook:  http://0.0.0.0:5000/webhook/tduck"
echo "  健康检查: http://0.0.0.0:5000/health"
echo "  后台管理: http://0.0.0.0:5000/admin"
echo "========================================"
echo "  按 Ctrl+C 停止服务"
echo "========================================"
echo ""

$PYTHON_CMD -m src.app
