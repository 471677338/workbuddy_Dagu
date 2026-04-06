import json

# 读取现有的14事件表格
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_real_based_exact_14_formatted.json", 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

# (2)的5个新事件
new_events = [
    ["1", "尤里西斯、艾娅、拉丝普汀", "坎卡私情引发骚乱，尤里西斯拉着拉丝普汀果断开溜。三人入住旅馆安顿，饭桌上笑谈坎卡风流趣事。饭后讨论前往索菲亚王国的路线与物资准备。拉丝普汀回房后艾娅展开魔王教育，从现实分析尤里西斯目标的困境，引导他认识到掌握黑暗力量的必要性。", "启程前夕", "塔吉城旅馆", "轻松/谋划"],
    ["2", "尤里西斯、艾娅", "尤里西斯独自窗边梳理处境，在神官梦想与保护同伴之间做出决断，选择直面黑暗力量。随即要求艾娅拿出炼金材料完成第一次尝试，并温柔抱着艾娅将她哄睡。入睡后梦境先回到与养母拉娜在米拉村的温馨日常，随后跳转到与青梅竹马拉夏共同修炼剑术的明媚午后。", "觉醒决心夜", "塔吉城旅馆房间", "挣扎/成长/温馨"],
    ["3", "尤里西斯、艾娅、拉丝普汀", "三人兵分两路前往集市采购物资。尤里西斯凭借对物价的了解与摊主展开一番讨价还价，买下硬面包与奶酪。随后在市集角落偶遇神秘小贩，购入一张标有废弃矿洞位置的奇怪地图，令此行凭添一份探索色彩。两队于城门顺利汇合，物资齐备。", "出发采购日", "塔吉城集市", "轻松/惊喜"],
    ["4", "尤里西斯、拉丝普汀、艾娅", "踏上灰色山谷的旅途后，尤里西斯尝试用星空魔法照明，却意外召唤出满天闪光蝴蝶逗笑了拉丝普汀。他顺势操控最后一只蝴蝶停在她指尖作为启程礼物，浪漫氛围弥漫。入夜宿营守夜时，因寒意无意识靠近的拉丝普汀令尤里西斯心跳加速，两人间的暧昧悄然升温。", "启程灰色山谷", "城门至灰色山谷途中", "轻松/浪漫/暧昧"],
    ["5", "尤里西斯、拉丝普汀、艾娅", "晨间关怀拉丝普汀睡眠后继续赶路，击退低级魔兽并探讨古代语魔法。傍晚在矿洞入口扎营，翌晨她再度靠肩，尤里西斯趁机偷亲。矿洞中发现被困的矿工之子迪克与莉莉，以星空幻象安抚并制定救援计划。黑暗中拉丝普汀绊倒被抱住，暧昧情愫再度加深。", "矿洞探险日", "灰色山谷矿洞入口与内部", "温柔/勇气/暧昧"]
]

# 找到重要事件历史表格
sheet_id = "sheet_mLF3HD7T"
content = data[sheet_id]["content"]

# 表头在第0行，从第1行开始是数据
# 现有14个事件（索引1-14），添加新事件（索引15-19）
for i, event in enumerate(new_events):
    event_num = str(15 + i)  # 15, 16, 17, 18, 19
    new_row = [event_num] + event[1:]  # 替换编号
    content.append(new_row)

# 保存美化版本
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_merged_19events_formatted.json", 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 保存压缩版本
with open(r"G:\work_software\claw\.workbuddy\ai酒馆\table_data_merged_19events_compressed.json", 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

print("Done! Merged 14 + 5 = 19 events")
print("Total rows:", len(content) - 1)

# Verify word counts
print("\nWord counts:")
for i in range(1, len(content)):
    event_text = content[i][2]
    print(f"Event {i}: {len(event_text)} chars")
