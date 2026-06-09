# ⚡ 网页摘要助手

一个智能的网页内容摘要工具，支持多种云端 AI 模型，一键生成结构化中文摘要。

## ✨ 功能特点

- 🌐 **多站点适配** - 支持 GitHub、CSDN、知乎、掘金、博客园等主流技术站点
- 🤖 **多模型支持** - 小米 MiMo、DeepSeek、OpenAI、通义千问、Ollama 本地模型
- ⚡ **流式输出** - 实时展示生成过程，逐字返回
- 📦 **智能缓存** - 相同链接 1 小时内秒级返回
- 🎨 **炫酷界面** - 科幻风格 UI，粒子效果、光晕动画
- 🔒 **隐私安全** - 支持本地模型，数据不经过第三方

## 🚀 快速开始

### 系统要求

- Python 3.8+
- 网络连接（使用云端模型时）

### 安装步骤

#### macOS / Linux

```bash
# 1. 克隆或下载项目
git clone <repository-url>
cd web-summarizer

# 2. 运行启动脚本（会自动创建虚拟环境、安装依赖、引导配置）
chmod +x start.sh
./start.sh
```

#### Windows

```cmd
# 1. 克隆或下载项目
git clone <repository-url>
cd web-summarizer

# 2. 双击运行 start.bat
```

### 首次运行配置

首次启动时，程序会自动引导你完成配置：

1. **选择默认模型** - 推荐选择小米 MiMo（国产、性价比高）
2. **配置 API Key** - 根据选择的模型输入对应的 API Key
3. **测试连接** - 自动验证 API Key 是否有效

## 📋 支持的模型

| 模型 | 提供商 | 特点 | API Key 获取 |
|------|--------|------|--------------|
| **小米 MiMo** | 小米 | 国产、性价比高 | [小米 AI 平台](https://api.xiaomimimo.com) |
| **DeepSeek** | DeepSeek | 国产、代码能力强 | [DeepSeek 平台](https://platform.deepseek.com) |
| **GPT-4o** | OpenAI | 效果最好、价格较高 | [OpenAI 平台](https://platform.openai.com) |
| **通义千问** | 阿里 | 国产、中文优化 | [阿里云](https://dashscope.console.aliyun.com) |
| **Ollama** | 本地 | 完全免费、需本地部署 | [Ollama 官网](https://ollama.ai) |

## ⚙️ 手动配置

如果需要手动配置，可以编辑 `.env` 文件：

```bash
# 小米 MiMo
MIMO_API_KEY=sk-you...-key

# DeepSeek
DEEPSEEK_API_KEY=*** OpenAI
OPENAI_API_KEY=*** 通义千问
QWEN_API_KEY=*** 默认模型 (可选: mimo, deepseek, openai, qwen, ollama)
DEFAULT_MODEL=mimo
```

## 🌐 访问地址

启动成功后，访问以下地址：

- **首页**: http://localhost:5001
- **模型设置**: http://localhost:5001/settings

## 📁 项目结构

```
web-summarizer/
├── app.py              # 主程序
├── setup.py            # 首次运行配置向导
├── start.sh            # macOS/Linux 启动脚本
├── start.bat           # Windows 启动脚本
├── requirements.txt    # Python 依赖
├── .env                # 配置文件（自动生成）
├── .env.example        # 配置示例
├── static/
│   ├── index.html      # 首页
│   └── settings.html   # 模型设置页
└── venv/               # 虚拟环境（自动创建）
```

## 🔧 API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 首页 |
| `/settings` | GET | 模型设置页 |
| `/api/summarize` | POST | 同步摘要 |
| `/api/summarize/stream` | POST | 流式摘要 (SSE) |
| `/api/models` | GET | 获取模型列表 |
| `/api/models/current` | GET | 获取当前模型 |
| `/api/models/switch` | POST | 切换模型 |
| `/api/models/test` | POST | 测试模型连接 |

### 使用示例

```bash
# 同步摘要
curl -X POST http://localhost:5001/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo"}'

# 流式摘要
curl -X POST http://localhost:5001/api/summarize/stream \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo"}'
```

## ❓ 常见问题

### Q: 如何切换模型？

A: 访问 http://localhost:5001/settings，点击想要使用的模型卡片即可切换。

### Q: API Key 在哪里获取？

A: 根据选择的模型，访问对应的平台注册并获取 API Key：
- 小米 MiMo: https://api.xiaomimimo.com
- DeepSeek: https://platform.deepseek.com
- OpenAI: https://platform.openai.com
- 通义千问: https://dashscope.console.aliyun.com

### Q: 如何使用本地 Ollama 模型？

A: 
1. 安装 Ollama: https://ollama.ai
2. 拉取模型: `ollama pull gemma4`
3. 在设置页面切换到 "Ollama (本地)" 模型

### Q: 遇到 "无法连接到模型服务" 错误？

A: 
1. 检查网络连接
2. 确认 API Key 是否正确
3. 确认账户是否有足够余额
4. 尝试在设置页面测试连接

### Q: 如何在服务器上部署？

A: 
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export MIMO_API_KEY=sk-you...-key
export DEFAULT_MODEL=mimo

# 启动服务
python app.py --host 0.0.0.0 --port 5001
```

## 📄 许可证

MIT License

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [OpenAI Python SDK](https://github.com/openai/openai-python) - AI 模型调用
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析
