import os
import json
import time
import requests
import re
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动广域搜索模式：直接抓取全网 Top 50 原始新闻...")

# 核心策略：不再搜索关键词，而是抓取过去 24 小时所有的 Top 故事
yesterday_ts = int(time.time()) - (24 * 3600)
url = "https://hn.algolia.com/api/v1/search_by_date" # 👑 改用按日期排序，保证新鲜
params = {
    "tags": "story",
    "numericFilters": f"created_at_i>{yesterday_ts}",
    "hitsPerPage": 50 # 👑 一口气撒大网，抓 50 条！
}

candidates_text = ""
try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    hits = response.json().get("hits", [])
    
    for i, hit in enumerate(hits):
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        title = hit.get("title", "")
        candidates_text += f"[{i+1}] {title} (URL: {link})\n"
        
    print(f"📡 原始网捕完成，成功带回 {len(hits)} 条候选情报。")
except Exception as e:
    print(f"❌ 抓取失败: {e}")

if candidates_text:
    print("🧠 召唤 AI 主编进行深度语义筛选...")
    
    # 注入我们设计的双语硬核 Prompt
    prompt = f"""
    你现在是一名拥有 20 年经验的硬核科技主编。
    我会给你 50 条过去 24 小时全球最热的科技新闻标题。
    
    【候选名单】：
    {candidates_text}

    【筛选任务】：
    1. 过滤：彻底剔除所有“言论八卦”、“CEO 动态”、“政策法规”、“融资传闻”、“文章回顾”。
    2. 筛选：挑选出 3 条最具“技术硬核度”或“行业颠覆性”的新闻（重点关注 AI、芯片、机器人、硬核开源工具）。
    3. 转化：将选中的新闻处理为地道中文标题，撰写一句话技术总结(summary)，以及一段给普通人看的技术解析(article)。

    【输出要求】：严格返回 JSON 数组，不要任何 markdown 标记。格式如下：
    [
        {{
            "title": "[硬核前沿] 中文标题",
            "summary": "一句话核心技术总结",
            "article": "300字内技术原理解析",
            "url": "原文链接"
        }}
    ]
    """
    
    try:
        ai_response = client.models.generate_content(
            model='gemini-2.0-flash', # 👑 使用响应最快的 2.0 模型
            contents=prompt
        )
        
        # 暴力提取 JSON
        match = re.search(r'\[.*\]', ai_response.text, re.DOTALL)
        
        if match:
            final_news_data = json.loads(match.group(0))
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(final_news_data, f, ensure_ascii=False, indent=4)
            print(f"✅ 筛选成功！AI 已从 50 条中精准锁定了 {len(final_news_data)} 条技术干货。")
        else:
            print("❌ AI 结果解析失败，未发现有效 JSON。")
            
    except Exception as e:
        print(f"❌ AI 接口故障: {e}")
else:
    print("⚠️ 过去 24 小时全网无新动态（这基本不可能发生）。")
