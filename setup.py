#!/usr/bin/env python3
"""
网页摘要助手 - 首次运行配置向导
自动检测环境、引导用户配置 API Key
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

# 颜色定义
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

def print_banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════╗
║               🤖 网页摘要助手 - 配置向导                  ║
╠═══════════════════════════════════════════════════════════╣
║  支持云端 AI 模型：小米 MiMo / DeepSeek / OpenAI / 通义   ║
║  也支持本地 Ollama 模型运行                                ║
╚═══════════════════════════════════════════════════════════╝
{Colors.END}""")

def check_python():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"{Colors.RED}❌ Python 版本过低: {version.major}.{version.minor}")
        print(f"   需要 Python 3.9 或更高版本{Colors.END}")
        return False
    print(f"{Colors.GREEN}✅ Python {version.major}.{version.minor}.{version.micro}{Colors.END}")
    return True

def check_pip():
    """检查 pip 是否可用"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print(f"{Colors.GREEN}✅ pip 可用{Colors.END}")
        return True
    except:
        print(f"{Colors.RED}❌ pip 不可用{Colors.END}")
        return False

def check_ollama():
    """检查 Ollama 是否安装"""
    if shutil.which("ollama"):
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                models = [line.split()[0] for line in result.stdout.strip().split('\n')[1:] if line.strip()]
                if models:
                    print(f"{Colors.GREEN}✅ Ollama 已安装，可用模型: {', '.join(models[:3])}{Colors.END}")
                    return True
                else:
                    print(f"{Colors.YELLOW}⚠️  Ollama 已安装，但没有下载任何模型{Colors.END}")
                    return True
        except:
            pass
    print(f"{Colors.DIM}⏭️  Ollama 未安装（可选，不影响使用云端模型）{Colors.END}")
    return False

def install_dependencies():
    """安装 Python 依赖"""
    print(f"\n{Colors.CYAN}📦 安装依赖...{Colors.END}")
    
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        print(f"{Colors.RED}❌ 找不到 requirements.txt{Colors.END}")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "-q"
        ], check=True)
        print(f"{Colors.GREEN}✅ 依赖安装完成{Colors.END}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}❌ 依赖安装失败{Colors.END}")
        return False

def detect_existing_env():
    """检测是否已有 .env 配置"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
            if "MIMO_API_KEY=" in content and "sk-" in content:
                return True
    return False

def get_api_key_input(provider_name, env_var_name, hint=""):
    """获取用户输入的 API Key"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔑 配置 {provider_name}{Colors.END}")
    if hint:
        print(f"{Colors.DIM}   {hint}{Colors.END}")
    
    print(f"   请输入 API Key (输入 'skip' 跳过): ", end="", flush=True)
    api_key = input().strip()
    
    if api_key.lower() == 'skip' or not api_key:
        return None
    return api_key

def create_env_file(config):
    """创建 .env 文件"""
    env_path = Path(__file__).parent / ".env"
    
    lines = ["# 网页摘要助手 - 环境变量配置", "# 由配置向导自动生成\n"]
    
    if config.get("mimo"):
        lines.append(f"# 小米 MiMo")
        lines.append(f"MIMO_API_KEY={config['mimo']}\n")
    
    if config.get("deepseek"):
        lines.append(f"# DeepSeek")
        lines.append(f"DEEPSEEK_API_KEY={config['deepseek']}\n")
    
    if config.get("openai"):
        lines.append(f"# OpenAI")
        lines.append(f"OPENAI_API_KEY={config['openai']}\n")
    
    if config.get("qwen"):
        lines.append(f"# 通义千问")
        lines.append(f"QWEN_API_KEY={config['qwen']}\n")
    
    # 设置默认模型
    if config.get("mimo"):
        lines.append(f"DEFAULT_MODEL=mimo")
    elif config.get("deepseek"):
        lines.append(f"DEFAULT_MODEL=deepseek")
    elif config.get("openai"):
        lines.append(f"DEFAULT_MODEL=openai")
    elif config.get("qwen"):
        lines.append(f"DEFAULT_MODEL=qwen")
    else:
        lines.append(f"DEFAULT_MODEL=ollama")
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n{Colors.GREEN}✅ 配置已保存到 .env 文件{Colors.END}")

def interactive_setup():
    """交互式配置"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}═══ 模型配置 ═══{Colors.END}")
    print(f"请选择要使用的云端模型（可多选，按回车跳过）：\n")
    print(f"  {Colors.CYAN}1{Colors.END} - 小米 MiMo (推荐，国产模型)")
    print(f"  {Colors.CYAN}2{Colors.END} - DeepSeek (性价比高)")
    print(f"  {Colors.CYAN}3{Colors.END} - OpenAI GPT-4o")
    print(f"  {Colors.CYAN}4{Colors.END} - 通义千问 (阿里)")
    print(f"  {Colors.DIM}5{Colors.END} - 仅使用本地 Ollama\n")
    
    print("请输入选项 (如: 1,2 或 1): ", end="", flush=True)
    choices = input().strip().split(',')
    choices = [c.strip() for c in choices if c.strip()]
    
    config = {}
    
    for choice in choices:
        if choice == '1':
            key = get_api_key_input(
                "小米 MiMo",
                "MIMO_API_KEY",
                "获取地址: https://platform.xiaomi.com 或联系小米 AI 开放平台"
            )
            if key:
                config["mimo"] = key
        
        elif choice == '2':
            key = get_api_key_input(
                "DeepSeek",
                "DEEPSEEK_API_KEY",
                "获取地址: https://platform.deepseek.com"
            )
            if key:
                config["deepseek"] = key
        
        elif choice == '3':
            key = get_api_key_input(
                "OpenAI",
                "OPENAI_API_KEY",
                "获取地址: https://platform.openai.com"
            )
            if key:
                config["openai"] = key
        
        elif choice == '4':
            key = get_api_key_input(
                "通义千问",
                "QWEN_API_KEY",
                "获取地址: https://dashscope.console.aliyun.com"
            )
            if key:
                config["qwen"] = key
        
        elif choice == '5':
            print(f"\n{Colors.YELLOW}ℹ️  将使用本地 Ollama 模型（需要先安装 Ollama）{Colors.END}")
    
    return config

