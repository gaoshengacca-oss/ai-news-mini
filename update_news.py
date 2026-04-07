import os
import json
import time
import requests
import re
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动全网雷达：工业级 API 请求接入中...")

yesterday_ts = int(time.time()) - (24 * 3600)

# 👑 核心升级：使用 params 字典安全传递参数，彻底解决网址包含空格导致抓取失败的问题
url = "https://hn.algolia.com/api/v1/search"
params = {
    "query": "AI OR LLM OR ChatGPT OR model",
    "tags": "story",
    "numericFilters": f"created_at_i>{yesterday_ts}",
    "hitsPerPage": 15
}

candidates_text = ""
try:
    response = requests.get(url, params=params)
    response.raise_for_status() # 检查网络是否真正通畅
    hits = response.json().get("hits", [])
    
    for i, hit in enumerate(hits):
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        title = hit.get("title", "")
        candidates_text += f"[{i+1}] {title} (链接: {link})\n"
        
    print(f"📡 成功抓取 {len(hits)} 条原始情报。")
except Exception as e:
    print(f"❌ 网络抓取失败: {e}")

if candidates_text:
    print("🧠 正在呼叫 AI 主编...")
    
    prompt = f"""
    你是一名极其挑剔的硬核科技主编。
    以下是过去 24 小时内全网最热的 AI 新闻候选名单：
    {candidates_text}

    任务要求：
    1. 淘汰所有“言论”、“八卦”、“文章回顾”、“商业水文”。
    2. 只挑出 3 条纯正的“技术突破”、“新模型发布”、“硬核工具”。
    3. 如果连3条都没有，挑1-2条也可以，宁缺毋滥。
    4. 输出严格的 JSON 数组。

    格式要求（必须只返回这个格式）：
    [
        {{
            "title": "[硬核前沿] 中文标题",
            "summary": "一句话核心技术总结",
            "article": "300字通俗易懂的技术原理解析",
            "url": "原文链接"
        }}
    ]
    """
    
    try:
        # 使用稳定的闪电模型
        ai_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # 暴力提取 JSON
        match = re.search(r'\[.*\]', ai_response.text, re.DOTALL)
        
        if match:
            final_news_data = json.loads(match.group(0))
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(final_news_data, f, ensure_ascii=False, indent=4)
            print("✅ 引擎完美运转！成功提取并覆盖 data.json 文件。")
        else:
            print("❌ AI 返回格式异常，无法提取 JSON。")
            
    except Exception as e:
        print(f"❌ AI 接口调用失败: {e}")
else:
    print("⚠️ 没抓到新闻，本次不更新文件。")
