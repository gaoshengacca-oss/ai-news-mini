import os
import json
import time
import requests
import re
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动省电多源雷达：HN + Dev.to + GitHub...")

def fetch_raw_data():
    candidates = []
    # 关键词黑名单：Python 预处理，不花 Token！
    blacklist = ["CEO", "Elon Musk", "Sam Altman", "Lawsuit", "Regulatory", "Investment", "Review"]
    
    # 1. Hacker News (Top 10)
    try:
        hn_res = requests.get("https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=10", timeout=10)
        for hit in hn_res.json().get("hits", []):
            candidates.append({"title": hit['title'], "url": hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"})
    except: print("HN 抓取跳过")

    # 2. Dev.to (Top 10)
    try:
        dev_res = requests.get("https://dev.to/api/articles?top=1&per_page=10", timeout=10)
        for art in dev_res.json():
            candidates.append({"title": art['title'], "url": art['url']})
    except: print("Dev.to 抓取跳过")

    # 简单过滤
    filtered = [c for c in candidates if not any(word.lower() in c['title'].lower() for word in blacklist)]
    return filtered[:20] # 👑 严格控制总量在 20 条以内，极度节省 Token

# 执行抓取
news_pool = fetch_raw_data()
pool_text = ""
for i, item in enumerate(news_pool):
    pool_text += f"[{i+1}] {item['title']} (URL: {item['url']})\n"

if pool_text:
    print(f"📡 预过滤后剩余 {len(news_pool)} 条精品候选。等待 5s 避开频率限制...")
    time.sleep(5)
    
    try:
        # 使用 1.5-flash，额度更高，解析 20 条速度极快
        ai_response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents="你是硬核主编，从下面列表选3条真正的技术发布或突破，以JSON格式输出：\n" + pool_text
        )
        
        match = re.search(r'\[.*\]', ai_response.text, re.DOTALL)
        if match:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(json.loads(match.group(0)), f, ensure_ascii=False, indent=4)
            print("✅ 任务圆满完成！多源数据已入库。")
    except Exception as e:
        print(f"❌ AI 还是报错了: {e}")
