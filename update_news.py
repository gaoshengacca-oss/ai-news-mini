import os
import json
import time
import requests
import re

# 1. 获取密钥
zhipu_key = os.environ.get("ZHIPU_API_KEY")

print("🤖 启动全能自愈雷达：完全体版本...")

# 2. 智谱 AI 调用函数
def call_zhipu_ai(prompt_text):
    if not zhipu_key:
        print("🚨 错误：系统未读取到 ZHIPU_API_KEY，请检查 GitHub Secrets 和 main.yml 配置。")
        return None
        
    api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {zhipu_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.2 # 降低温度，让 AI 严格遵守格式
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        
        if 'choices' not in res_json:
            print(f"❌ 智谱接口返回错误详情: {res_json}")
            return None
            
        return res_json['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ 调用智谱 AI 时发生系统异常: {e}")
        return None

# 3. 抓取 Hacker News 逻辑
print("📡 正在抓取过去 24 小时的新鲜情报...")
yesterday_ts = int(time.time()) - (24 * 3600)
url = "https://hn.algolia.com/api/v1/search_by_date"
params = {"tags": "story", "numericFilters": f"created_at_i>{yesterday_ts}", "hitsPerPage": 20}

candidates_text = ""
try:
    res = requests.get(url, params=params, timeout=10)
    hits = res.json().get("hits", [])
    for i, hit in enumerate(hits):
        title = hit.get('title', '无标题')
        link = hit.get('url') or f"
