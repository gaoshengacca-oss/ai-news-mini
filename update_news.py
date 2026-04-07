import os
import json
import time
import requests
import re

# 1. 获取密钥
zhipu_key = os.environ.get("ZHIPU_API_KEY")

def call_zhipu_ai(prompt_text):
    api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {zhipu_key}", "Content-Type": "application/json"}
    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.2 # 👑 降低随机性，让 AI 严格守规矩
    }
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=60)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ AI 呼叫失败: {e}")
        return None

# 2. 抓取逻辑 (保持不变)
print("📡 正在抓取新鲜情报...")
yesterday_ts = int(time.time()) - (24 * 3600)
url = "https://hn.algolia.com/api/v1/search_by_date"
params = {"tags": "story", "numericFilters": f"created_at_i>{yesterday_ts}", "hitsPerPage": 20}

candidates = ""
try:
    hits = requests.get(url, params=params).json().get("hits", [])
    for i, h in enumerate(hits):
        candidates += f"ID:{i} | Title: {h['title']} | URL: {h.get('url','#')}\n"
except: print("抓取异常")

# 3. AI 筛选 (强化 Prompt)
if candidates:
    # 👑 强化版 Prompt：强制 AI 进行多维度扩写
    strict_prompt = f"""
    你是一名硬核科技专栏作家。请从下列新闻中选出3条最重磅的技术突破，并撰写深度解析。
    
    【写作要求】：
    1. 标题(title)：必须是吸引人的硬核中文标题。
    2. 总结(summary)：用一句话点出最震撼的技术细节。
    3. 解析(article)：字数必须不少于 250 字。禁止使用“本文介绍了”等废话，请按以下结构撰写：
       - 第一段：解析该技术的底层逻辑(How it works)。
       - 第二段：分析它对当前行业现状的颠覆性影响。
       - 第三段：预测它在未来 1-3 年内会如何改变普通人的生活。
    4. 链接(url)：必须对应原始链接。
    
    【JSON 格式模板】：
    [
      {{
        "title": "...",
        "summary": "...",
        "article": "此处应包含至少 250 字的深度三段式解析...",
        "url": "..."
      }}
    ]

    【候选名单】：
    {candidates}
    """

    【候选名单】：
    {candidates}
    """
    
    print("🧠 正在进行深度翻译与筛选...")
    ai_reply = call_zhipu_ai(strict_prompt)
    
    if ai_reply:
        # 使用正则提取，防止 AI 加废话
        match = re.search(r'\[.*\]', ai_reply, re.DOTALL)
        if match:
            try:
                json_str = match.group(0)
                final_data = json.loads(json_str)
                # 写入文件
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=4)
                print("✅ 网页数据已成功更新！")
            except:
                print("❌ AI 返回的 JSON 格式解析失败")
        else:
            print("❌ AI 未按要求返回 JSON 数组")
