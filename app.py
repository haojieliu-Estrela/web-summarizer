from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from openai import OpenAI
import requests
import re
import html
import os
import json
import time
from html.parser import HTMLParser
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# =================== 模型配置管理 ===================

# 预设的云端模型配置
PRESET_MODELS = {
    "mimo": {
        "name": "小米 MiMo",
        "provider": "xiaomi",
        "base_url": "https://api.xiaomimimo.com/v1",
        "model": "mimo-v2.5-pro",
        "api_key_env": "MIMO_API_KEY"
    },
    "deepseek": {
        "name": "DeepSeek",
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY"
    },
    "openai": {
        "name": "OpenAI GPT-4o",
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY"
    },
    "qwen": {
        "name": "通义千问",
        "provider": "qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
        "api_key_env": "QWEN_API_KEY"
    },
    "ollama": {
        "name": "Ollama (本地)",
        "provider": "ollama",
        "base_url": "http://localhost:11434/v1",
        "model": "gemma4",
        "api_key_env": None
    }
}

# 当前使用的模型配置（默认使用 ollama）
_current_model_key = os.environ.get("DEFAULT_MODEL", "ollama")
_model_config_cache = {}
_config_lock = Lock()


def get_current_model_config():
    """获取当前模型配置"""
    with _config_lock:
        config = PRESET_MODELS.get(_current_model_key, PRESET_MODELS["ollama"]).copy()

        # 从环境变量读取 API Key
        api_key_env = config.get("api_key_env")
        if api_key_env:
            config["api_key"] = os.environ.get(api_key_env, "")
        else:
            config["api_key"] = ""

        # 允许通过环境变量覆盖
        config["base_url"] = os.environ.get("MODEL_BASE_URL", config["base_url"])
        config["model"] = os.environ.get("MODEL_NAME", config["model"])

        return config


def get_openai_client():
    """获取 OpenAI 客户端"""
    config = get_current_model_config()

    if config["provider"] == "ollama":
        return OpenAI(
            base_url=config["base_url"],
            api_key="ollama"  # Ollama 不需要真实的 key
        )
    else:
        return OpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"]
        )


def set_current_model(model_key):
    """切换当前使用的模型"""
    global _current_model_key
    if model_key in PRESET_MODELS:
        _current_model_key = model_key
        return True
    return False


def get_fallback_model():
    """获取备用模型（当当前模型不可用时）"""
    # 优先尝试 Ollama 本地模型
    if _current_model_key != "ollama":
        return "ollama"
    # 如果已经是 Ollama，尝试其他有 API Key 的云端模型
    for key, config in PRESET_MODELS.items():
        if key != "ollama" and key != _current_model_key:
            api_key_env = config.get("api_key_env")
            if api_key_env and os.environ.get(api_key_env):
                return key
    return None


def check_model_availability():
    """检查当前模型是否可用"""
    config = get_current_model_config()

    # 检查 API Key
    api_key_env = config.get("api_key_env")
    if api_key_env and not os.environ.get(api_key_env):
        return False, f"缺少 API Key: {api_key_env}"

    return True, "OK"


# 启动时打印配置信息
def print_startup_info():
    """打印启动信息"""
    config = get_current_model_config()
    print("\n" + "="*60)
    print("⚡ 网页摘要助手 - 启动中...")
    print("="*60)
    print(f"📍 当前模型: {config['name']} ({config['model']})")
    print(f"🔗 API 地址: {config['base_url']}")

    # 检查 API Key
    api_key_env = config.get("api_key_env")
    if api_key_env:
        has_key = bool(os.environ.get(api_key_env))
        if has_key:
            print(f"🔑 API Key: ✅ 已配置")
        else:
            print(f"🔑 API Key: ❌ 未配置 ({api_key_env})")
            print(f"   💡 提示: 运行 python setup.py 配置 API Key")
    else:
        print(f"🔑 API Key: 不需要 (本地模型)")

    # 检测其他可用模型
    available_models = []
    for key, model_config in PRESET_MODELS.items():
        if key == _current_model_key:
            continue
        api_key = model_config.get("api_key_env")
        if api_key and os.environ.get(api_key):
            available_models.append(model_config['name'])

    if available_models:
        print(f"🎯 其他可用模型: {', '.join(available_models)}")

    print("="*60)
    print(f"🌐 访问地址: http://localhost:5001")
    print(f"⚙️  模型设置: http://localhost:5001/settings")
    print("="*60 + "\n")


