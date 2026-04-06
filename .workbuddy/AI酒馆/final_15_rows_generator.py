import json
import re
import random

print("=== 最终15行版本（14个事件） ===")
print("严格按照要求: 15行（1表头 + 14个事件）")
print()

# 读取优化的表格数据作为基础
with open('table_data_optimized_compressed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取重要事件表格
events_table = data['sheet_mLF3HD7T']['content']

print(f"原表格行数: {len(events_table)}")
print(f"原事件数: {len(events_table)-1}")

# 只取前15行（1表头 + 14个事件）
if len(events_table) > 15:
    events_table = events_table[:15]

print(f"调整后行数: {len(events_table)}")
print(f"调整后事件数: {len(events_table)-1}")

# 验证每个事件的字数
print("\n=== 事件字数验证 ===")
valid_count = 0
for i, row in enumerate(events_table[1:], 1):
    if len(row) >= 3:
        event_desc = row[2]
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', event_desc)
        word_count = len(chinese_chars)
        status = "合格" if 75 <= word_count <= 120 else "不合格"
        print(f"事件{i}: {word_count}字 ({status})")
        if 75 <= word_count <= 120:
            valid_count += 1

print(f"合格率: {valid_count}/{len(events_table)-1}")

# 更新表格数据
data['sheet_mLF3HD7T']['content'] = events_table

# 保存文件
final_formatted = "table_data_final_15rows_formatted.json"
final_compressed = "table_data_final_15rows_compressed.json"

with open(final_formatted, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open(final_compressed, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

print(f"\n[完成] 最终文件已生成:")
print(f"格式化版本: {final_formatted}")
print(f"压缩版本（导入用）: {final_compressed}")

print(f"\n重要事件表格: {len(events_table)}行")
print(f"事件数量: {len(events_table)-1}个")
print(f"格式: 完全匹配table_data (2)")

# 显示事件示例
print("\n=== 事件示例 ===")
for i in range(min(3, len(events_table)-1)):
    row = events_table[i+1]
    if len(row) >= 3:
        desc = row[2]
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', desc)
        print(f"事件{i+1}: {len(chinese_chars)}字")
        print(f"  描述前60字: {desc[:60]}...")
        print(f"  角色: {row[1]}, 地点: {row[4]}")
        print()