def print_next_steps(has_config):
    """打印后续步骤"""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
═══════════════════════════════════════════════════════════
                    ✅ 配置完成！
═══════════════════════════════════════════════════════════{Colors.END}

{Colors.BOLD}🚀 启动服务：{Colors.END}

    {Colors.CYAN}python app.py{Colors.END}

    或使用启动脚本：
    {Colors.CYAN}./start.sh{Colors.END}      (macOS/Linux)
    {Colors.CYAN}start.bat{Colors.END}       (Windows)

{Colors.BOLD}🌐 访问地址：{Colors.END}

    首页:      {Colors.CYAN}http://127.0.0.1:5001{Colors.END}
    模型设置:  {Colors.CYAN}http://127.0.0.1:5001/settings{Colors.END}

{Colors.BOLD}📝 修改配置：{Colors.END}

    编辑 {Colors.CYAN}.env{Colors.END} 文件，或重新运行 {Colors.CYAN}python setup.py{Colors.END}

{Colors.DIM}───────────────────────────────────────────────────────────{Colors.END}
""")

def main():
    """主函数"""
    print_banner()
    
    # 检测环境
    print(f"{Colors.CYAN}{Colors.BOLD}🔍 环境检测{Colors.END}\n")
    
    python_ok = check_python()
    pip_ok = check_pip()
    has_ollama = check_ollama()
    has_existing_env = detect_existing_env()
    
    if not python_ok:
        print(f"\n{Colors.RED}请安装 Python 3.9 或更高版本后重试{Colors.END}")
        sys.exit(1)
    
    # 安装依赖
    print(f"\n{Colors.CYAN}{Colors.BOLD}📦 依赖安装{Colors.END}")
    if not install_dependencies():
        print(f"\n{Colors.YELLOW}⚠️  依赖安装失败，请手动执行: pip install -r requirements.txt{Colors.END}")
    
    # 配置模型
    if has_existing_env:
        print(f"\n{Colors.GREEN}✅ 检测到已有配置文件 (.env){Colors.END}")
        print(f"是否重新配置？(y/N): ", end="", flush=True)
        if input().strip().lower() != 'y':
            print_next_steps(True)
            return
    
    config = interactive_setup()
    
    if config:
        create_env_file(config)
    else:
        print(f"\n{Colors.YELLOW}⚠️  未配置任何 API Key{Colors.END}")
        print(f"   将使用本地 Ollama 模型（如果已安装）")
        print(f"   或编辑 .env 文件手动添加 API Key\n")
    
    print_next_steps(bool(config))

if __name__ == "__main__":
    main()
