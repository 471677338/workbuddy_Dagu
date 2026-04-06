import json

def analyze_timed_worldinfo():
    """深入分析timedWorldInfo字典"""
    print("=== timedWorldInfo深度分析 ===")
    
    try:
        # 读取第一行数据
        with open('魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl', 'r', encoding='utf-8') as f:
            data = json.loads(f.readline())
        
        timed_info = data['chat_metadata']['timedWorldInfo']
        
        print(f"timedWorldInfo类型: {type(timed_info)}")
        print(f"字典键数量: {len(timed_info)}")
        print(f"所有键: {list(timed_info.keys())}")
        print()
        
        # 检查是否有entries键
        if 'entries' in timed_info:
            entries = timed_info['entries']
            print(f"找到 'entries' 键")
            print(f"entries类型: {type(entries)}")
            
            if isinstance(entries, list):
                print(f"entries数量: {len(entries)}")
                print()
                
                # 显示条目结构
                print("=== entries条目结构分析 ===")
                if entries:
                    # 显示前3个条目的详细结构
                    for i, entry in enumerate(entries[:3]):
                        print(f"\n[{i}] 条目类型: {type(entry)}")
                        if isinstance(entry, dict):
                            keys = list(entry.keys())
                            print(f"   键数量: {len(keys)}")
                            print(f"   键列表: {keys}")
                            
                            # 显示重要字段
                            for key in ['content', 'message', 'text', 'note', 'id', 'index', 'step', 'position']:
                                if key in entry:
                                    value = entry[key]
                                    print(f"   {key}: {type(value)}")
                                    if isinstance(value, str):
                                        preview = value[:100] + "..." if len(value) > 100 else value
                                        print(f"      内容: {preview}")
                                    elif isinstance(value, (int, float)):
                                        print(f"      值: {value}")
                        print()
                    
                    # 统计条目类型
                    entry_types = {}
                    for entry in entries:
                        if isinstance(entry, dict):
                            # 检查是否有content/message/text等键
                            has_content = any(k in entry for k in ['content', 'message', 'text', 'note'])
                            if has_content:
                                key_present = []
                                for k in ['content', 'message', 'text', 'note']:
                                    if k in entry and entry[k]:
                                        key_present.append(k)
                                type_str = ",".join(key_present)
                                entry_types[type_str] = entry_types.get(type_str, 0) + 1
                            else:
                                entry_types['no_content'] = entry_types.get('no_content', 0) + 1
                        else:
                            entry_types[str(type(entry))] = entry_types.get(str(type(entry)), 0) + 1
                    
                    print("\n=== 条目类型统计 ===")
                    for type_name, count in entry_types.items():
                        print(f"{type_name}: {count}个")
                        
                else:
                    print("entries列表为空")
            else:
                print(f"entries不是列表，实际类型为: {type(entries)}")
                
        else:
            print("没有找到 'entries' 键")
            # 检查是否有其他可能包含事件的键
            possible_event_keys = ['eventList', 'timedEvents', 'notes', 'worldEntries', 'events']
            found = False
            for key in possible_event_keys:
                if key in timed_info:
                    found = True
                    print(f"\n找到 '{key}' 键")
                    value = timed_info[key]
                    print(f"类型: {type(value)}")
                    if isinstance(value, (list, dict)):
                        if isinstance(value, list):
                            print(f"长度: {len(value)}")
                            if value:
                                print(f"第一个元素类型: {type(value[0])}")
                        elif isinstance(value, dict):
                            print(f"键数量: {len(value)}")
                    break
            
            if not found:
                # 显示timed_info的所有内容（简略）
                print("\n=== timedWorldInfo内容预览 ===")
                for key, value in list(timed_info.items())[:5]:  # 只显示前5个
                    print(f"{key}: {type(value)}")
                    if isinstance(value, (str, int, float, bool)):
                        print(f"   值: {value}")
                    elif isinstance(value, list):
                        print(f"   列表长度: {len(value)}")
                    elif isinstance(value, dict):
                        print(f"   字典键数量: {len(value)}")
        
        # 再检查variables，可能包含对话数量等信息
        print("\n" + "="*60)
        print("=== variables分析 ===")
        variables = data['chat_metadata']['variables']
        if isinstance(variables, dict):
            print(f"variables键数量: {len(variables)}")
            # 显示一些可能的对话相关键
            dialogue_keys = [k for k in variables.keys() if 'dialogue' in k.lower() or 'conversation' in k.lower() or 'message' in k.lower() or 'count' in k.lower()]
            if dialogue_keys:
                print(f"可能的对话相关键:")
                for key in dialogue_keys[:10]:  # 最多显示10个
                    print(f"  {key}: {variables[key]}")
            else:
                # 显示所有键的前10个
                print(f"前10个键:")
                for i, key in enumerate(list(variables.keys())[:10]):
                    print(f"  {key}: {variables[key]}")
    
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_timed_worldinfo()