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

    def _find_related_notes(self, tags, category, current_file=None):
        """基于标签和分类查找关联笔记"""
        related = []
        for cat in self.CATEGORIES.keys():
            cat_path = self.summaries_path / cat
            if not cat_path.exists():
                continue
            for md_file in cat_path.glob("*.md"):
                if current_file and md_file.name == current_file:
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8")
                    if not content.startswith("---"):
                        continue
                    end_idx = content.index("---", 3)
                    frontmatter = content[3:end_idx]

                    title_match = re.search(r'title:\s*"(.+?)"', frontmatter)
                    file_tags_match = re.search(r'tags:\s*\[(.+?)\]', frontmatter)
                    if not title_match:
                        continue

                    file_title = title_match.group(1)
                    file_tags = []
                    if file_tags_match:
                        file_tags = [t.strip().strip('"') for t in file_tags_match.group(1).split(",")]

                    # 计算关联分数：共享标签 + 同分类
                    score = len(set(tags) & set(file_tags)) * 2
                    if cat == category:
                        score += 1

                    if score > 0:
                        related.append({
                            "title": file_title,
                            "file": md_file.stem,
                            "category": cat,
                            "score": score,
                            "shared_tags": list(set(tags) & set(file_tags))
                        })
                except Exception:
                    continue

        # 按关联分数排序，取前 5 个
        related.sort(key=lambda x: x["score"], reverse=True)
        return related[:5]

    def generate_markdown(self, title, url, summary, model="unknown", extra_tags=None):
        """生成 Obsidian Markdown 文件（带 wikilinks 关联）"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # 自动分类
        category = self.classify_content(title, summary, url)

        # 提取标签
        tags = self.extract_tags(title, summary, url)
        if extra_tags:
            tags.extend(extra_tags)
        tags = list(set(tags))[:8]

        # 提取关键要点
        key_points = self.extract_key_points(summary)
        key_points_text = "\n- ".join(key_points) if key_points else "待提取"

        # 生成文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
        filename = f"{date_str}-{safe_title}.md"

        # 查找关联笔记
        related = self._find_related_notes(tags, category, filename)
        related_links = ""
        if related:
            for r in related:
                shared = ", ".join(r["shared_tags"]) if r["shared_tags"] else r["category"]
                related_links += f"- [[{r['file']}|{r['title']}]] _({shared})_\n"
        else:
            related_links = "- _暂无关联笔记，添加更多摘要后自动生成_\n"

        # 标签 wikilinks
        tag_links = ", ".join([f'[[#{tag}|{tag}]]' for tag in tags])

        # 分类索引链接
        category_link = f"[[{category}-index|{category}]]"

        # 生成标签字符串
        tags_str = ", ".join([f'"{tag}"' for tag in tags])

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
| 📂 分类 | {category_link} |
| 🏷️ 标签 | {tag_links} |

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

## 🔗 关联笔记

{related_links}

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
            "related": [r["file"] for r in related],
            "markdown": markdown
        }

    def save_summary(self, title, url, summary, model="unknown", extra_tags=None):
        """保存摘要到 Obsidian Vault，并更新索引页"""
        result = self.generate_markdown(title, url, summary, model, extra_tags)

        # 保存文件
        file_path = self.summaries_path / result["category"] / result["filename"]
        file_path.write_text(result["markdown"], encoding="utf-8")

        # 更新分类索引和标签索引
        self._update_category_index(result["category"])
        for tag in result["tags"]:
            self._update_tag_index(tag)
        self._update_overview()

        return {
            "path": str(file_path),
            "category": result["category"],
            "tags": result["tags"],
            "filename": result["filename"],
            "related": result.get("related", [])
        }

    def _get_all_notes(self):
        """获取所有摘要笔记的元数据"""
        notes = []
        for category in self.CATEGORIES.keys():
            cat_path = self.summaries_path / category
            if not cat_path.exists():
                continue
            for md_file in cat_path.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    if not content.startswith("---"):
                        continue
                    end_idx = content.index("---", 3)
                    frontmatter = content[3:end_idx]

                    title_match = re.search(r'title:\s*"(.+?)"', frontmatter)
                    date_match = re.search(r'date:\s*"(.+?)"', frontmatter)
                    tags_match = re.search(r'tags:\s*\[(.+?)\]', frontmatter)
                    model_match = re.search(r'model:\s*"(.+?)"', frontmatter)
                    status_match = re.search(r'status:\s*"(.+?)"', frontmatter)
                    rating_match = re.search(r'rating:\s*(\d+)', frontmatter)

                    if not title_match:
                        continue

                    file_tags = []
                    if tags_match:
                        file_tags = [t.strip().strip('"') for t in tags_match.group(1).split(",")]

                    notes.append({
                        "title": title_match.group(1),
                        "file": md_file.stem,
                        "category": category,
                        "date": date_match.group(1) if date_match else "",
                        "tags": file_tags,
                        "model": model_match.group(1) if model_match else "",
                        "status": status_match.group(1) if status_match else "unread",
                        "rating": int(rating_match.group(1)) if rating_match else 0,
                    })
                except Exception:
                    continue
        return notes

    def _update_category_index(self, category):
        """更新分类索引页"""
        notes = self._get_all_notes()
        cat_notes = [n for n in notes if n["category"] == category]
        cat_notes.sort(key=lambda x: x["date"], reverse=True)

        cat_names = {
            "tech": "💻 技术", "ai": "🤖 AI/ML", "devops": "🔧 运维",
            "news": "📰 新闻", "academic": "📚 学术", "other": "📦 其他"
        }
        cat_name = cat_names.get(category, category)

        links = []
        for n in cat_notes:
            rating_stars = "⭐" * n["rating"] if n["rating"] > 0 else "—"
            status_icon = "✅" if n["status"] == "read" else "📖"
            tag_str = " ".join([f'`{t}`' for t in n["tags"][:3]])
            links.append(f"| [[{n['file']}|{n['title']}]] | {n['date']} | {tag_str} | {rating_stars} | {status_icon} |")

        table = "\n".join(links) if links else "| _暂无笔记_ | — | — | — | — |"

        content = f"""---
