---
title: "📊 摘要总览"
type: "overview"
---

# ⚡ 网页摘要助手 v2.0

> 智能网页内容摘要工具 — 支持 5 大 AI 模型，一键生成结构化中文摘要

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://python.org)

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🌐 **多站点适配** | GitHub、CSDN、知乎、掘金、博客园等主流技术站点 |
| 🤖 **5 大模型** | 小米 MiMo、DeepSeek、GPT-4o、通义千问、Ollama 本地 |
| ⚡ **流式输出** | SSE 实时逐字返回，带阶段状态推送 |
| 🔄 **自动降级** | 当前模型不可用时自动切换备用模型 |
| 📦 **智能缓存** | 相同链接 1 小时内秒级返回 |
| 🎨 **炫酷界面** | 科幻风格 UI，粒子效果、光晕动画 |
| 📚 **Obsidian 集成** | 自动导出、分类、标签索引、关系图谱 |
| 🔒 **隐私安全** | 支持本地模型，数据不经过第三方 |
| ⚡ **GitHub 极速** | 多通道并行抓取，仓库页 < 1s |

---

## 🚀 快速开始

### 系统要求

- Python 3.8+
- 网络连接（使用云端模型时）

### 安装步骤

#### macOS / Linux

```bash
# 1. 克隆项目
git clone https://github.com/haojieliu-Estrela/web-summarizer.git
cd web-summarizer

# 2. 运行启动脚本（自动创建虚拟环境、安装依赖、引导配置）
chmod +x start.sh
./start.sh
```

#### Windows

```cmd
# 1. 克隆项目
git clone https://github.com/haojieliu-Estrela/web-summarizer.git
cd web-summarizer

# 2. 双击运行 start.bat
```

### 首次运行配置

首次启动时，程序会自动引导你完成配置：

1. **选择默认模型** — 推荐选择小米 MiMo（国产、性价比高）
2. **配置 API Key** — 根据选择的模型输入对应的 API Key
3. **测试连接** — 自动验证 API Key 是否有效

---

## 📋 支持的模型

