import os
import json
import time
import requests
import re

# 1. 获取密钥
zhipu_key = os.environ.get("ZHIPU_API_KEY")

print("🤖 启动全能自愈雷达：调试版...")

# 2. 抓取逻辑 (保持不变)
yesterday_ts = int(time.time()) - (24 * 3600)
url = "https://hn.algolia.com/api/v1/search_by_date"
params = {"tags": "story", "numericFilters": f"created_at_i>{yesterday_ts}", "hitsPerPage": 20}

candidates_text = ""
try:
    res = requests.get(url, params=params, timeout=10)
    hits = res.json().get("hits", [])
    for i, hit in enumerate(hits):
        title = hit.get('title', '无标题')
        link = hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        candidates_text += f"{i+1}. {title} (URL: {link})\n"
    print(f"📡 抓取完成，共 {len(hits)} 条候选。")
except Exception as e:
    print(f"❌ 抓取失败: {e}")

# 3. 智谱 AI 调用函数（增加了排错逻辑）
def call_zhipu_ai(prompt_text):
    api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {zhipu_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.3
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        # 👑 核心调试代码：如果报错了，把全家福打印出来
        if response.status_code != 200:
            print(f"❌ 智谱接口返回错误状态码: {response.status_code}")
            print(f"❌ 错误详情: {res_json}")
            return None
            
        return res_json['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ 调用智谱时发生系统级异常: {e}")
        return None

# 4. 执行任务
if candidates_text:
    prompt = "你是硬核科技主编，请从下列标题选3个最硬核的技术突破，严格输出JSON数组格式。"
    print("🧠 正在通过智谱 AI 进行硬核筛选...")
    ai_content = call_zhipu_ai(prompt + "\n" + candidates_text)
    
    if ai_content:
        match = re.search(r'\[.*\]', ai_content, re.DOTALL)
        if match:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(json.loads(match.group(0)), f, ensure_ascii=False, indent=4)
            print("✅ 任务圆满完成！")
        else:
            print(f"❌ 未在 AI 回复中找到 JSON。AI 原话是：{ai_content[:100]}...")
