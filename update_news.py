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
        link = hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        candidates_text += f"[{i+1}] {title} (URL: {link})\n"
    print(f"📡 抓取完成，共 {len(hits)} 条候选新闻。")
except Exception as e:
    print(f"❌ 抓取失败: {e}")

# 4. 执行筛选与深度解析任务
if candidates_text:
    strict_prompt = f"""
    你是一名资深硬核科技专栏作家。请从下列新闻中选出3条最重磅的技术突破，并撰写深度解析。
    
    【强制要求】：
    1. 标题(title)：必须是吸引人的硬核中文标题。
    2. 总结(summary)：用一句话点出最震撼的技术细节。
    3. 解析(article)：字数必须不少于 250 字。禁止使用“本文探讨了”等废话。必须按以下三段式结构撰写：
       - 第一段：解析该技术的底层逻辑(它是怎么工作的)。
       - 第二段：分析它对当前行业现状的颠覆性影响。
       - 第三段：预测它在未来会如何改变普通人的生活。
    4. 链接(url)：必须严格对应你选中的原始链接。
    5. 输出格式：严格且仅输出 JSON 数组，禁止任何解释性文字。
    
    【JSON 格式模板】：
    [
      {{
        "title": "中文标题",
        "summary": "一句话核心技术看点",
        "article": "此处应包含至少 250 字的深度三段式解析...",
        "url": "对应的原始链接"
      }}
    ]

    【候选名单】：
    {candidates_text}
    """
    
    print("🧠 正在通过智谱 AI 进行深度翻译与扩写...")
    ai_reply = call_zhipu_ai(strict_prompt)
    
    if ai_reply:
        # 使用正则表达式精准提取 JSON 数组部分，防止 AI 在前后加废话
        match = re.search(r'\[.*\]', ai_reply, re.DOTALL)
        if match:
            try:
                json_str = match.group(0)
                final_data = json.loads(json_str)
                # 将数据写入文件
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=4)
                print("✅ 任务圆满完成！网页数据已成功更新，包含深度解析。")
            except Exception as e:
                print(f"❌ JSON 转换失败: {e}\nAI 原文片段: {json_str[:100]}")
        else:
            print(f"❌ 未在 AI 回复中找到有效 JSON。AI 原文: {ai_reply[:100]}")
else:
    print("⚠️ 候选名单为空，没有数据可供 AI 处理。")
