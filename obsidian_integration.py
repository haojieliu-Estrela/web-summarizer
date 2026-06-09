"""
Obsidian 集成模块
功能：将网页摘要导出到 Obsidian Vault
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path


class ObsidianIntegration:
    """Obsidian 集成类"""

    # 默认分类
    CATEGORIES = {
        "tech": ["python", "javascript", "java", "golang", "rust", "c++", "编程", "开发", "代码", "github", "gitlab"],
        "ai": ["ai", "人工智能", "机器学习", "深度学习", "llm", "大模型", "gpt", "openai", "transformer", "神经网络"],
        "devops": ["docker", "kubernetes", "k8s", "ci/cd", "devops", "运维", "部署", "容器", "微服务"],
        "news": ["新闻", "资讯", "动态", "发布", "更新", "公告"],
        "academic": ["论文", "研究", "学术", "arxiv", "期刊", "会议", "实验"],
        "other": []
    }

    def __init__(self, vault_path=None):
        """初始化 Obsidian 集成"""
        if vault_path is None:
            # 默认 Vault 路径
            vault_path = os.path.expanduser("~/Documents/Obsidian Vault")

        self.vault_path = Path(vault_path)
        self.summaries_path = self.vault_path / "Web Summaries"
        self.templates_path = self.summaries_path / ".templates"
        self.mindmap_path = self.summaries_path / ".mindmap"

        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保目录结构存在"""
        self.summaries_path.mkdir(parents=True, exist_ok=True)

        # 创建分类目录
        for category in self.CATEGORIES.keys():
            (self.summaries_path / category).mkdir(exist_ok=True)

        # 创建模板和思维导图目录
        self.templates_path.mkdir(exist_ok=True)
        self.mindmap_path.mkdir(exist_ok=True)

    def classify_content(self, title, summary, url=""):
        """AI 自动分类"""
        text = f"{title} {summary} {url}".lower()

        # 计算每个分类的匹配分数
        scores = {}
        for category, keywords in self.CATEGORIES.items():
            if category == "other":
                continue
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score

        # 返回得分最高的分类
        if scores:
            return max(scores, key=scores.get)
        return "other"

    def extract_tags(self, title, summary, url=""):
        """提取标签"""
        text = f"{title} {summary} {url}".lower()

        # 常见技术标签
        tech_tags = [
            "python", "javascript", "java", "golang", "rust", "typescript",
            "react", "vue", "angular", "node", "django", "flask", "fastapi",
            "docker", "kubernetes", "aws", "azure", "gcp",
            "ai", "ml", "llm", "gpt", "openai", "transformer",
            "database", "mysql", "postgresql", "mongodb", "redis",
            "git", "github", "gitlab", "ci/cd", "devops",
            "api", "rest", "graphql", "microservices",
            "security", "authentication", "authorization"
        ]

        tags = []
        for tag in tech_tags:
            if tag in text:
                tags.append(tag)

        # 限制标签数量
        return tags[:8]

    def extract_key_points(self, summary):
        """提取关键要点"""
        # 简单提取：按行分割，取前 5 个要点
        lines = summary.split('\n')
        key_points = []

        for line in lines:
            line = line.strip()
            # 跳过空行和标题
            if not line or line.startswith('#'):
                continue
            # 提取列表项
            if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                key_points.append(line[2:].strip())
            # 提取数字列表
            elif re.match(r'^\d+[\.\)]\s', line):
                key_points.append(re.sub(r'^\d+[\.\)]\s', '', line).strip())

        # 如果没有找到列表项，取前 3 句话
        if not key_points:
            sentences = re.split(r'[。！？.!?]', summary)
            key_points = [s.strip() for s in sentences if len(s.strip()) > 10][:3]

        return key_points[:5]

    def generate_markdown(self, title, url, summary, model="unknown", extra_tags=None):
        """生成 Obsidian Markdown 文件"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # 自动分类
        category = self.classify_content(title, summary, url)

        # 提取标签
        tags = self.extract_tags(title, summary, url)
        if extra_tags:
            tags.extend(extra_tags)
        tags = list(set(tags))[:8]  # 去重并限制数量

        # 提取关键要点
        key_points = self.extract_key_points(summary)
        key_points_text = "\n- ".join(key_points) if key_points else "待提取"

        # 生成文件名（去除特殊字符）
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
        filename = f"{date_str}-{safe_title}.md"

        # 生成标签字符串
        tags_str = ", ".join([f'"{tag}"' for tag in tags])

        # 生成 Markdown 内容
        markdown = f"""---
