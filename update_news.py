import os
import json
import time
import requests
from google import genai

# 1. 提取大模型密钥
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动全网雷达：多源抓取、严格24小时、智能去重...")

# 2. 【核心魔法：智能防重】读取昨天的历史记录
seen_urls = set()
if os.path.exists('data.json'):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            # 把昨天的链接全部加入“黑名单”，今天坚决不抓
            for item in old_data:
                seen_urls.add(item.get('url', ''))
    except Exception as e:
        print("首次运行或无历史数据，跳过防重检测。")

# 3. 准备抓取：设定 24 小时时间戳，并伪装成真实浏览器
yesterday_ts = int(time.time()) - (24 * 3600)
candidates = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Bot/1.0'}

# ================= 来源 A: Hacker News (硬核极客) =================
try:
    hn_url = f"https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i>{yesterday_ts}"
    hn_hits = requests.get(hn_url, headers=headers).json().get("hits", [])
    for hit in hn_hits:
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        if url and url not in seen_urls:
            candidates.append({"title": hit.get("title"), "url": url, "source": "Hacker News"})
            break # 只要没见过的第 1 条
except Exception as e: print(f"HN抓取失败: {e}")

# ================= 来源 B: Reddit Technology (全球大众科技) =================
try:
    # t=day 严格限制为过去 24 小时最热
    reddit_url = "https://www.reddit.com/r/technology/top.json?t=day&limit=5"
    reddit_hits = requests.get(reddit_url, headers=headers).json()["data"]["children"]
    for hit in reddit_hits:
        url = hit["data"].get("url")
        if url and url not in seen_urls:
            candidates.append({"title": hit["data"].get("title"), "url": url, "source": "Reddit Tech"})
            break
except Exception as e: print(f"Reddit抓取失败: {e}")

# ================= 来源 C: Dev.to (前沿数字工具与开发) =================
try:
    # top=1 代表提取每日最热
    dev_url = "https://dev.to/api/articles?top=1"
    dev_hits = requests.get(dev_url, headers=headers).json()
    for hit in dev_hits:
        url = hit.get("url")
        if url and url not in seen_urls:
            candidates.append({"title": hit.get("title"), "url": url, "source": "Dev.to"})
            break
except Exception as e: print(f"Dev.to抓取失败: {e}")

# 4. 呼叫大模型进行翻译和通俗化
final_news_data = []

for item in candidates:
    print(f"🔄 正在呼叫 AI 处理 [{item['source']}] 的新闻: {item['title']}")
    
    prompt = f"""
    你现在是一名极简主义科技编辑。
    请处理以下来自 {item['source']} 的过去24小时内最热科技新闻：
    标题：{item['title']}
    链接：{item['url']}
    
    请执行：
    1. 翻译成地道中文标题（拒绝标题党）。
    2. 用一句话（不超过30字）提炼核心看点(summary)。
    3. 写一段300字内给普通人看的通俗科普或行业影响分析(article)。
    4. 严格按以下JSON输出，不要包含其他废话：
    {{
        "title": "[{item['source']}] 中文标题",
        "summary": "一句话总结",
        "article": "通俗科普内容",
        "url": "{item['url']}"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        ai_result = json.loads(clean_text)
        final_news_data.append(ai_result)
        print("✅ AI 提炼完成！\n")
    except Exception as e:
        print(f"❌ AI 处理时开了个小差: {e}\n")
        
    time.sleep(2)

# 5. 保存最新数据，覆盖旧文件
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(final_news_data, f, ensure_ascii=False, indent=4)
