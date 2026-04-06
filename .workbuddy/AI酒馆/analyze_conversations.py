import json
import re

def analyze_conversation_data():
    """分析SillyTavern导出的对话数据"""
    print("=== SillyTavern对话数据分析 ===")
    
    try:
        # 读取第一行数据
        with open('魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl', 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        
        data = json.loads(first_line)
        
        print(f"用户: {data['user_name']}")
        print(f"角色: {data['character_name']}")
        print(f"创建时间: {data['create_date']}")
        print()
        
        chat_meta = data['chat_metadata']
        
        # 1. 检查timedWorldInfo
        if 'timedWorldInfo' in chat_meta:
            timed_info = chat_meta['timedWorldInfo']
            
            # 尝试解析timedWorldInfo
            if isinstance(timed_info, str):
                try:
                    timed_data = json.loads(timed_info)
                    print(f"timedWorldInfo解析为 {type(timed_data)}")
                    
                    if isinstance(timed_data, dict):
                        # 这是一个字典，检查常用键
                        for key in ['entries', 'eventList', 'timedEvents', 'notes', 'worldEntries']:
                            if key in timed_data:
                                entries = timed_data[key]
                                print(f"\n找到条目键: '{key}'")
                                print(f"  类型: {type(entries)}")
                                
                                if isinstance(entries, list):
                                    print(f"  条目数量: {len(entries)}")
                                    
                                    # 显示前3个条目
                                    print(f"\n前3个条目结构:")
                                    for i, entry in enumerate(entries[:3]):
                                        print(f"  [{i}] 类型: {type(entry)}")
                                        if isinstance(entry, dict):
                                            print(f"     键: {list(entry.keys())}")
                                            # 显示重要的内容字段
                                            for content_key in ['content', 'message', 'text', 'description', 'note']:
                                                if content_key in entry and entry[content_key]:
                                                    content = entry[content_key]
                                                    preview = content[:100] + "..." if len(content) > 100 else content
                                                    print(f"     {content_key}: {preview}")
                                                    break
                                        print()
                                    break
                            
                        # 如果没有找到entries键，显示所有键
                        if 'entries' not in timed_data and 'eventList' not in timed_data:
                            print(f"\ntimedWorldInfo字典的所有键: {list(timed_data.keys())}")
                    
                    elif isinstance(timed_data, list):
                        print(f"\ntimedWorldInfo是列表，长度: {len(timed_data)}")
                        if timed_data:
                            print(f"第一个条目类型: {type(timed_data[0])}")
                            if isinstance(timed_data[0], dict):
                                print(f"第一个条目键: {list(timed_data[0].keys())}")
                
                except json.JSONDecodeError as e:
                    print(f"解析timedWorldInfo失败: {e}")
                    # 显示timedWorldInfo的前500个字符
                    preview = timed_info[:500] + "..." if len(timed_info) > 500 else timed_info
                    print(f"timedWorldInfo内容预览: {preview}")
            else:
                print(f"timedWorldInfo类型: {type(timed_info)}")
        else:
            print("没有timedWorldInfo键")
        
        print("\n" + "="*60)
        
        # 2. 计算文件总行数（对话总轮数）
        print("\n=== 对话统计 ===")
        with open('魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl', 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        print(f"文件总行数: {total_lines} (应该是总对话次数)")
        
        # 3. 检查是否有对话内容的键
        print("\n=== 其他可能包含对话的键 ===")
        for key in chat_meta.keys():
            val = chat_meta[key]
            if isinstance(val, (list, dict)) and key not in ['timedWorldInfo', 'sheets', 'selected_sheets']:
                print(f"{key}: {type(val)}")
                if isinstance(val, list):
                    print(f"  长度: {len(val)}")
                elif isinstance(val, dict):
                    print(f"  键数量: {len(val)}")
        
        # 4. 建议的处理方式
        print("\n" + "="*60)
        print("=== 建议的处理方式 ===")
        print("根据st-memory-enhancement插件的思路，应该:")
        print("1. 提取timedWorldInfo中的事件/对话条目")
        print("2. 每5个条目为一组，生成一个事件总结")
        print("3. 事件总结要简洁，50-100字")
        print("4. 保持原始事件的时间顺序")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")

if __name__ == "__main__":
    analyze_conversation_data()