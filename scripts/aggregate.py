#!/usr/bin/env python3
"""Aggregate daily trending data into weekly/monthly reports with trend analysis."""
import os
import json
from datetime import datetime, timedelta
from collections import Counter

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_DIR, "data")
WEEKLY_DIR = os.path.join(REPO_DIR, "weekly")
MONTHLY_DIR = os.path.join(REPO_DIR, "monthly")

def load_daily_data(days):
    """Load daily JSON data for the past N days."""
    all_repos = []
    today = datetime.now()
    loaded_days = 0
    for i in range(days):
        d = today - timedelta(days=i)
        json_path = os.path.join(DATA_DIR, f"{d.strftime('%Y-%m-%d')}.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
                repos = data.get("new", data if isinstance(data, list) else [])
                for r in repos:
                    r["date"] = d.strftime("%Y-%m-%d")
                all_repos.extend(repos)
                loaded_days += 1
    return all_repos, loaded_days

def generate_report(days, period_name):
    """Generate weekly or monthly report."""
    repos, loaded_days = load_daily_data(days)
    if not repos:
        print(f"No data found for the past {days} days.")
        return

    # Stats
    repo_freq = Counter()
    repo_info = {}
    for r in repos:
        repo_freq[r["name"]] += 1
        repo_info[r["name"]] = r

    tag_freq = Counter()
    for r in repos:
        for t in r.get("tags", []):
            tag_freq[t] += 1

    lang_freq = Counter(r.get("lang", "N/A") for r in repos)
    stars_by_repo = {}
    for r in repos:
        name = r["name"]
        if name not in stars_by_repo:
            stars_by_repo[name] = 0
        stars_by_repo[name] += r.get("stars_today", 0)

    # Persistent repos (appeared multiple days)
    persistent = [(name, count) for name, count in repo_freq.items() if count >= 2]
    persistent.sort(key=lambda x: x[1], reverse=True)

    # Top repos by total star gain
    top_by_stars = sorted(stars_by_repo.items(), key=lambda x: x[1], reverse=True)[:15]

    # Build markdown
    date = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# GitHub Trending {period_name}报 - {date}\n"]
    lines.append(f"> 数据覆盖 {loaded_days} 天，共 {len(repos)} 条记录，涉及 {len(set(r['name'] for r in repos))} 个独立项目\n")

    # Top projects
    lines.append(f"\n## 🏆 本期 TOP 15 项目\n")
    for i, (name, total_stars) in enumerate(top_by_stars, 1):
        r = repo_info[name]
        freq = repo_freq[name]
        tags = " ".join(f"`{t}`" for t in r.get("tags", []))
        freq_note = f" (出现{freq}天)" if freq > 1 else ""
        lines.append(f"### {i}. [{name}](https://github.com/{name}){freq_note}")
        lines.append(f"- 语言: {r.get('lang', 'N/A')} | 累计 +{total_stars:,}⭐ | 标签: {tags}")
        lines.append(f"- 🇨🇳 {r.get('cn', '暂无简介')}\n")

    # Persistent hot repos
    if persistent:
        lines.append(f"\n## 🔥 持续热门（出现2天以上）\n")
        for name, count in persistent[:10]:
            r = repo_info[name]
            tags = " ".join(f"`{t}`" for t in r.get("tags", []))
            lines.append(f"- **[{name}](https://github.com/{name})** x{count}天 {tags}")
            lines.append(f"  {r.get('cn', '')}\n")

    # Tag analysis
    lines.append(f"\n## 🏷️ 兴趣方向热度\n")
    total_tags = sum(tag_freq.values())
    for tag, count in tag_freq.most_common():
        pct = count / total_tags * 100 if total_tags else 0
        bar = "█" * min(count, 20)
        lines.append(f"- **{tag}**: {count}次 ({pct:.0f}%) {bar}")

    # Language distribution
    lines.append(f"\n## 💻 编程语言分布\n")
    for lang, count in lang_freq.most_common(10):
        bar = "█" * min(count, 20)
        lines.append(f"- **{lang}**: {count}个 {bar}")

    # Save
    if period_name == "周":
        out_dir = WEEKLY_DIR
    else:
        out_dir = MONTHLY_DIR
    os.makedirs(out_dir, exist_ok=True)

    filepath = os.path.join(out_dir, f"{date} {period_name}报.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved: {filepath}")

if __name__ == "__main__":
    import sys
    period = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    if period == "weekly":
        generate_report(7, "周")
    elif period == "monthly":
        generate_report(30, "月")
    else:
        print(f"Unknown period: {period}. Use 'weekly' or 'monthly'.")
