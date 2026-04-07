import os
import json
import time
import requests
import re
from google import genai

# 1. 密钥与客户端
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动生存主义雷达：只抓 15 条，死守额度...")

# 2. 抓取逻辑
yesterday_ts = int(time.time()) - (24 * 3600)
url = "https://hn.algolia.com/api/v1/search_by_date"
params = {"tags": "story", "numericFilters": f"created_at_i>{yesterday_ts}", "hitsPerPage": 15}

candidates = []
try:
    res = requests.get(url, params=params, timeout=10)
    hits = res.json().get("hits", [])
    for i, hit in enumerate(hits):
        candidates.append({
            "id": i+1,
            "title": hit.get("title", "无标题"),
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        })
    print(f"📡 成功带回 {len(candidates)} 条候选。")
except Exception as e:
    print(f"❌ 抓取失败: {e}")

if candidates:
    # 3. 极度克制的投喂
    # 我们只把序号和标题发给 AI，不发链接，省下巨额 Token！
    pool_text = ""
    for c in candidates:
        pool_text += f"{c['id']}. {c['title']}\n"

    print("⏳ 进入 20s 深度睡眠，躲避谷歌额度检查...")
    time.sleep(20) 
    
    print("🧠 召唤 2.0-Flash 主编进行硬核筛选...")
    
    prompt = f"""
    你是硬核科技主编。从下面标题中选3个最硬核的技术突破，严格输出JSON。
    不要八卦，不要CEO言论。
    
    【候选标题】：
    {pool_text}

    【输出格式】：
    [
        {{"index": 选中序号, "title": "地道中文标题", "summary": "硬核总结", "article": "300字通俗科普"}}
    ]
    """
    
    try:
        # 回归 2.0，因为它的地址在库里最稳
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            # 4. 二次对齐：根据 AI 选的序号，把对应的 URL 补回来
            ai_data = json.loads(match.group(0))
            final_data = []
            for item in ai_data:
                # 找到原始链接
                idx = item.get("index", 1) - 1
                original_url = candidates[idx]["url"] if idx < len(candidates) else "#"
                final_data.append({
                    "title": item["title"],
                    "summary": item["summary"],
                    "article": item["article"],
                    "url": original_url
                })
            
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print("✅ 任务完美达成！额度保住了，数据更新了。")
        else:
            print("❌ AI 没按格式说话。")
    except Exception as e:
        print(f"❌ AI 环节还是报错: {e}")
