#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成叙事性的对话总结 - 每5个对话写一段连贯故事
输出SillyTavern兼容的table_data格式
"""

import json
import os

def read_conversations():
    """读取对话文件"""
    input_file = "魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl"
    
    conversations = []
    line_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    conversations.append(data)
                    line_count += 1
                except json.JSONDecodeError as e:
                    print(f"第{line_count+1}行JSON解析错误: {e}")
                    
        print(f"成功读取 {len(conversations)} 个对话")
        return conversations
    except Exception as e:
        print(f"文件读取错误: {e}")
        return []

def extract_message_content(conversation):
    """从对话中提取消息内容"""
    message = conversation.get('mes', '')
    name = conversation.get('name', '未知')
    user_name = conversation.get('user_name', '')
    is_user = conversation.get('is_user', False)
    
    if isinstance(message, str):
        # 清理消息内容
        clean_msg = message.strip()
        
        # 构建角色标识
        if is_user:
            if user_name:
                role = f"[{user_name}]"
            else:
                role = "[用户]"
        else:
            if name:
                role = f"[{name}]"
            else:
                role = "[AI角色]"
                
        return role + " " + clean_msg
    return ""

def generate_narrative_summary(group_num, conversations_chunk):
    """生成叙事性的总结"""
    
    # 提取这个组的所有消息
    messages = []
    for conv in conversations_chunk:
        msg = extract_message_content(conv)
        if msg:
            messages.append(msg)
    
    # 分析关键信息
    user_msgs = [conv for conv in conversations_chunk if conv.get('is_user')]
    ai_msgs = [conv for conv in conversations_chunk if not conv.get('is_user') and not conv.get('is_system')]
    
    # 提取关键角色和事件
    key_events = []
    key_characters = set()
    
    # 从用户消息中提取关键信息
    for conv in user_msgs[:3]:  # 只看前几条
        msg = conv.get('mes', '')
        if isinstance(msg, str) and len(msg) > 20:
            # 简单提取前30个字符作为事件线索
            event = msg[:50].strip()
            if event:
                key_events.append(event)
    
    # 从AI消息中提取角色
    for conv in ai_msgs[:3]:
        name = conv.get('name', '')
        if name:
            key_characters.add(name)
    
    # 构建叙事性总结
    if len(messages) >= 3:
        # 用第一、中间、最后的消息构建连贯故事
        first_msg = messages[0][:100] + "..." if len(messages[0]) > 100 else messages[0]
        middle_idx = len(messages) // 2
        middle_msg = messages[middle_idx][:80] + "..." if len(messages[middle_idx]) > 80 else messages[middle_idx]
        
        # 简单写个故事板
        if user_msgs and ai_msgs:
            summary = f"在这个阶段，共有{len(user_msgs)}次用户发言和{len(ai_msgs)}次AI角色互动。"
            summary += f" 对话始于：{first_msg}。"
            summary += f" 中段发展为：{middle_msg}"
            
            if key_characters:
                chars = "、".join(key_characters)
                summary += f" 涉及角色包括{chars}。"
                
            if key_events:
                summary += f" 关键线索：{key_events[0]}"
        else:
            summary = f"第{group_num}组对话（共{len(conversations_chunk)}条记录）。"
    else:
        summary = f"第{group_num}组对话片段。"
    
    return summary

def create_table_data(conversations):
    """创建SillyTavern格式的事件表"""
    
    # 分组：每5个对话一组
    group_size = 5
    num_groups = (len(conversations) + group_size - 1) // group_size
    
    # 生成事件表内容
    table_content = []
    
    # 表头
    header = ["事件组", "叙事性对话总结", "对话次数统计", "涉及主要角色", "情感走向分析"]
    table_content.append(header)
    
    for i in range(num_groups):
        start_idx = i * group_size
        end_idx = min((i + 1) * group_size, len(conversations))
        
        group_conv = conversations[start_idx:end_idx]
        
        # 数据行
        group_num = i + 1
        
        # 生成叙事性总结
        narrative_summary = generate_narrative_summary(group_num, group_conv)
        
        # 统计信息
        dialog_count = f"总对话: {len(group_conv)} | 用户: {len([c for c in group_conv if c.get('is_user')])} | AI角色: {len([c for c in group_conv if not c.get('is_user')])}"
        
        # 提取角色
        characters = set()
        for conv in group_conv:
            if not conv.get('is_user'):
                name = conv.get('name', '')
                if name:
                    characters.add(name)
            elif conv.get('is_user') and conv.get('user_name'):
                characters.add(conv.get('user_name'))
        
        char_list = "、".join(characters) if characters else "未知"
        
        # 简单情感分析（示例）
        if "高兴" in narrative_summary or "开心" in narrative_summary:
            emotion = "积极正面"
        elif "悲伤" in narrative_summary or "难过" in narrative_summary:
            emotion = "负面情绪"
        else:
            emotion = "中性/日常"
        
        row = [
            f"第{group_num}组",
            narrative_summary,
            dialog_count,
            char_list,
            emotion
        ]
        table_content.append(row)
    
    # 构建最终的table_data
    table_data = {
        "sheet_dialog_narrative_summary": {
            "name": "剧情对话叙事总结（每5次对话）",
            "firstRowIsHeader": True,
            "content": table_content
        }
    }
    
    return table_data

def save_json_files(table_data):
    """保存JSON文件"""
    
    # 格式化版本
    formatted_file = "dialog_narrative_summary_formatted.json"
    with open(formatted_file, 'w', encoding='utf-8') as f:
        json.dump(table_data, f, ensure_ascii=False, indent=2)
    
    print(f"格式化版本已保存: {formatted_file}")
    
    # 压缩版本（SillyTavern可用）
    compressed_file = "dialog_narrative_summary_compressed.json"
    with open(compressed_file, 'w', encoding='utf-8') as f:
        json.dump(table_data, f, ensure_ascii=False, separators=(',', ':'))
    
    print(f"压缩版本已保存: {compressed_file}")
    return compressed_file

def main():
    print("开始生成叙事性对话总结...")
    
    # 读取对话
    conversations = read_conversations()
    if not conversations:
        print("没有读取到对话，程序退出")
        return
    
    print(f"共读取 {len(conversations)} 个对话，将分为 {((len(conversations)+4)//5)} 组进行叙事总结")
    
    # 创建事件表
    table_data = create_table_data(conversations)
    
    # 保存文件
    compressed_file = save_json_files(table_data)
    
    print("\n" + "="*60)
    print("生成完成！")
    print(f"请导入文件: {compressed_file}")
    print("="*60)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()