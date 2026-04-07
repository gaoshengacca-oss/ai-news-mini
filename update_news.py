import os
import json
import time
import requests
import re  # 👑 新增：引入强大的正则表达式工具
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动全网雷达：批量抓取，召唤 AI 主编进行硬核筛选...")

yesterday_ts = int(time.time()) - (24 * 3600)

try:
    url = f"https://hn.algolia.com/api/v1/search?query=AI OR LLM OR model OR release&tags=story&numericFilters=created_at_i>{yesterday_ts}&hitsPerPage=15"
    hits = requests.get(url).json().get("hits", [])
    
    candidates_text = ""
    for i, hit in enumerate(hits):
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        title = hit.get("title", "")
        candidates_text += f"[{i+1}] {title} (链接: {link})\n"
        
    print(f"📡 成功抓取 15 条原始情报。")
except Exception as e:
    print(f"❌ 抓取失败: {e}")
    candidates_text = ""

if candidates_text:
    print("🧠 正在将 15 条情报交由 AI 主编进行洗稿与筛选...")
    
    prompt = f"""
    你现在是一名极其挑剔的硬核科技主编。
    以下是过去 24 小时内全网最热的 15 条 AI/科技新闻候选名单：
    
    {candidates_text}

    请你执行以下极其严格的筛选和处理任务：
    1. 淘汰所有关于“CEO言论/八卦”、“政策监管”、“演讲”、“精选回顾”。
    2. 只挑出 3 条纯正的“技术突破”、“新模型发布”、“硬核开发工具”。
    3. 将选中的 3 条处理为中文，写一句话总结，以及300字内通俗科普。

    必须严格返回如下 JSON 格式数组（千万不要加其他任何废话）：
    [
        {{
            "title": "[硬核前沿] 中文标题",
            "summary": "一句话核心技术总结",
            "article": "通俗易懂的技术原理解析",
            "url": "选中的原文链接"
        }}
    ]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # 👑 核心绝杀：用正则暴力抠出 JSON 数组，无视前后废话！
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        
        if match:
            json_str = match.group(0)
            final_news_data = json.loads(json_str)
            
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(final_news_data, f, ensure_ascii=False, indent=4)
            print("✅ AI 主编筛选完毕！JSON 数据完美抠出，文件已更新。")
        else:
            print("❌ 哎呀，没找到 JSON 数组！AI 原话是：", response.text)
            
    except Exception as e:
        print(f"❌ 解析 AI 结果时报错了: {e}")
else:
    print("⚠️ 候选列表为空，退出程序。")
