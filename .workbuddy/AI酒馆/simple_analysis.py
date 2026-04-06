import json

print("=== 分析对话数据的'问答轮次'结构 ===")
print()

# 读取文件的前几行来分析结构
line_number = 0
user_responses = []
ai_responses = []
conversation_blocks = []

with open('魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl', 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f):
        line_number += 1
        
        # 只分析前5行对话数据（第2-6行）
        if line_number <= 6:
            try:
                data = json.loads(line.strip())
                
                if line_number == 1:
                    print(f"第1行（配置）: {data.get('character_name', '未知')}")
                    print(f"  创建时间: {data.get('create_date', '不详')}")
                    print()
                    continue
                
                # 对话数据
                print(f"第{line_number}行对话:")
                print(f"  角色名: {data.get('name', '不详')}")
                print(f"  是用户: {data.get('is_user', False)}")
                mes_content = data.get('mes', '')
                print(f"  内容前40字: {mes_content[:40]}...")
                print()
                
                # 记录用户和AI消息
                if data.get('is_user', False):
                    user_responses.append((line_number, data.get('name', '用户'), mes_content[:50]))
                else:
                    ai_responses.append((line_number, data.get('name', 'AI'), mes_content[:50]))
                    
            except json.JSONDecodeError as e:
                print(f"第{line_number}行解析失败: {e}")
                continue
            
        if line_number >= 6:
            break

print("=== 问答轮次识别 ===")
print(f"用户发言: {len(user_responses)} 条")
print(f"AI发言: {len(ai_responses)} 条")
print()

# 尝试配对问答轮
print("前几个问答轮次:")
for i in range(min(len(user_responses), len(ai_responses), 3)):
    user_line, user_name, user_content = user_responses[i]
    ai_line, ai_name, ai_content = ai_responses[i]
    
    # 检查是否构成一个问答轮（用户先发言，AI后回应）
    if user_line < ai_line:
        print(f"轮次{i+1}:")
        print(f"  用户（第{user_line}行）: {user_name}")
        print(f"    说: {user_content}...")
        print(f"  AI（第{ai_line}行）: {ai_name}")
        print(f"    回应: {ai_content}...")
        print()
    else:
        print(f"可能不是问答轮: AI发言（{ai_line}）在用户发言（{user_line}）之前")
        print()