title: "{title}"
url: "{url}"
date: "{date_str}"
time: "{time_str}"
category: "{category}"
tags: [{tags_str}]
model: "{model}"
source: "web-summarizer"
status: "unread"
rating: 0
---

# {title}

## 📋 基本信息

| 属性 | 值 |
|------|-----|
| 🔗 链接 | [原文]({url}) |
| 📅 日期 | {date_str} |
| ⏰ 时间 | {time_str} |
| 🤖 模型 | {model} |
| 📂 分类 | {category} |
| 🏷️ 标签 | {', '.join(tags)} |

---

## 📝 摘要内容

{summary}

---

## 🔍 关键要点

- {key_points_text}

---

## 💡 个人笔记

> 在这里添加你的想法和笔记...



---

## 🔗 相关链接

- 

---

## 📊 元数据

```dataview
TABLE WITHOUT ID
  file.link as "文件",
  date as "日期",
  category as "分类",
  model as "模型",
  rating as "评分"
WHERE file.name = this.file.name
```
"""
        return {
            "filename": filename,
            "category": category,
            "tags": tags,
            "markdown": markdown
        }

    def save_summary(self, title, url, summary, model="unknown", extra_tags=None):
        """保存摘要到 Obsidian Vault"""
        result = self.generate_markdown(title, url, summary, model, extra_tags)

        # 保存文件
        file_path = self.summaries_path / result["category"] / result["filename"]
        file_path.write_text(result["markdown"], encoding="utf-8")

        return {
            "path": str(file_path),
            "category": result["category"],
            "tags": result["tags"],
            "filename": result["filename"]
        }

    def generate_mindmap(self, days=30):
        """生成思维导图数据"""
        from collections import defaultdict

        # 收集所有摘要
        summaries = []
        for category in self.CATEGORIES.keys():
            category_path = self.summaries_path / category
            if not category_path.exists():
                continue

            for md_file in category_path.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    # 提取 frontmatter
                    if content.startswith("---"):
                        end_idx = content.index("---", 3)
                        frontmatter = content[3:end_idx]
                        # 简单解析
                        title_match = re.search(r'title:\s*"(.+?)"', frontmatter)
                        if title_match:
                            summaries.append({
                                "title": title_match.group(1),
                                "category": category,
                                "file": md_file.name
                            })
                except Exception:
                    continue

        # 按分类组织
        mindmap_data = {
            "name": "网页摘要知识图谱",
            "children": []
        }

        category_groups = defaultdict(list)
        for s in summaries:
            category_groups[s["category"]].append(s)

        for category, items in category_groups.items():
            category_node = {
                "name": f"{category} ({len(items)})",
                "children": [{"name": item["title"]} for item in items[:10]]
            }
            mindmap_data["children"].append(category_node)

        return mindmap_data

    def generate_markmap(self, days=30):
        """生成 Markmap 格式的思维导图"""
        mindmap_data = self.generate_mindmap(days)

        lines = ["# 网页摘要知识图谱", ""]

        for category in mindmap_data.get("children", []):
            lines.append(f"## {category['name']}")
            for item in category.get("children", []):
                lines.append(f"- {item['name']}")
            lines.append("")

        return "\n".join(lines)

    def get_statistics(self):
        """获取统计信息"""
        stats = {
            "total": 0,
            "by_category": {},
            "by_model": {},
            "by_date": {}
        }

        for category in self.CATEGORIES.keys():
            category_path = self.summaries_path / category
            if not category_path.exists():
                continue

            files = list(category_path.glob("*.md"))
            stats["by_category"][category] = len(files)
            stats["total"] += len(files)

        return stats


# 命令行接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian 集成工具")
    parser.add_argument("--mindmap", action="store_true", help="生成思维导图")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--vault", type=str, help="Obsidian Vault 路径")

    args = parser.parse_args()

    # 初始化
    integration = ObsidianIntegration(args.vault)

    if args.mindmap:
        markmap = integration.generate_markmap()
        print(markmap)

        # 保存到文件
        output_path = integration.mindmap_path / "knowledge-graph.md"
        output_path.write_text(markmap, encoding="utf-8")
        print(f"\n✅ 思维导图已保存到: {output_path}")

    elif args.stats:
        stats = integration.get_statistics()
        print("\n📊 摘要统计信息")
        print("=" * 40)
        print(f"总数: {stats['total']}")
        print("\n按分类:")
        for cat, count in stats["by_category"].items():
            print(f"  {cat}: {count}")

    else:
        parser.print_help()
