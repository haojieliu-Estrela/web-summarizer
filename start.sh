#!/bin/bash
# 网页摘要助手 - 启动脚本 (macOS/Linux)
# 使用方法: ./start.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ⚡ 网页摘要助手 - 启动程序 ⚡               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python 版本
info "检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    success "Python $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    if [[ "$PYTHON_VERSION" == 3.* ]]; then
        success "Python $PYTHON_VERSION"
        PYTHON_CMD="python"
    else
        error "需要 Python 3.8+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
else
    error "未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    warn "虚拟环境不存在，正在创建..."
    $PYTHON_CMD -m venv venv
    success "虚拟环境创建完成"
fi

# 激活虚拟环境
info "激活虚拟环境..."
source venv/bin/activate

# 检查依赖
info "检查依赖..."
if ! python -c "import flask" &> /dev/null; then
    warn "依赖未安装，正在安装..."
    pip install -r requirements.txt -q
    success "依赖安装完成"
else
    success "依赖已安装"
fi

# 检查配置
if [ ! -f ".env" ]; then
    warn "配置文件不存在"
    echo ""
    echo "首次使用需要配置 API Key，是否现在配置？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        $PYTHON_CMD setup.py
    else
        warn "跳过配置，将使用默认 Ollama 本地模型"
        echo "DEFAULT_MODEL=ollama" > .env
    fi
fi

# 启动服务
echo ""
info "启动网页摘要助手..."
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🌐 访问地址: http://localhost:5001                      ║"
echo "║  ⚙️  模型设置: http://localhost:5001/settings             ║"
echo "║  📝 按 Ctrl+C 停止服务                                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

python app.py