# =================== 内容抓取 ====================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4"

# 内存缓存：url -> {"summary": str, "timestamp": float}
_summary_cache = {}
_cache_lock = Lock()
CACHE_TTL = 3600  # 缓存 1 小时


class TextExtractor(HTMLParser):
    """提取 HTML 正文内容，过滤噪音标签"""
    SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "noscript", "iframe", "svg", "canvas"}

    def __init__(self):
        super().__init__()
        self.texts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.texts.append(stripped)

    def get_text(self):
        return "\n".join(self.texts)


def clean_text(text):
    """清理提取的文本，过滤噪音行"""
    text = html.unescape(text)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 4:
            continue
        if re.match(r'^[\W\d_]+$', stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines[:2500])


def _make_request_with_session(url, timeout=15):
    """使用 Session + 完整浏览器头请求网页，自动处理 cookie 和反爬"""
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    parsed = urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/"

    # 仅对需要 cookie 的站点先访问首页（GitHub 等不需要，跳过可节省 10s+）
    _COOKIE_REQUIRED_HOSTS = {"zhuanlan.zhihu.com", "blog.csdn.net", "juejin.cn", "www.zhihu.com", "mp.weixin.qq.com"}
    if any(h in parsed.netloc for h in _COOKIE_REQUIRED_HOSTS):
        try:
            session.get(referer, headers=headers, timeout=5, allow_redirects=True)
        except Exception:
            pass

    headers["Referer"] = referer
    headers["Sec-Fetch-Site"] = "same-origin"

    # 正式请求目标页面
    resp = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)

    # 如果 403，尝试移动端 UA
    if resp.status_code == 403:
        mobile_headers = dict(headers)
        mobile_headers["User-Agent"] = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        mobile_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        resp = session.get(url, headers=mobile_headers, timeout=timeout, allow_redirects=True)

    resp.raise_for_status()
    return resp


def fetch_generic_content(url):
    """通用网页内容提取，适配 CSDN、知乎、掘金、博客园等常见技术博客"""
    resp = _make_request_with_session(url)
    resp.encoding = resp.apparent_encoding

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 移除噪音标签
    for tag in soup([
        'script', 'style', 'nav', 'header', 'footer', 'aside',
        'noscript', 'iframe', 'svg', 'canvas', 'form', 'button', 'ad'
    ]):
        tag.decompose()

    # 常见内容区域选择器（按优先级排序）
    selectors = [
        ('article', None),
        ('main', None),
        ('div', {'id': 'content_views'}),              # CSDN 新文章页
        ('div', {'class': 'RichContent-inner'}),       # 知乎
        ('div', {'class': 'markdown-body'}),           # 掘金 / GitHub
        ('div', {'class': 'post-content'}),            # 博客园 / WordPress
        ('div', {'id': 'cnblogs_post_body'}),          # 博客园旧版
        ('div', {'class': 'article-content'}),         # 通用
        ('div', {'class': 'entry-content'}),           # WordPress
        ('div', {'class': 'content'}),                 # 通用
        ('div', {'class': 'post'}),                    # 通用
        ('section', None),
    ]

    for tag_name, attrs in selectors:
        elem = soup.find(tag_name, attrs)
        if elem:
            text = elem.get_text(separator='\n', strip=True)
            if len(text) > 200:
                return clean_text(text)

    # Fallback: 提取 body 全部文本
    body = soup.find('body')
    if body:
        text = body.get_text(separator='\n', strip=True)
    else:
        text = soup.get_text(separator='\n', strip=True)

    cleaned = clean_text(text)
    return cleaned if len(cleaned) > 50 else None


# =================== GitHub 多通道抓取（保持不变）====================

def channel_raw_readme(repo, branch="main"):
    urls = [
        f"https://raw.githubusercontent.com/{repo}/{branch}/README.md",
        f"https://raw.githubusercontent.com/{repo}/{branch}/readme.md",
        f"https://raw.githubusercontent.com/{repo}/{branch}/README.rst",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.text) > 50:
                return resp.text
        except Exception:
            continue
    return None


def channel_repo_api(repo):
    try:
        resp = requests.get(f"https://api.github.com/repos/{repo}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            parts = [
                f"Name: {data.get('full_name', '')}",
                f"Description: {data.get('description', '')}",
                f"Topics: {', '.join(data.get('topics', []))}",
            ]
            readme_resp = requests.get(
                f"https://api.github.com/repos/{repo}/readme",
                timeout=10,
                headers={"Accept": "application/vnd.github.raw"}
            )
            if readme_resp.status_code == 200:
                parts.append(f"\nREADME:\n{readme_resp.text}")
            return "\n".join(parts)
    except Exception:
        pass
    return None