title: "{cat_name} 索引"
type: "index"
category: "{category}"
---

# {cat_name}

> 📂 共 {len(cat_notes)} 篇摘要 | [[📊 摘要总览|返回总览]]

| 标题 | 日期 | 标签 | 评分 | 状态 |
|------|------|------|------|------|
{table}

---

```dataview
TABLE WITHOUT ID
  file.link as "文件",
  date as "日期",
  tags as "标签",
  rating as "评分"
FROM "Web Summaries/{category}"
SORT date DESC
```
"""
        index_path = self.summaries_path / f"{category}-index.md"
        index_path.write_text(content, encoding="utf-8")

    def _update_tag_index(self, tag):
        """更新标签索引页"""
        notes = self._get_all_notes()
        tag_notes = [n for n in notes if tag in n["tags"]]
        tag_notes.sort(key=lambda x: x["date"], reverse=True)

        links = []
        for n in tag_notes:
            cat_link = f"[[{n['category']}-index|{n['category']}]]"
            links.append(f"| [[{n['file']}|{n['title']}]] | {n['date']} | {cat_link} |")

        table = "\n".join(links) if links else "| _暂无笔记_ | — | — |"

        content = f"""---
title: "🏷️ {tag}"
type: "tag-index"
tag: "{tag}"
---

# 🏷️ {tag}

> 共 {len(tag_notes)} 篇相关摘要 | [[📊 摘要总览|返回总览]]

| 标题 | 日期 | 分类 |
|------|------|------|
{table}
"""
        tag_dir = self.summaries_path / ".tags"
        tag_dir.mkdir(exist_ok=True)
        tag_path = tag_dir / f"{tag}.md"
        tag_path.write_text(content, encoding="utf-8")

    def _update_overview(self):
        """更新总览页"""
        notes = self._get_all_notes()
        total = len(notes)

        # 分类统计
        cat_counts = {}
        for n in notes:
            cat_counts[n["category"]] = cat_counts.get(n["category"], 0) + 1

        cat_rows = []
        cat_names = {
            "tech": "💻 技术", "ai": "🤖 AI/ML", "devops": "🔧 运维",
            "news": "📰 新闻", "academic": "📚 学术", "other": "📦 其他"
        }
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            cat_rows.append(f"| [[{cat}-index|{cat_names.get(cat, cat)}]] | {count} |")

        # 标签统计
        tag_counts = {}
        for n in notes:
            for t in n["tags"]:
                tag_counts[t] = tag_counts.get(t, 0) + 1

        tag_rows = []
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:10]:
            tag_rows.append(f"| [[.tags/{tag}|{tag}]] | {count} |")

        # 最近笔记
        recent = sorted(notes, key=lambda x: x["date"], reverse=True)[:10]
        recent_rows = []
        for n in recent:
            cat_link = f"[[{n['category']}-index|{n['category']}]]"
            recent_rows.append(f"| [[{n['file']}|{n['title']}]] | {n['date']} | {cat_link} |")

        cat_table = "\n".join(cat_rows) if cat_rows else "| _暂无_ | 0 |"
        tag_table = "\n".join(tag_rows) if tag_rows else "| _暂无_ | 0 |"
        recent_table = "\n".join(recent_rows) if recent_rows else "| _暂无_ | — | — |"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        content = f"""---
title: "📊 摘要总览"
type: "overview"
---

# 📊 摘要总览

> 共 **{total}** 篇摘要 | 最后更新: {now_str}

---

## 📂 分类导航

| 分类 | 数量 |
|------|------|
{cat_table}

---

## 🏷️ 热门标签

| 标签 | 关联数 |
|------|--------|
{tag_table}

---

## 📅 最近摘要

| 标题 | 日期 | 分类 |
|------|------|------|
{recent_table}

---

## 🔍 高级查询

```dataview
TABLE WITHOUT ID
  file.link as "文件",
  date as "日期",
  category as "分类",
  tags as "标签",
  rating as "评分",
  status as "状态"
FROM "Web Summaries"
WHERE source = "web-summarizer"
SORT date DESC
LIMIT 20
```

### ⭐ 高评分

```dataview
TABLE WITHOUT ID
  file.link as "文件",
  rating as "评分",
  category as "分类"
FROM "Web Summaries"
WHERE rating >= 4
SORT rating DESC
```

### 📖 未读

```dataview
TABLE WITHOUT ID
  file.link as "文件",
  date as "日期",
  category as "分类"
FROM "Web Summaries"
WHERE status = "unread"
SORT date DESC
```
"""
        overview_path = self.summaries_path / "📊 摘要总览.md"
        overview_path.write_text(content, encoding="utf-8")

    def rebuild_all_indexes(self):
        """重建所有索引页"""
        notes = self._get_all_notes()

        # 更新所有分类索引
        for category in self.CATEGORIES.keys():
            self._update_category_index(category)

        # 更新所有标签索引
        all_tags = set()
        for n in notes:
            all_tags.update(n["tags"])
        for tag in all_tags:
            self._update_tag_index(tag)

        # 更新总览
        self._update_overview()

        return {
            "total_notes": len(notes),
            "categories": len([c for c in self.CATEGORIES.keys() if (self.summaries_path / c).exists()]),
            "tags": len(all_tags)
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
