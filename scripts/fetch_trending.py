#!/usr/bin/env python3
"""Fetch GitHub Trending with robust parsing, retry, dedup, and Chinese summaries."""
import urllib.request
import urllib.parse
import re
import os
import json
import time
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_DIR, "data")
DAILY_DIR = os.path.join(REPO_DIR, "daily")
KNOWN_FILE = os.path.join(DATA_DIR, "known_repos.json")

TOP_N = 30
MAX_RETRIES = 5
RETRY_BASE_DELAY = 3

INTEREST_KEYWORDS = {
    "边缘AI": ["edge ai", "edge computing", "embedded ai", "on-device", "edge inference", "tinyml", "microcontroller", "jetson", "raspberry pi", "mcu", "embedded ml"],
    "AI部署": ["deploy", "serving", "inference", "onnx", "tensorrt", "tflite", "quantiz", "distill", "runtime", "model serving", "optimization", "gguf", "llama.cpp", "vllm"],
    "AI Infra": ["infra", "mlops", "pipeline", "kubernetes", "k8s", "gpu cluster", "training infra", "distributed", "ray", "triton server", "scaling", "cluster"],
    "AI Agent": ["agent", "agentic", "tool use", "function call", "mcp", "autonomous", "multi-agent", "orchestrat", "langchain", "autogen", "crewai", "swarm", "reasoning"],
    "Vibe Coding": ["vibe cod", "cursor", "copilot", "windsurf", "cline", "aider", "devin", "coding agent", "code gen", "ai pair", "ai assist", "bolt"],
    "AI编程提效": ["ai cod", "code review", "code complet", "refactor", "test gen", "documentation gen", "code quality", "developer tool", "devex", "productivity"],
    "投资交易": ["trading", "quant", "backtest", "portfolio", "stock", "crypto", "defi", "strategy", "finance", "invest", "algotrading", "hedge", "market"],
    "AI for Science": ["science", "scientific", "molecule", "protein", "drug", "genomic", "bio", "chemistry", "physics", "material", "simulation", "foundation model for", "discovery", "research"],
}

CN_TEMPLATES = {
    "edge ai": "边缘AI推理框架，支持在移动/嵌入式设备上高效运行模型",
    "agent": "AI Agent 框架/工具，支持自主任务规划和执行",
    "deploy": "模型部署工具，简化AI模型的生产环境上线流程",
    "inference": "高性能推理引擎，优化模型推理速度和资源占用",
    "quantiz": "模型量化工具，大幅降低模型体积和计算需求",
    "serving": "模型服务化框架，提供标准化的模型API接口",
    "coding agent": "AI编程助手，支持代码生成、补全和智能重构",
    "code gen": "代码生成工具，用AI辅助提高开发效率",
    "trading": "量化交易工具/策略，可用于自动化投资决策",
    "research": "AI研究工具，辅助学术文献检索和知识发现",
    "science": "AI for Science 项目，用AI加速科学研究",
    "molecule": "分子模拟/药物发现AI工具",
    "protein": "蛋白质结构预测/分析AI工具",
    "foundation model": "基础模型，特定领域的大规模预训练模型",
    "scraper": "智能爬虫/数据采集工具",
    "llm": "大语言模型相关工具或资源",
    "rag": "检索增强生成(RAG)工具，提升LLM知识准确性",
    "vector": "向量数据库/嵌入检索工具",
    "cli": "命令行工具，提升终端工作效率",
    "framework": "开发框架，提供标准化的项目结构和工具链",
    "browser": "浏览器相关项目",
    "database": "数据库相关工具",
}