def channel_raw_blob(url):
    raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    try:
        resp = requests.get(raw_url, timeout=10)
        if resp.status_code == 200 and len(resp.text) > 20:
            return resp.text
    except Exception:
        pass
    return None


def channel_issue_api(repo, issue_num):
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{repo}/issues/{issue_num}", timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            parts = [f"Title: {data.get('title', '')}", f"\n{data.get('body', '')}"]
            comments_url = data.get("comments_url")
            if comments_url:
                try:
                    cresp = requests.get(comments_url, timeout=10)
                    if cresp.status_code == 200:
                        comments = cresp.json()
                        if comments:
                            parts.append("\n\nComments:")
                            for c in comments[:15]:
                                parts.append(f"- {c.get('body', '')}")
                except Exception:
                    pass
            return "\n".join(parts)
    except Exception:
        pass
    return None


def channel_pr_api(repo, pr_num):
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_num}", timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            parts = [
                f"Title: {data.get('title', '')}",
                f"State: {data.get('state', '')}",
                f"\n{data.get('body', '')}",
            ]
            return "\n".join(parts)
    except Exception:
        pass
    return None


def channel_html_extract(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        extractor = TextExtractor()
        try:
            extractor.feed(resp.text)
        except Exception:
            pass
        text = extractor.get_text()
        cleaned = clean_text(text)
        if len(cleaned) > 100:
            return cleaned
    except Exception:
        pass
    return None


def fetch_github_content(url):
    """多通道抓取 GitHub 内容，并行请求，返回 (content, channel_name)
    优化：GitHub 页面 HTML 解析极慢且质量差，移除该通道；优先走 API（~1s）
    """
    channels = []

    if "/blob/" in url:
        channels.append(("raw_blob", lambda: channel_raw_blob(url)))

    elif "/issues/" in url:
        match = re.search(r'github\.com/([^/]+/[^/]+)/issues/(\d+)', url)
        if match:
            repo, issue_num = match.groups()
            channels.append(("issue_api", lambda: channel_issue_api(repo, issue_num)))

    elif "/pull/" in url:
        match = re.search(r'github\.com/([^/]+/[^/]+)/pull/(\d+)', url)
        if match:
            repo, pr_num = match.groups()
            channels.append(("pr_api", lambda: channel_pr_api(repo, pr_num)))

    else:
        match = re.search(r'github\.com/([^/]+/[^/]+)/?', url)
        if match:
            repo = match.group(1)
            # API 通道（最快，~0.6s），包含 repo 信息 + README
            channels.append(("repo_api", lambda: channel_repo_api(repo)))
            # raw README 作为备用（国内可能慢，20s+），但比 html_extract 快
            branch = "main"
            try:
                api_resp = requests.get(f"https://api.github.com/repos/{repo}", timeout=5)
                if api_resp.status_code == 200:
                    branch = api_resp.json().get("default_branch", "main")
            except Exception:
                pass
            channels.append(("raw_readme", lambda: channel_raw_readme(repo, branch)))

    if not channels:
        content = channel_html_extract(url)
        return (content, "html_extract") if content else (None, None)

    results = {}
    with ThreadPoolExecutor(max_workers=len(channels)) as executor:
        future_to_name = {
            executor.submit(fn): name for name, fn in channels
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                result = future.result()
                if result and len(result) > 50:
                    results[name] = result
            except Exception:
                pass

    priority = ["raw_blob", "issue_api", "pr_api", "repo_api", "raw_readme"]
    for p in priority:
        if p in results:
            return results[p], p

    return None, None


# =================== 统一内容入口 ====================

def fetch_content(url):
    """统一内容抓取入口：GitHub 走多通道，其他网页走通用提取"""
    parsed = urlparse(url)
    if parsed.netloc.endswith("github.com"):
        return fetch_github_content(url)
    content = fetch_generic_content(url)
    return (content, "generic_bs4") if content else (None, None)


def build_prompt(text):
    truncated = text[:8000] if len(text) > 8000 else text
    return f"""请阅读以下内容，生成一份简洁的中文摘要。
要求：
1. 提炼核心观点和关键结论
2. 技术内容说明主要方案
3. 条理清晰，分点输出
4. 300-500字

内容：

{truncated}

摘要："""


def summarize_with_openai_stream(text):
    """使用 OpenAI 兼容 API 流式调用"""
    config = get_current_model_config()
    client = get_openai_client()

    prompt = build_prompt(text)

    try:
        stream = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.2,
            max_tokens=1500
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield token, False
            if chunk.choices[0].finish_reason == "stop":
                yield "", True
                break

    except Exception as e:
        raise e


def summarize_with_openai(text):
    """使用 OpenAI 兼容 API 同步调用"""
    config = get_current_model_config()
    client = get_openai_client()

    prompt = build_prompt(text)

    try:
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.2,
            max_tokens=1500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise e


# 保留旧的 Ollama 直接调用作为后备
def summarize_with_ollama_stream(text):
    """流式调用 Ollama，yield 每个 token"""
    prompt = build_prompt(text)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 1500
        }
    }
    resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=180)
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            try:
                data = json.loads(line)
                token = data.get("response", "")
                done = data.get("done", False)
                yield token, done
                if done:
                    break
            except json.JSONDecodeError:
                pass


