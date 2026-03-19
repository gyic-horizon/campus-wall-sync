#!/bin/bash
# ========================================
# 本地开发启动脚本
# 
# 功能：自动安装依赖并启动服务
# 使用：./run_local.sh
# ========================================
@echo off
set -e  # 遇到错误立即退出

echo "========================================"
echo "  校园墙同步服务 - 本地开发启动脚本"
echo "========================================"

# 检查Python版本
echo "[1/5] 检查Python版本..."
python_version=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1)
if [ "$python_version" -lt 3 ]; then
    echo "错误: 需要Python 3.x，请先安装Python 3"
    exit 1
fi
echo "  Python版本检查通过"

# 创建虚拟环境（可选）
if [ ! -d "venv" ]; then
    echo "[2/5] 创建虚拟环境..."
    python -m venv venv
    echo "  虚拟环境创建完成"
else
    echo "[2/5] 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "[3/5] 激活虚拟环境..."
source venv/Scripts/activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
echo "[4/5] 安装项目依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 检查配置文件
echo "[5/5] 检查配置文件..."
if [ ! -f "config.json" ]; then
    echo "  警告: config.json 不存在，正在从示例文件创建..."
    cp config.json.example config.json
    echo "  请编辑 config.json 填写配置信息后再运行！"
    exit 0
fi

# 启动服务
echo ""
echo "========================================"
echo "  启动服务..."
echo "========================================"
python -m src.app