| 模型 | 提供商 | 特点 | 适合场景 | API Key 获取 |
|------|--------|------|----------|--------------|
| **小米 MiMo** | 小米 | 国产、性价比高、中文优秀 | 日常摘要、中文内容 | [小米 AI 平台](https://api.xiaomimimo.com) |
| **DeepSeek** | DeepSeek | 国产、代码能力强 | 技术文档、代码解析 | [DeepSeek 平台](https://platform.deepseek.com) |
| **GPT-4o** | OpenAI | 效果最好、价格较高 | 高质量摘要、英文内容 | [OpenAI 平台](https://platform.openai.com) |
| **通义千问** | 阿里 | 国产、中文优化、价格低 | 中文内容、批量处理 | [阿里云](https://dashscope.console.aliyun.com) |
| **Ollama** | 本地 | 完全免费、数据不出本机 | 隐私敏感、离线使用 | [Ollama 官网](https://ollama.ai) |

### 🔑 API Key 获取指南

<details>
<summary><b>小米 MiMo（推荐）</b></summary>

1. 访问 [小米 AI 开放平台](https://api.xiaomimimo.com)
2. 注册账号并登录
3. 进入「API Key 管理」
4. 创建新的 API Key（以 `sk-` 开头）
5. 复制 Key，粘贴到 `.env` 文件的 `MIMO_API_KEY` 字段

</details>

<details>
<summary><b>DeepSeek</b></summary>

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com)
2. 注册账号并登录
3. 进入「API Keys」页面
4. 创建新的 API Key（以 `sk-` 开头）
5. 复制 Key，粘贴到 `.env` 文件的 `DEEPSEEK_API_KEY` 字段

</details>

<details>
<summary><b>OpenAI GPT-4o</b></summary>

1. 访问 [OpenAI 平台](https://platform.openai.com)
2. 注册账号并登录（需要海外手机号）
3. 进入「API Keys」页面
4. 创建新的 Secret Key（以 `sk-` 开头）
5. 复制 Key，粘贴到 `.env` 文件的 `OPENAI_API_KEY` 字段

</details>

<details>
<summary><b>通义千问</b></summary>

1. 访问 [阿里云百炼平台](https://dashscope.console.aliyun.com)
2. 用阿里云账号登录
3. 开通「DashScope」服务
4. 进入「API-KEY 管理」创建 Key
5. 复制 Key，粘贴到 `.env` 文件的 `QWEN_API_KEY` 字段

</details>

<details>
<summary><b>Ollama 本地模型</b></summary>

1. 访问 [Ollama 官网](https://ollama.ai) 下载安装
2. 终端运行 `ollama pull gemma4` 拉取模型
3. 确认 Ollama 服务运行：`ollama serve`
4. 在设置页面切换到「Ollama (本地)」即可
5. **无需 API Key**，数据完全不出本机

</details>

---

## ⚙️ 手动配置

如果需要手动配置，可以编辑 `.env` 文件：

```bash
# ──── 模型 API Key ────

# 小米 MiMo（推荐）
MIMO_API_KEY=sk-your-mimo-key

# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# 通义千问
QWEN_API_KEY=sk-your-qwen-key

# ──── 默认模型 ────
# 可选值: mimo, deepseek, openai, qwen, ollama
DEFAULT_MODEL=mimo

# ──── 自定义配置（可选）────
# 使用其他 OpenAI 兼容 API 时可覆盖
# MODEL_BASE_URL=https://api.example.com/v1
# MODEL_NAME=your-model-name
```

---

## 🌐 访问地址

启动成功后，访问以下地址：

| 页面 | 地址 | 功能 |
|------|------|------|
| 🏠 首页 | http://localhost:5001 | 输入链接生成摘要 |
| ⚙️ 设置 | http://localhost:5001/settings | 模型切换、连接测试 |

---

## 📚 Obsidian 集成

v2.0 新增 Obsidian 知识管理集成，摘要自动导出到 Obsidian Vault。

### 功能

- **自动导出** — 生成摘要后自动保存为 Markdown
- **智能分类** — 根据内容自动归类（tech / ai / devops / news / academic）
- **标签提取** — 自动提取技术标签（python, docker, llm 等）
- **关系图谱** — 基于共享标签自动关联笔记（`[[wikilinks]]`）
- **索引页** — 自动生成分类索引、标签索引、总览页
- **Dataview** — 内置 Dataview 查询，支持高级筛选

### 配置

在 `.env` 中设置 Vault 路径（可选）：

```bash
OBSIDIAN_VAULT_PATH=~/Documents/Obsidian Vault
```

### 目录结构

```
你的 Vault/
└── Web Summaries/
    ├── 📊 摘要总览.md          ← 总览（自动生成）
    ├── tech-index.md           ← 分类索引
    ├── ai-index.md
    ├── .tags/                  ← 标签索引
    │   ├── python.md
    │   ├── github.md
    │   └── ...
    ├── tech/                   ← 技术类摘要
    │   ├── 2026-01-01-xxx.md
    │   └── ...
    ├── ai/                     ← AI 类摘要
    ├── devops/                 ← 运维类摘要
    └── ...
```

### API

```bash
# 导出摘要到 Obsidian
curl -X POST http://localhost:5001/api/obsidian/export \
  -H "Content-Type: application/json" \
  -d '{"title": "...", "url": "...", "summary": "...", "model": "mimo-v2.5-pro"}'

# 重建所有索引
curl -X POST http://localhost:5001/api/obsidian/rebuild

# 查询关联笔记
curl -X POST http://localhost:5001/api/obsidian/related \
  -H "Content-Type: application/json" \
  -d '{"tags": ["python", "github"], "category": "tech"}'

# 获取统计信息
curl http://localhost:5001/api/obsidian/stats

# 获取思维导图数据
curl http://localhost:5001/api/obsidian/mindmap?days=30
```

---

## 🔧 API 接口

### 核心接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 首页 |
| `/settings` | GET | 模型设置页 |
| `/api/summarize` | POST | 同步摘要 |
| `/api/summarize/stream` | POST | 流式摘要 (SSE) |

### 模型管理

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/models` | GET | 获取所有模型列表 |
| `/api/models/current` | GET | 获取当前模型信息 |
| `/api/models/switch` | POST | 切换模型 |
| `/api/models/test` | POST | 测试模型连接 |

### Obsidian 集成

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/obsidian/export` | POST | 导出摘要到 Obsidian |
| `/api/obsidian/auto-export` | POST | 自动导出 |
| `/api/obsidian/rebuild` | POST | 重建所有索引 |
| `/api/obsidian/related` | POST | 查询关联笔记 |
| `/api/obsidian/stats` | GET | 获取统计信息 |
| `/api/obsidian/mindmap` | GET | 思维导图数据 |
| `/api/obsidian/classify` | POST | AI 自动分类 |

### 使用示例

```bash
# 同步摘要
curl -X POST http://localhost:5001/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo"}'

# 流式摘要（推荐，实时返回）
curl -X POST http://localhost:5001/api/summarize/stream \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo"}'

# 切换模型
curl -X POST http://localhost:5001/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_key": "deepseek"}'

# 测试连接
curl -X POST http://localhost:5001/api/models/test
```

---

## 📁 项目结构

```
web-summarizer/
├── app.py                   # 主程序（Flask 服务）
├── obsidian_integration.py  # Obsidian 集成模块
├── setup.py                 # 首次运行配置向导
├── start.sh                 # macOS/Linux 启动脚本
├── start.bat                # Windows 启动脚本
├── requirements.txt         # Python 依赖
├── .env                     # 配置文件（自动生成）
├── .env.example             # 配置示例
├── static/
│   ├── index.html           # 首页（科幻风格 UI）
│   └── settings.html        # 模型设置页
└── venv/                    # 虚拟环境（自动创建）
```

---

## ❓ 常见问题

### Q: 如何切换模型？

A: 访问 http://localhost:5001/settings，点击想要使用的模型卡片即可切换。也可以通过 API：

```bash
curl -X POST http://localhost:5001/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_key": "deepseek"}'
```

### Q: API Key 在哪里获取？

A: 根据选择的模型，访问对应的平台注册并获取 API Key：

| 平台 | 地址 | 费用 |
|------|------|------|
| 小米 MiMo | https://api.xiaomimimo.com | 注册送额度 |
| DeepSeek | https://platform.deepseek.com | 极低价格 |
| OpenAI | https://platform.openai.com | 需要海外支付 |
| 通义千问 | https://dashscope.console.aliyun.com | 有免费额度 |
| Ollama | https://ollama.ai | 完全免费 |

### Q: 如何使用本地 Ollama 模型？

A:
1. 安装 Ollama: https://ollama.ai
2. 拉取模型: `ollama pull gemma4`
3. 在设置页面切换到 "Ollama (本地)" 模型
4. **无需 API Key**，数据完全不出本机

### Q: 遇到 "无法连接到模型服务" 错误？

A:
1. 检查网络连接
2. 确认 API Key 是否正确
3. 确认账户是否有足够余额
4. 尝试在设置页面测试连接
5. 如果是 Ollama，确认服务已启动: `ollama serve`

### Q: 如何在服务器上部署？

A:
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export MIMO_API_KEY=sk-your-key
export DEFAULT_MODEL=mimo

# 启动服务
python app.py --host 0.0.0.0 --port 5001
```

### Q: GitHub 抓取很慢？

A: v2.0 已优化 GitHub 抓取（仓库页 < 1s）。如果仍然慢：
- 检查网络到 GitHub API 的连通性
- 国内用户可尝试使用代理
- `raw.githubusercontent.com` 在国内较慢，已自动降级到 GitHub API

### Q: 如何接入 Obsidian？

A:
1. 安装 [Obsidian](https://obsidian.md)
2. 打开或创建一个 Vault
3. 在 `.env` 中设置 `OBSIDIAN_VAULT_PATH`
4. 安装推荐插件：**Dataview**、**Markmap**
5. 生成摘要后会自动导出到 Vault

---

## 🔄 更新日志

### v2.0.0 (2026-06-09)

**⚡ 性能优化**
- 摘要生成速度提升 62%（85s → 33s）
- GitHub 抓取从 55s → 0.4s（提速 98%）
- GitHub API 并行请求，移除慢速通道
- 精简 prompt，优化 token 消耗

**📚 Obsidian 集成**
- 自动导出摘要到 Obsidian Vault
- AI 智能分类 + 标签提取
- 关系图谱（`[[wikilinks]]` 自动关联）
- 分类索引、标签索引、总览页自动生成
- Dataview 查询支持

**🔧 新增 API**
- `/api/obsidian/export` — 导出到 Obsidian
- `/api/obsidian/rebuild` — 重建索引
- `/api/obsidian/related` — 查询关联笔记

### v1.0.0

- 初始版本
- 支持 5 大 AI 模型
- 流式输出 + 智能缓存
- 科幻风格 UI

---

## 📄 许可证

MIT License

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) — Web 框架
- [OpenAI Python SDK](https://github.com/openai/openai-python) — AI 模型调用
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — HTML 解析
- [Obsidian](https://obsidian.md) — 知识管理工具
