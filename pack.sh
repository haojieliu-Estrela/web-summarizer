#!/bin/bash
# 网页摘要助手 - 打包脚本
# 使用方法: ./pack.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ⚡ 网页摘要助手 - 打包程序 ⚡               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 获取版本号
VERSION=$(grep -oP 'version.*?["\047]([^"\047]+)["\047]' app.py 2>/dev/null | head -1 | grep -oP '["\047]([^"\047]+)["\047]' | tr -d '"' || echo "1.0.0")
PACKAGE_NAME="web-summarizer-v${VERSION}"
DIST_DIR="dist"
PACKAGE_DIR="${DIST_DIR}/${PACKAGE_NAME}"

info "打包版本: ${VERSION}"
info "包名: ${PACKAGE_NAME}.tar.gz"
echo ""

# 清理旧的打包
if [ -d "${DIST_DIR}" ]; then
    warn "清理旧的打包目录..."
    rm -rf "${DIST_DIR}"
fi

# 创建打包目录
info "创建打包目录..."
mkdir -p "${PACKAGE_DIR}"

# 复制必要文件
info "复制项目文件..."

# 核心文件
cp app.py "${PACKAGE_DIR}/"
cp setup.py "${PACKAGE_DIR}/"
cp start.sh "${PACKAGE_DIR}/"
cp start.bat "${PACKAGE_DIR}/"
cp requirements.txt "${PACKAGE_DIR}/"
cp README.md "${PACKAGE_DIR}/"
cp .env.example "${PACKAGE_DIR}/"

# 静态文件
cp -r static "${PACKAGE_DIR}/"

# 模板文件（如果存在）
if [ -d "templates" ]; then
    cp -r templates "${PACKAGE_DIR}/"
fi

# 设置脚本可执行权限
chmod +x "${PACKAGE_DIR}/start.sh"
chmod +x "${PACKAGE_DIR}/setup.py"

success "文件复制完成"

# 创建 .gitignore（如果不存在）
if [ ! -f ".gitignore" ]; then
    cat > "${PACKAGE_DIR}/.gitignore" << 'EOF'
# 虚拟环境
venv/
.venv/

# Python 缓存
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# 配置文件（包含 API Key）
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db

# 打包输出
dist/
build/
*.egg-info/
EOF
    success "创建 .gitignore"
fi

# 创建压缩包
info "创建压缩包..."
cd "${DIST_DIR}"
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
cd ..

# 计算包大小
PACKAGE_SIZE=$(du -h "${DIST_DIR}/${PACKAGE_NAME}.tar.gz" | cut -f1)

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    ✅ 打包完成！                         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📦 包文件: ${DIST_DIR}/${PACKAGE_NAME}.tar.gz"
echo "📏 包大小: ${PACKAGE_SIZE}"
echo ""
echo "📋 包内容:"
ls -la "${PACKAGE_DIR}" | grep -v "^total" | awk '{print "   " $NF}'
echo ""
echo "🚀 使用方法:"
echo "   1. 解压: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "   2. 进入: cd ${PACKAGE_NAME}"
echo "   3. 启动: ./start.sh (macOS/Linux) 或 start.bat (Windows)"
echo ""
