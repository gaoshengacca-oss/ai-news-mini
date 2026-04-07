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
    # 👑 这里是核心：给 AI 的“死命令”
    strict_prompt = f"""
    你是一名硬核科技编辑。请从以下新闻中选出3条最硬核的技术新闻。
    
    【任务要求】：
    1. 必须将标题翻译成地道的【中文】。
    2. 撰写中文总结(summary)和科普解析(article)。
    3. 严格输出 JSON 数组格式，禁止任何开头结尾的废话。
    
    【JSON 格式模板】：
    [
      {{
        "title": "中文标题",
        "summary": "一句话核心技术看点",
        "article": "300字内深度解析",
        "url": "对应的原始链接"
      }}
    ]

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
