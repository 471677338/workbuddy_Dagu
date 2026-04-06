import json
import os

def analyze_dialog_file():
    """分析对话文件的实际结构和内容"""
    
    dialog_file = '魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl'
    
    if not os.path.exists(dialog_file):
        print(f"[错误] 文件不存在: {dialog_file}")
        return
    
    user_messages = []
    all_messages = []
    
    with open(dialog_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"[信息] 文件总行数: {len(lines)}")
    
    # 分析每行内容
    for i, line in enumerate(lines):
        try:
            line = line.strip()
            if not line:
                continue
                
            data = json.loads(line)
            
            # 记录消息信息
            msg_type = str(data.get('type', 'unknown'))
            name = str(data.get('name', 'unknown'))
            is_user = data.get('is_user', False)
            mes = data.get('mes', '').strip()
            
            all_messages.append({
                'line': i+1,
                'type': msg_type,
                'name': name,
                'is_user': is_user,
                'mes': mes[:100] + '...' if len(mes) > 100 else mes,
                'length': len(mes)
            })
            
            if is_user and mes:
                user_messages.append({
                    'index': len(user_messages) + 1,
                    'line_number': i+1,
                    'name': name,
                    'content': mes,
                    'length': len(mes)
                })
                
        except json.JSONDecodeError as e:
            print(f"[警告] 行 {i+1}: JSON解析失败 - {e}")
        except Exception as e:
            print(f"[警告] 行 {i+1}: 其他错误 - {e}")
    
    # 输出关键统计
    print(f"\\n[统计] 用户发言总数: {len(user_messages)}")
    print(f"[统计] 所有消息总数: {len(all_messages)}")
    
    # 显示前10个用户发言
    print(f"\\n[前10个用户发言]")
    for i, msg in enumerate(user_messages[:10]):
        print(f"  {i+1}. 第{msg['line_number']}行 - {msg['name']}:")
        print(f"      内容: {msg['content'][:80]}... ({msg['length']}字)")
    
    # 统计消息类型分布
    type_counts = {}
    for msg in all_messages:
        msg_type = msg['type']
        type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
    
    print(f"\\n[消息类型分布]")
    for msg_type, count in sorted(type_counts.items()):
        print(f"  {msg_type}: {count}条")
    
    return user_messages, all_messages

if __name__ == "__main__":
    user_messages, all_messages = analyze_dialog_file()