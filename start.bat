@echo off
chcp 65001 >nul
title 网页摘要助手

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              ⚡ 网页摘要助手 - 启动程序 ⚡               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: 检查 Python
echo [INFO] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python %PYTHON_VERSION%

:: 检查虚拟环境
if not exist "venv" (
    echo [!] 虚拟环境不存在，正在创建...
    python -m venv venv
    echo [✓] 虚拟环境创建完成
)

:: 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查依赖
echo [INFO] 检查依赖...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 依赖未安装，正在安装...
    pip install -r requirements.txt -q
    echo [✓] 依赖安装完成
) else (
    echo [✓] 依赖已安装
)

:: 检查配置
if not exist ".env" (
    echo [!] 配置文件不存在
    echo.
    echo 首次使用需要配置 API Key，是否现在配置？(Y/N)
    set /p response=
    if /i "%response%"=="Y" (
        python setup.py
    ) else (
        echo [!] 跳过配置，将使用默认 Ollama 本地模型
        echo DEFAULT_MODEL=ollama > .env
    )
)

:: 启动服务
echo.
echo [INFO] 启动网页摘要助手...
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  🌐 访问地址: http://localhost:5001                      ║
echo ║  ⚙️  模型设置: http://localhost:5001/settings             ║
echo ║  📝 按 Ctrl+C 停止服务                                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

python app.py
pause
