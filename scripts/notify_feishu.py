#!/usr/bin/env python3
"""Send GitHub Trending report to Feishu via webhook."""
import urllib.request
import json
import os
from datetime import datetime

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def load_today_data():
    date = datetime.now().strftime("%Y-%m-%d")
    json_path = os.path.join(DATA_DIR, f"{date}.json")
    if not os.path.exists(json_path):
        return None
    with open(json_path, "r") as f:
        return json.load(f)

def build_card(data):
    """Build Feishu interactive card message."""
    new_repos = data.get("new", [])
    all_repos = data.get("all", [])
    date = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]
    
    # If there are new repos, show them; otherwise show all trending
    display_repos = new_repos if new_repos else all_repos
    label = "新发现" if new_repos else "上榜"
    
    recommended = [r for r in display_repos if r.get("tags")]
    others = [r for r in display_repos if not r.get("tags")]
    
    header = {
        "title": {"tag": "plain_text", "content": f"🔥 GitHub Trending 日报 | {date} {weekday}"},
        "template": "blue"
    }
    
    elements = []
    
    # Summary
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": f"今日 **{len(all_repos)}** 个项目{label}，其中 **{len(recommended)}** 个与你相关"}
    })
    elements.append({"tag": "hr"})
    
    # Recommended projects
    if recommended:
        content = "**⭐ 为你推荐**\n\n"
        for i, r in enumerate(recommended[:8], 1):
            tags = " ".join(f"`{t}`" for t in r.get("tags", []))
            stars = r.get("stars_today", 0)
            desc = r.get("cn", r.get("desc", ""))
            content += f"**{i}. [{r['name']}](https://github.com/{r['name']})** +{stars}⭐\n"
            content += f"{tags}\n"
            content += f"{desc}\n\n"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})
    
    # Other projects
    if others:
        elements.append({"tag": "hr"})
        content = "**📋 其他热门**\n\n"
        for i, r in enumerate(others[:5], 1):
            stars = r.get("stars_today", 0)
            desc = r.get("cn", r.get("desc", ""))
            content += f"{i}. [{r['name']}](https://github.com/{r['name']}) +{stars}⭐\n"
            content += f"   {desc}\n"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})
    
    # Footer
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": "📎 详细报告请查看 Obsidian/07-GitHub-Trending"}]
    })
    
    return {"msg_type": "interactive", "card": {"header": header, "elements": elements}}

def send_to_feishu(card):
    if not FEISHU_WEBHOOK:
        print("FEISHU_WEBHOOK not set, skipping notification")
        return False
    
    data = json.dumps(card).encode("utf-8")
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        print(f"Feishu response: {result}")
        return result.get("code") == 0 or result.get("StatusCode") == 0
    except Exception as e:
        print(f"Feishu send failed: {e}")
        return False

if __name__ == "__main__":
    data = load_today_data()
    if not data:
        print("No data found for today")
        exit(0)
    card = build_card(data)
    if FEISHU_WEBHOOK:
        send_to_feishu(card)
    else:
        print("Set FEISHU_WEBHOOK env to enable notifications")
        print(json.dumps(card, ensure_ascii=False, indent=2))
