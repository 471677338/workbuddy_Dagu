import json

# 读取对话数据并正确理解"轮"的含义
print("=== 重新分析对话数据，理解'问答五轮' ===")
print()

# 统计所有对话数据
all_conversations = []
with open('魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl', 'r', encoding='utf-8') as f:
    # 跳过第一行（配置）
    first_line = next(f)
    config_data = json.loads(first_line)
    
    # 收集所有对话行
    for i, line in enumerate(f, start=2):
        try:
            conv = json.loads(line)
            all_conversations.append(conv)
            if i > 30:  # 只看前30行分析模式
                break
        except json.JSONDecodeError:
            print(f"第{i}行解析失败")

print(f"配置行: {config_data.get('character_name', '未知角色')} (第1行)")
print(f"对话行数量: {len(all_conversations)}")
print()

# 分析第一个对话块
if all_conversations:
    first_conv = all_conversations[0]
    print("第一个对话块键:", list(first_conv.keys()))
    print()
    
    # 查看chat数组
    if 'chat' in first_conv:
        chat_data = first_conv['chat']
        print(f"chat数组长度: {len(chat_data)}")
        print()
        
        # 分析前几个消息的"轮"结构
        print("=== 对话轮次分析 ===")
        user_messages = []
        ai_messages = []
        
        for i, msg in enumerate(chat_data[:20]):  # 只分析前20条消息
            is_user = msg.get('is_user', False)
            name = msg.get('name', '未知')
            content = msg.get('mes', '')[30] + "..." if len(msg.get('mes', '')) > 30 else msg.get('mes', '')
            
            if is_user:
                user_messages.append((i, name, content))
            else:
                ai_messages.append((i, name, content))
            
            if i < 5:  # 只显示前5条消息的模式
                print(f"消息{i}: 角色={name}, 用户={is_user}")
                print(f"  内容: {content}")
                print()
        
        print(f"用户消息数量: {len(user_messages)}")
        print(f"AI消息数量: {len(ai_messages)}")
        print()
        
        # 尝试识别"问答轮次"
        # 问答轮通常交替出现：用户 -> AI -> 用户 -> AI
        if user_messages and ai_messages:
            print("前几个问答轮次:")
            round_count = 0
            user_idx = 0
            ai_idx = 0
            
            # 简化：假设用户和AI消息交替出现
            min_len = min(len(user_messages), len(ai_messages))
            for i in range(min_len):
                if user_messages[i][0] < ai_messages[i][0]:  # 用户发言在先，然后AI回复
                    print(f"轮次{i+1}:")
                    print(f"  用户: {user_messages[i][1]} - {user_messages[i][2]}")
                    print(f"  AI: {ai_messages[i][1]} - {ai_messages[i][2]}")
                    print()
                    round_count += 1
                if round_count >= 3:  # 只显示前3轮
                    break