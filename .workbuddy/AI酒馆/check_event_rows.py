import json

print("=== 分析重要事件表格行数 ===")

# 检查之前的生成文件
filename = "table_data_st_memory_perfect_formatted.json"

try:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"文件读取成功")
    
    # 找重要事件表格
    events_table = None
    table_key = None
    
    for key in data:
        if isinstance(data[key], dict):
            table_name = data[key].get('name', '')
            if '重要事件' in table_name or 'sheet_mLF3HD7T' == key:
                table_key = key
                events_table = data[key]['content']
                break
    
    if events_table:
        print(f"找到重要事件表格: {data[table_key].get('name', table_key)}")
        print(f"总行数: {len(events_table)}")
        print(f"事件数量: {len(events_table) - 1} (减去表头)")
        print()
        
        # 显示前几行
        print("前3行事件:")
        for i in range(min(4, len(events_table))):
            if i == 0:
                print(f"表头: {events_table[i]}")
            else:
                row = events_table[i]
                event_desc = row[3] if len(row) > 3 else "无描述"
                # 计算字数
                import re
                chinese_chars = re.findall(r'[\u4e00-\u9fff]', event_desc)
                word_count = len(chinese_chars)
                print(f"第{i}行事件: {row[1]}（{word_count}字）")
                print(f"  描述: {event_desc[:50]}...")
    else:
        print("未找到重要事件表格")
        print("所有表格:")
        for key in data:
            if isinstance(data[key], dict) and 'name' in data[key]:
                print(f"  {key}: {data[key]['name']}")
                
except Exception as e:
    print(f"读取失败: {e}")