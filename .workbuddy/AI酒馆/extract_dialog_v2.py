#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取魔王神官 (2) 对话文件内容，输出每条发言的角色和文本摘要
"""
import json
import os

input_file = r"G:\work_software\claw\.workbuddy\ai酒馆\魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported (2).jsonl"
output_file = r"G:\work_software\claw\.workbuddy\ai酒馆\dialog_extract_v2.txt"

messages = []

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            # SillyTavern jsonl格式：每行是一条消息
            # 通常有 name, mes, is_user 等字段
            if isinstance(obj, dict):
                name = obj.get('name', '')
                mes = obj.get('mes', '')
                is_user = obj.get('is_user', False)
                is_system = obj.get('is_system', False)
                
                if mes and not is_system:
                    messages.append({
                        'name': name,
                        'is_user': is_user,
                        'mes': mes
                    })
        except json.JSONDecodeError:
            pass

print(f"总消息数: {len(messages)}")

user_msgs = [m for m in messages if m['is_user']]
ai_msgs = [m for m in messages if not m['is_user']]

print(f"用户发言数: {len(user_msgs)}")
print(f"AI发言数: {len(ai_msgs)}")
print(f"五轮计算: {len(user_msgs)} ÷ 5 = {len(user_msgs)/5:.1f}")
print(f"事件数（取整）: {len(user_msgs)//5} 个事件")
print()

# 输出所有发言内容到文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"总消息数: {len(messages)}\n")
    f.write(f"用户发言数: {len(user_msgs)}\n")
    f.write(f"AI发言数: {len(ai_msgs)}\n")
    f.write(f"五轮计算: {len(user_msgs)} ÷ 5 = {len(user_msgs)/5:.1f}\n")
    f.write(f"事件数（取整）: {len(user_msgs)//5} 个事件\n\n")
    f.write("=" * 80 + "\n\n")
    
    msg_idx = 0
    user_count = 0
    for msg in messages:
        msg_idx += 1
        role = "【用户】" if msg['is_user'] else f"【{msg['name']}】"
        if msg['is_user']:
            user_count += 1
        
        # 截取前300字符展示
        text = msg['mes'][:300].replace('\n', ' ')
        f.write(f"[{msg_idx:03d}] {role} (用户第{user_count}发言)\n" if msg['is_user'] else f"[{msg_idx:03d}] {role}\n")
        f.write(f"  {text}\n\n")

print(f"已保存到: {output_file}")
