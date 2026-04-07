import os
import json
import requests
from google import genai

# 从 GitHub 的安全密码箱里提取你的密钥
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("🤖 启动每日资讯抓取...")
url_top_stories = "https://hacker-news.firebaseio.com/v0/topstories.json"
top_3_ids = requests.get(url_top_stories).json()[:3]

final_news_data = []

for news_id in top_3_ids:
    item_url = f"https://hacker-news.firebaseio.com/v0/item/{news_id}.json"
    item_data = requests.get(item_url).json()
    
    original_title = item_data.get("title", "")
    original_url = item_data.get("url", "无链接（纯文本讨论）")
    
    prompt = f"""
    你现在是一名极简主义科技编辑。
    请处理以下新闻：
    标题：{original_title}
    链接：{original_url}
    
    请执行：
    1. 翻译成中文标题。
    2. 用一句话（不超过30字）提炼硬核技术点(summary)。
    3. 写一段300字内给普通人看的通俗科普(article)。
    4. 严格按以下JSON输出：
    {{
        "title": "中文标题",
        "summary": "一句话总结",
        "article": "通俗科普内容",
        "url": "{original_url}"
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
        print(f"✅ 成功处理: {original_title}")
    except Exception as e:
        print(f"❌ 处理失败: {e}")

# 最关键的一步：把结果保存为 data.json，供你的网页读取
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(final_news_data, f, ensure_ascii=False, indent=4)