def summarize_with_ollama(text):
    """同步调用 Ollama（非流式）"""
    prompt = build_prompt(text)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1500
        }
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
    resp.raise_for_status()
    result = resp.json()
    return result.get("response", "").strip()


def sse(event, data):
    """构造 SSE 事件行"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# =================== 路由 ====================

@app.route("/")
def index():
    return send_from_directory(os.path.join(app.root_path, "static"), "index.html")


@app.route("/settings")
def settings_page():
    return send_from_directory(os.path.join(app.root_path, "static"), "settings.html")


@app.route("/api/models", methods=["GET"])
def get_models():
    """获取所有可用模型配置"""
    models = []
    for key, config in PRESET_MODELS.items():
        api_key_env = config.get("api_key_env")
        has_key = bool(os.environ.get(api_key_env)) if api_key_env else True

        models.append({
            "key": key,
            "name": config["name"],
            "provider": config["provider"],
            "model": config["model"],
            "has_api_key": has_key,
            "is_current": key == _current_model_key
        })

    return jsonify({
        "models": models,
        "current": _current_model_key
    })


@app.route("/api/models/current", methods=["GET"])
def get_current_model():
    """获取当前模型信息"""
    config = get_current_model_config()
    return jsonify({
        "key": _current_model_key,
        "name": config["name"],
        "provider": config["provider"],
        "model": config["model"],
        "base_url": config["base_url"]
    })


@app.route("/api/models/switch", methods=["POST"])
def switch_model():
    """切换模型"""
    data = request.get_json(silent=True) or {}
    model_key = data.get("model_key", "")

    if not model_key:
        return jsonify({"error": "请提供 model_key"}), 400

    if model_key not in PRESET_MODELS:
        return jsonify({"error": f"不支持的模型: {model_key}"}), 400

    # 检查 API Key
    config = PRESET_MODELS[model_key]
    api_key_env = config.get("api_key_env")
    if api_key_env and not os.environ.get(api_key_env):
        return jsonify({
            "error": f"缺少 API Key，请先配置环境变量 {api_key_env}",
            "env_var": api_key_env
        }), 400

    if set_current_model(model_key):
        new_config = get_current_model_config()
        return jsonify({
            "success": True,
            "message": f"已切换到 {config['name']}",
            "current": {
                "key": model_key,
                "name": config["name"],
                "model": config["model"]
            }
        })
    else:
        return jsonify({"error": "切换失败"}), 500


@app.route("/api/models/test", methods=["POST"])
def test_model():
    """测试当前模型是否可用"""
    try:
        config = get_current_model_config()
        client = get_openai_client()

        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "user", "content": "你好，请回复'连接成功'"}
            ],
            stream=False,
            max_tokens=50
        )

        result = response.choices[0].message.content.strip()
        return jsonify({
            "success": True,
            "message": "模型连接正常",
            "response": result,
            "model": config["model"]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/summarize", methods=["POST"])
def summarize():
    global _current_model_key
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    parsed = urlparse(url)
    if not url or parsed.scheme not in ("http", "https"):
        return jsonify({"error": "请输入有效的网页链接（http:// 或 https://）"}), 400

    try:
        # 检查缓存
        with _cache_lock:
            cached = _summary_cache.get(url)
            if cached and (time.time() - cached["timestamp"]) < CACHE_TTL:
                return jsonify({
                    "summary": cached["summary"],
                    "url": url,
                    "content_length": cached.get("content_length", 0),
                    "cached": True,
                    "model": get_current_model_config()["model"]
                })

        content, channel = fetch_content(url)
        if not content or len(content) < 10:
            return jsonify({"error": "无法获取页面内容，请确认链接可访问"}), 400

        # 根据当前模型选择调用方式，支持自动降级
        config = get_current_model_config()
        used_model = _current_model_key

        try:
            if config["provider"] == "ollama":
                summary = summarize_with_ollama(content)
            else:
                summary = summarize_with_openai(content)
        except Exception as model_error:
            # 当前模型失败，尝试降级到备用模型
            fallback_key = get_fallback_model()
            if fallback_key:
                print(f"⚠️  模型 {config['name']} 调用失败: {model_error}")
                print(f"🔄 自动降级到备用模型: {PRESET_MODELS[fallback_key]['name']}")

                # 临时切换到备用模型
                old_model = _current_model_key
                _current_model_key = fallback_key

                try:
                    fallback_config = get_current_model_config()
                    if fallback_config["provider"] == "ollama":
                        summary = summarize_with_ollama(content)
                    else:
                        summary = summarize_with_openai(content)
                    used_model = fallback_key
                except Exception as fallback_error:
                    # 恢复原模型
                    _current_model_key = old_model
                    raise fallback_error
            else:
                raise model_error

        with _cache_lock:
            _summary_cache[url] = {
                "summary": summary,
                "timestamp": time.time(),
                "content_length": len(content)
            }

        return jsonify({
            "summary": summary,
            "url": url,
            "content_length": len(content),
            "channel": channel,
            "cached": False,
            "model": get_current_model_config()["model"],
            "used_model": used_model
        })
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "无法连接到模型服务，请检查网络或 API 配置"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summarize/stream", methods=["POST"])
def summarize_stream():
    """SSE 流式摘要：实时展示生成过程"""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    parsed = urlparse(url)
    if not url or parsed.scheme not in ("http", "https"):
        return jsonify({"error": "请输入有效的网页链接（http:// 或 https://）"}), 400

    def event_stream():
        start_time = time.time()

        # 阶段 1: 解析 URL
        yield sse("stage", {
            "stage": "parse",
            "message": "正在解析网页链接...",
            "elapsed": round(time.time() - start_time, 2)
        })

        # 检查缓存
        with _cache_lock:
            cached = _summary_cache.get(url)
            if cached and (time.time() - cached["timestamp"]) < CACHE_TTL:
                yield sse("stage", {
                    "stage": "cached",
                    "message": "✅ 发现缓存结果，直接返回",
                    "elapsed": round(time.time() - start_time, 2)
                })
                summary = cached["summary"]
                chunk_size = max(1, len(summary) // 30)
                for i in range(0, len(summary), chunk_size):
                    yield sse("token", {"token": summary[i:i+chunk_size]})
                yield sse("done", {
                    "url": url,
                    "content_length": cached.get("content_length", 0),
                    "elapsed": round(time.time() - start_time, 2),
                    "cached": True
                })
                return

        # 阶段 2: 多通道抓取
        yield sse("stage", {
            "stage": "fetch_start",
            "message": "正在抓取网页内容...",
            "elapsed": round(time.time() - start_time, 2)
        })

        try:
            content, channel = fetch_content(url)
        except Exception as e:
            yield sse("stage", {
                "stage": "error",
                "message": f"抓取失败: {str(e)}",
                "elapsed": round(time.time() - start_time, 2)
            })
            return

        if not content or len(content) < 10:
            yield sse("stage", {
                "stage": "error",
                "message": "无法获取有效的页面内容",
                "elapsed": round(time.time() - start_time, 2)
            })
            return

        yield sse("stage", {
            "stage": "fetch_done",
            "message": f"抓取完成，通过 [{channel}] 通道获取 {len(content)} 字符",
            "elapsed": round(time.time() - start_time, 2),
            "channel": channel,
            "content_length": len(content)
        })

        # 阶段 3: 调用模型生成摘要
        config = get_current_model_config()
        yield sse("stage", {
            "stage": "summarize_start",
            "message": f"正在调用 {config['name']} 生成摘要...",
            "elapsed": round(time.time() - start_time, 2),
            "model": config["model"]
        })

        full_summary = ""
        try:
            if config["provider"] == "ollama":
                for token, done in summarize_with_ollama_stream(content):
                    if token:
                        full_summary += token
                        yield sse("token", {"token": token})
                    if done:
                        break
            else:
                for token, done in summarize_with_openai_stream(content):
                    if token:
                        full_summary += token
                        yield sse("token", {"token": token})
                    if done:
                        break

        except requests.exceptions.ConnectionError:
            yield sse("stage", {
                "stage": "error",
                "message": "无法连接到模型服务，请检查网络或 API 配置",
                "elapsed": round(time.time() - start_time, 2)
            })
            return
        except Exception as e:
            yield sse("stage", {
                "stage": "error",
                "message": f"生成失败: {str(e)}",
                "elapsed": round(time.time() - start_time, 2)
            })
            return

        # 存入缓存
        with _cache_lock:
            _summary_cache[url] = {
                "summary": full_summary,
                "timestamp": time.time(),
                "content_length": len(content)
            }

        # 完成
        yield sse("done", {
            "url": url,
            "content_length": len(content),
            "elapsed": round(time.time() - start_time, 2),
            "cached": False,
            "channel": channel,
            "model": config["model"]
        })

    return Response(event_stream(), mimetype="text/event-stream")


# =================== Obsidian 集成 ====================

# 导入 Obsidian 集成模块
try:
    from obsidian_integration import ObsidianIntegration
    obsidian = ObsidianIntegration()
    OBSIDIAN_ENABLED = True
except Exception as e:
    print(f"⚠️  Obsidian 集成未启用: {e}")
    OBSIDIAN_ENABLED = False


@app.route("/api/obsidian/export", methods=["POST"])
def export_to_obsidian():
    """导出摘要到 Obsidian"""
    if not OBSIDIAN_ENABLED:
        return jsonify({"error": "Obsidian 集成未启用"}), 500

    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    url = data.get("url", "")
    summary = data.get("summary", "")
    model = data.get("model", "unknown")
    tags = data.get("tags", [])

    if not summary:
        return jsonify({"error": "摘要内容不能为空"}), 400

    try:
        result = obsidian.save_summary(title, url, summary, model, tags)
        return jsonify({
            "success": True,
            "message": "已导出到 Obsidian",
            "path": result["path"],
            "category": result["category"],
            "tags": result["tags"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/obsidian/auto-export", methods=["POST"])
def auto_export_to_obsidian():
    """自动导出（摘要完成后自动调用）"""
    if not OBSIDIAN_ENABLED:
        return jsonify({"skipped": True, "reason": "Obsidian 未启用"})

    data = request.get_json(silent=True) or {}
    title = data.get("title", "未命名摘要")
    url = data.get("url", "")
    summary = data.get("summary", "")
    model = data.get("model", "unknown")

    if not summary:
        return jsonify({"skipped": True, "reason": "摘要为空"})

    try:
        result = obsidian.save_summary(title, url, summary, model)
        return jsonify({
            "success": True,
            "path": result["path"],
            "category": result["category"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/obsidian/mindmap", methods=["GET"])
def get_mindmap():
    """获取思维导图数据"""
    if not OBSIDIAN_ENABLED:
        return jsonify({"error": "Obsidian 集成未启用"}), 500

    try:
        days = request.args.get("days", 30, type=int)
        mindmap_data = obsidian.generate_mindmap(days)
        markmap_text = obsidian.generate_markmap(days)

        return jsonify({
            "success": True,
            "data": mindmap_data,
            "markmap": markmap_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/obsidian/stats", methods=["GET"])
def get_obsidian_stats():
    """获取 Obsidian 统计信息"""
    if not OBSIDIAN_ENABLED:
        return jsonify({"error": "Obsidian 集成未启用"}), 500

    try:
        stats = obsidian.get_statistics()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/obsidian/classify", methods=["POST"])
def classify_content():
    """AI 自动分类"""
    if not OBSIDIAN_ENABLED:
        return jsonify({"error": "Obsidian 集成未启用"}), 500

    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    summary = data.get("summary", "")
    url = data.get("url", "")

    try:
        category = obsidian.classify_content(title, summary, url)
        tags = obsidian.extract_tags(title, summary, url)

        return jsonify({
            "success": True,
            "category": category,
            "tags": tags
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print_startup_info()
    if OBSIDIAN_ENABLED:
        print("📚 Obsidian 集成已启用")
        print(f"   Vault 路径: {obsidian.vault_path}")
        print(f"   摘要目录: {obsidian.summaries_path}")
    print()
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)
