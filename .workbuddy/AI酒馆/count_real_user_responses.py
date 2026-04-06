import json

print("=== 统计实际用户发言数量 ===")

user_responses = []
ai_responses = []

# 读取所有行（跳过第一行配置）
with open('魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl', 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f):
        if line_num == 0:
            continue  # 跳过配置行
        
        try:
            data = json.loads(line.strip())
            
            is_user = data.get('is_user', False)
            name = data.get('name', '未知')
            
            if is_user:
                content = data.get('mes', '')[:50] + "..." if len(data.get('mes', '')) > 50 else data.get('mes', '')
                user_responses.append((line_num, name, content))
            else:
                ai_responses.append((line_num, name))
                
        except json.JSONDecodeError:
            continue

print(f"总对话行数（除配置外）: {line_num}")
print(f"用户发言数量: {len(user_responses)}")
print(f"AI发言数量: {len(ai_responses)}")
print()

# 显示前5个用户发言作为示例
print("前5个用户发言:")
for i in range(min(5, len(user_responses))):
    line_num, name, content = user_responses[i]
    print(f"  {i+1}. 第{line_num}行 ({name}): {content}")
print()

# 根据不同的理解计算事件数量
print("=== 不同理解下的事件数量 ===")

# 理解1: 每5行对话生成一个事件
dialogues_per_event_5 = 5
events_from_5 = (line_num - 1) // dialogues_per_event_5  # 减去配置行
print(f"理解1 - 每{dialogues_per_event_5}行对话生成一个事件 -> {events_from_5}个事件")

# 理解2: 每5个用户发言生成一个事件
user_responses_per_event_5 = 5
events_from_user_5 = len(user_responses) // user_responses_per_event_5
print(f"理解2 - 每{user_responses_per_event_5}个用户发言生成一个事件 -> {len(user_responses)}/{user_responses_per_event_5} = {events_from_user_5}个事件")

# 理解3: 每10行对话（约5个问答轮）生成一个事件
dialogues_per_event_10 = 10
events_from_10 = (line_num - 1) // dialogues_per_event_10
print(f"理解3 - 每{dialogues_per_event_10}行对话（约5轮）生成一个事件 -> {events_from_10}个事件")

print()
print("table_data (2).json 有 23 行（22个事件 + 表头）")
print("用户说'15行'可能意味着目标: 15个事件（14个事件行 + 表头）")