def fetch_with_retry(url, retries=MAX_RETRIES):
    """Fetch URL with exponential backoff retry."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html",
            })
            html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
            if len(html) < 1000:
                raise ValueError("Response too short, likely error page")
            return html
        except Exception as e:
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                print(f"  Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise

def parse_number(text):
    """Parse number from text like '1,234 stars today'."""
    if not text:
        return 0
    nums = re.sub(r'[^\d]', '', text)
    return int(nums) if nums else 0

def classify_repo(name, desc):
    text = f"{name} {desc}".lower()
    tags = []
    for tag, keywords in INTEREST_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                tags.append(tag)
                break
    return tags

def generate_cn_summary(name, desc, tags):
    text = f"{name} {desc}".lower()
    matched = []
    for kw, template in CN_TEMPLATES.items():
        if kw in text:
            matched.append(template)
            if len(matched) >= 2:
                break
    if matched:
        return "；".join(matched)
    if not desc or desc == "No description":
        return "暂无简介"
    return "GitHub 热门项目，详见英文简介"

def fetch_trending():
    print("Fetching GitHub Trending...")
    html = fetch_with_retry("https://github.com/trending")
    repos = []
    articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.DOTALL)
    print(f"Found {len(articles)} repos on trending page")

    for art in articles[:TOP_N]:
        name_m = re.search(r'<h2[^>]*>.*?<a[^>]*href="(/[^"]+)"', art, re.DOTALL)
        if not name_m:
            continue
        raw_path = name_m.group(1).strip()
        if "return_to=" in raw_path:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_path).query)
            if "return_to" in parsed:
                raw_path = parsed["return_to"][0]
        name = raw_path.strip("/")
        if not name or "/" not in name:
            continue

        desc_m = re.search(r'<p class="[^"]*col-9[^"]*">(.*?)</p>', art, re.DOTALL)
        desc = desc_m.group(1).strip() if desc_m else ""
        desc = re.sub(r'<[^>]+>', '', desc).strip()
        # Strip @mentions (from vitalets repo)
        desc = re.sub(r'(^|[^a-z0-9])@([a-z0-9-]+)', r'\1`@\2`', desc)

        stars_m = re.search(r'([\d,]+)\s+stars\s+today', art)
        stars_today = parse_number(stars_m.group(1)) if stars_m else 0

        lang_m = re.search(r'itemprop="programmingLanguage">(.*?)<', art)
        lang = lang_m.group(1) if lang_m else "N/A"

        # Total stars
        total_m = re.search(r'href="/[^"]+/stargazers"[^>]*>\s*([\d,]+)', art)
        total_stars = parse_number(total_m.group(1)) if total_m else 0

        # Forks
        fork_m = re.search(r'href="/[^"]+/forks"[^>]*>\s*([\d,]+)', art)
        forks = parse_number(fork_m.group(1)) if fork_m else 0

        tags = classify_repo(name, desc)
        cn = generate_cn_summary(name, desc, tags)

        repos.append({
            "name": name,
            "desc": desc[:200] if desc else "No description",
            "stars_today": stars_today,
            "total_stars": total_stars,
            "forks": forks,
            "lang": lang,
            "tags": tags,
            "cn": cn,
        })

    repos.sort(key=lambda r: r["stars_today"], reverse=True)
    return repos

def load_known_repos():
    """Load previously seen repos for deduplication."""
    if os.path.exists(KNOWN_FILE):
        with open(KNOWN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_known_repos(known):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(KNOWN_FILE, "w") as f:
        json.dump(known, f, ensure_ascii=False, indent=2)

def save_daily(repos, new_repos):
    date = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]

    os.makedirs(DAILY_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    recommended = [r for r in new_repos if r["tags"]]
    others = [r for r in new_repos if not r["tags"]]

    lines = [f"# GitHub Trending - {date} {weekday}\n"]
    lines.append(f"> 今日共 {len(repos)} 个项目上榜，其中 {len(new_repos)} 个为新发现项目\n")

    if recommended:
        lines.append(f"\n## ⭐ 为你推荐 ({len(recommended)} 个新项目)\n")
        for i, r in enumerate(recommended, 1):
            tag_str = " ".join(f"`{t}`" for t in r["tags"])
            stars_info = f"+{r['stars_today']}⭐ 今日 | {r['total_stars']:,}⭐ 总计 | {r['forks']:,}🍴"
            lines.append(f"### {i}. [{r['name']}](https://github.com/{r['name']})")
            lines.append(f"- 语言: {r['lang']} | {stars_info}")
            lines.append(f"- 标签: {tag_str}")
            lines.append(f"- 简介: {r['desc']}")
            lines.append(f"- 🇨🇳 {r['cn']}\n")

    if others:
        lines.append(f"\n## 📋 其他新项目 ({len(others)} 个)\n")
        for i, r in enumerate(others, 1):
            stars_info = f"+{r['stars_today']}⭐ 今日 | {r['total_stars']:,}⭐ 总计"
            lines.append(f"### {i}. [{r['name']}](https://github.com/{r['name']})")
            lines.append(f"- 语言: {r['lang']} | {stars_info}")
            lines.append(f"- 简介: {r['desc']}")
            lines.append(f"- 🇨🇳 {r['cn']}\n")

    if not new_repos:
        lines.append("\n> 今日无新发现项目，所有上榜项目此前已推送过。\n")

    daily_path = os.path.join(DAILY_DIR, f"{date} GitHub Trending.md")
    with open(daily_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Save raw JSON
    json_path = os.path.join(DATA_DIR, f"{date}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"all": repos, "new": new_repos}, f, ensure_ascii=False, indent=2)

    return daily_path

if __name__ == "__main__":
    repos = fetch_trending()
    print(f"Total trending repos: {len(repos)}")

    # Deduplication
    known = load_known_repos()
    new_repos = []
    for r in repos:
        if r["name"] not in known:
            new_repos.append(r)
            known[r["name"]] = {"first_seen": datetime.now().isoformat(), "tags": r["tags"]}

    print(f"New repos: {len(new_repos)} (skipped {len(repos) - len(new_repos)} known)")

    # Save
    save_known_repos(known)
    path = save_daily(repos, new_repos)
    print(f"Saved: {path}")
