import os
import json
import time
import requests
import re

# 1. 获取智谱 API Key (确保你在 GitHub Secrets 里配置的名字是这个)
zhipu_key = os.environ.get("ZHIPU_API_KEY")

print("🤖 启动全能自愈雷达：优先调用智谱 GLM-4-Flash...")

# 2. 抓取逻辑：从 Hacker News 获取过去 24 小时最火的 20 条新闻
yesterday_ts = int(time.time()) - (24 * 3600)
url = "https://hn.algolia.com/api/v1/search_by_date"
params = {
    "tags": "story", 
    "numericFilters": f"created_at_i>{yesterday_ts}", 
    "hitsPerPage": 20
}

candidates_text = ""
try:
    res = requests.get(url, params=params, timeout=10)
    hits = res.json().get("hits", [])
    for i, hit in enumerate(hits):
        # 提取标题和链接
        title = hit.get('title', '无标题')
        link = hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        candidates_text += f"{i+1}. {title} (URL: {link})\n"
    print(f"📡 抓取完成，共 {len(hits)} 条候选新闻。")
except Exception as e:
    print(f"❌ 原始数据抓取失败: {e}")

# 3. 智谱 AI 调用函数（核心逻辑：把新闻发给 GLM-4-Flash）
def call_zhipu_ai(prompt_text):
    api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {zhipu_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "glm-4-flash", # 智谱家性价比最高的型号
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.3
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ 智谱 AI 响应异常: {e}")
        return None

# 4. 如果抓到了新闻，就开始让 AI 工作
if candidates_text:
    prompt = f"""
    你现在是一名硬核科技主编。请从下列标题中选出 3 个真正代表技术突破、新产品发布或硬核研究的新闻。
    
    【强制要求】：
    1. 剔除所有 CEO 访谈、八卦、融资、政策法规、文章回顾。
    2. 将选中的 3 条处理为中文，并严格按以下 JSON 数组格式输出：
    [
        {{"title": "地道中文标题", "summary": "一句话技术看点", "article": "300字内通俗解析", "url": "原文链接"}}
    ]
    
    【候选名单】：
    {candidates_text}
    """
    
    print("🧠 正在通过智谱 AI 进行硬核筛选与翻译...")
    ai_content = call_zhipu_ai(prompt)
    
    if ai_content:
        # 使用正则表达式精准抠出 JSON 部分
        match = re.search(r'\[.*\]', ai_content, re.DOTALL)
        if match:
            try:
                final_data = json.loads(match.group(0))
                # 写入 data.json，这就是网页读取的文件
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=4)
                print("✅ 任务圆满完成！网页数据已更新。")
            except Exception as e:
                print(f"❌ JSON 转换失败: {e}")
        else:
            print("❌ AI 返回内容中没找到有效的 JSON 数组。")
