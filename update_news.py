import os
import json
import time
import requests
from google import genai

# 1. 提取大模型密钥
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动全网雷达：批量抓取，召唤 AI 主编进行硬核筛选...")

# 2. 准备抓取：过去 24 小时的时间戳
yesterday_ts = int(time.time()) - (24 * 3600)

# 我们直接从最硬核的 Hacker News 一口气抓取 15 条包含 AI/LLM 的最新热门
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
    
    # 3. 核心魔法：用极其严苛的 Prompt 逼迫大模型做质量控制
    prompt = f"""
    你现在是一名极其挑剔的硬核科技主编。
    以下是过去 24 小时内全网最热的 15 条 AI/科技新闻候选名单：
    
    {candidates_text}

    请你执行以下极其严格的筛选和处理任务：
    1. 【核心过滤】：立刻淘汰所有关于“CEO言论/八卦（比如萨姆·奥特曼说了什么）”、“政策监管”、“某某人演讲”、“每周精选/文章回顾”、“无聊的商业收购”的内容。
    2. 【精准挑选】：在这 15 条中，只挑出 3 条纯正的“技术突破”、“新模型发布”、“硬核开发工具”、“颠覆性科技事件”。
    3. 【重写输出】：将这选中的 3 条新闻处理为地道的中文标题，撰写一句硬核总结（summary），以及一段300字内给普通人看的技术原理解析（article）。

    请严格返回如下 JSON 格式数组（不要包含任何 markdown 代码块标记如 ```json，只输出纯纯的 JSON 符号）：
    [
        {{
            "title": "[硬核前沿] 这里写中文标题",
            "summary": "这里写一句话核心技术总结",
            "article": "这里写通俗易懂的技术原理解析或应用场景科普",
            "url": "选中的原文链接"
        }}
    ]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        # 清理可能携带的代码块符号
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        final_news_data = json.loads(clean_text)
        
        # 4. 保存最新数据
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(final_news_data, f, ensure_ascii=False, indent=4)
        print("✅ AI 主编筛选并生成完毕！文件已更新。")
        
    except Exception as e:
        print(f"❌ AI 处理时开了个小差: {e}")
else:
    print("⚠️ 候选列表为空，退出程序。")
