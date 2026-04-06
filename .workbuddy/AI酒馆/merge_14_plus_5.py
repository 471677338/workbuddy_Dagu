import json

# 读取之前的14事件
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_real_based_exact_14_formatted.json", 'r', encoding='utf-8-sig') as f:
    old_data = json.load(f)

old_events = old_data["sheet_mLF3HD7T"]["content"][1:]  # 去掉表头

# 读取刚创建的5事件（只有表头）
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_v2_correct_formatted.json", 'r', encoding='utf-8-sig') as f:
    new_data = json.load(f)

new_events = new_data["sheet_mLF3HD7T"]["content"][1:]  # 去掉表头

# 合并事件（14 + 5 = 19）
all_events = old_events + new_events

# 更新事件编号
for i, event in enumerate(all_events):
    event[0] = str(i + 1)

# 重新构建content
new_data["sheet_mLF3HD7T"]["content"] = [["", "角色", "事件简述", "日期", "地点", "情绪"]] + all_events

# 保存美化版
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_full_19events_formatted.json", 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

# 保存压缩版
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_full_19events_compressed.json", 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, separators=(',', ':'))

print("Done! Merged 14 + 5 = 19 events")

# 打印所有事件标题
print("\nAll events:")
for i, event in enumerate(all_events):
    print(f"{i+1}. [{event[3]}] {event[4]}")
