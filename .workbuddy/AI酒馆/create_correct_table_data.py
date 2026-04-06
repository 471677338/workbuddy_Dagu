#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建完全正确的SillyTavern table_data格式
包含所有必需的meta信息
"""

import json
import uuid

def generate_uid():
    """生成sheet的UID（类似于示例中的格式）"""
    # 生成类似 "aPMkvAOl" 这样的8字符UID
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=8))

def create_correct_table(name, content, tochat=True, required=True):
    """创建完全正确的SillyTavern表格结构"""
    
    table_uid = generate_uid()
    
    table = {
        "uid": f"sheet_{table_uid}",
        "name": name,
        "domain": "chat",
        "type": "dynamic",
        "enable": True,
        "required": required,
        "tochat": tochat,
        "triggerSend": False,
        "triggerSendDeep": 1,
        "config": {
            "toChat": tochat,
            "useCustomStyle": False,
            "triggerSendToChat": False,
            "alternateTable": False,
            "insertTable": False,
            "alternateLevel": 0,
            "skipTop": False,
            "selectedCustomStyleKey": "",
            "customStyles": {
                "自定义样式": {
                    "mode": "regex",
                    "basedOn": "html",
                    "regex": "/(^[\\s\\S]*$)/g",
                    "replace": "$1",
                    "replaceDivide": ""
                }
            }
        },
        "sourceData": {
            "value": ""
        },
        "content": content
    }
    
    return table

def create_dialog_narrative_content():
    """创建叙事对话总结内容"""
    
    # 读取之前生成的叙事总结
    try:
        with open("dialog_narrative_summary_formatted.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 提取内容
        content = data["sheet_dialog_narrative_summary"]["content"]
        return content
    except Exception as e:
        print(f"读取对话总结失败: {e}")
        # 创建默认内容
        return [
            ["事件组", "叙事性对话总结", "对话次数统计", "涉及主要角色", "情感走向分析"],
            ["第1组", "暂无数据", "总对话: 0 | 用户: 0 | AI角色: 0", "暂无", "未知"]
        ]

def create_dialog_narrative_table():
    """创建叙事对话总结表（完整格式）"""
    content = create_dialog_narrative_content()
    return create_correct_table("剧情对话叙事总结（每5次对话）", content, True, True)

def create_character_relationships_content():
    """创建角色关系表内容"""
    return [
        ["角色名称", "身份定位", "与尤里西斯的关系", "信任程度", "情感倾向", "互动特点"],
        ["尤里西斯", "主角/魔王继承者", "自我", "高", "纠结/成长", "在神官梦想与魔王命运间挣扎"],
        ["艾娅", "守护魔使", "主仆/同伴/引导者", "绝对忠诚", "深情/占有欲", "绝对忠诚，既是引导者也是依赖者"],
        ["拉丝普汀", "三系魔导士", "队友/盟友/潜在恋人", "中高", "敬佩/好感", "从警惕到信赖，关系逐渐升温"],
        ["法丽", "第八使徒/小圣女", "契约者/信任对象", "中", "感激/亲近", "纯真依赖，视尤里西斯为保护者"]
    ]

def create_character_relationships_table():
    """创建角色关系表（完整格式）"""
    content = create_character_relationships_content()
    return create_correct_table("核心角色关系网络", content, True, True)

def create_world_settings_content():
    """创建世界观设定表内容"""
    return [
        ["设定类型", "关键设定点", "解释说明"],
        ["身份冲突", "魔王与神官的矛盾", "尤里西斯体内同时有魔王血脉和对神官梦想的执着"],
        ["力量特性", "光系魔法与魔王兼容", "魔王血脉能与光明魔法共存，打破传统认知"],
        ["角色定位", "多线发展关系", "与艾娅（守护）、拉丝普汀（盟友）、法丽（契约）等多重关系"],
        ["剧情节奏", "日常与危机交织", "既有温馨日常（裁缝店、温泉），也有冒险战斗（无头骑士）"]
    ]

def create_world_settings_table():
    """创建世界观设定表（完整格式）"""
    content = create_world_settings_content()
    return create_correct_table("世界观统一设定", content, True, False)

def create_plot_progression_content():
    """创建剧情进展表内容"""
    return [
        ["阶段编号", "阶段描述", "关键事件", "情感发展", "关系变化"],
        ["第一阶段", "觉醒与迷茫", "魔王血脉觉醒、接受艾娅", "震惊→接受→困惑", "从孤独到有同伴陪伴"],
        ["第二阶段", "冒险开始", "签订契约（法丽）、探索遗迹", "日常互动中建立信任", "从陌生人到信赖伙伴"],
        ["第三阶段", "关系深化", "温泉谈心、照顾拉丝普汀", "从任务关系到情感依赖", "关系逐渐暧昧升温"],
        ["第四阶段", "抉择时刻", "魔王教育、自我反思", "矛盾达到顶峰，需要决断", "从被动接受命运到主动选择道路"]
    ]

def create_plot_progression_table():
    """创建剧情进展表（完整格式）"""
    content = create_plot_progression_content()
    return create_correct_table("剧情阶段进展表", content, True, True)

def create_key_scenes_content():
    """创建关键场景表内容"""
    return [
        ["场景名称", "发生地点", "涉及角色", "核心互动", "情感意义"],
        ["初遇艾娅", "神官小屋", "尤里西斯、艾娅", "魔王血脉觉醒，守护魔使现身", "命运转折的开始"],
        ["签订契约", "法丽房间", "尤里西斯、法丽、艾娅", "收下八音盒，签订守护契约", "建立第一个正式契约关系"],
        ["温泉谈心", "卡拉尔山脉温泉", "尤里西斯、拉丝普汀", "意外跌落温泉，坦诚交流过往", "关系从队友向更亲密发展"],
        ["魔王教育", "旅馆房间", "尤里西斯、艾娅", "关于魔王命运的严肃谈话", "对未来的思考与抉择"]
    ]

def create_key_scenes_table():
    """创建关键场景表（完整格式）"""
    content = create_key_scenes_content()
    return create_correct_table("关键场景记忆点", content, True, True)

def save_correct_format():
    """保存完全正确的格式"""
    
    # 创建所有表格
    all_tables = {}
    
    # 叙事对话总结（主要的table）
    narrative_table = create_dialog_narrative_table()
    all_tables[narrative_table["uid"]] = narrative_table
    
    # 其他辅助表格
    char_table = create_character_relationships_table()
    all_tables[char_table["uid"]] = char_table
    
    world_table = create_world_settings_table()
    all_tables[world_table["uid"]] = world_table
    
    plot_table = create_plot_progression_table()
    all_tables[plot_table["uid"]] = plot_table
    
    scene_table = create_key_scenes_table()
    all_tables[scene_table["uid"]] = scene_table
    
    # 构建完整的mate结构
    complete_data = all_tables.copy()
    complete_data["mate"] = {
        "type": "chatSheets",
        "version": 1
    }
    
    # 保存格式化版本
    formatted_file = "table_data_correct_formatted.json"
    with open(formatted_file, "w", encoding="utf-8") as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2)
    
    print(f"格式化版本已保存: {formatted_file}")
    
    # 保存压缩版本（SillyTavern导入）
    compressed_file = "table_data_correct_compressed.json"
    with open(compressed_file, "w", encoding="utf-8") as f:
        json.dump(complete_data, f, ensure_ascii=False, separators=(",", ":"))
    
    print(f"压缩版本已保存: {compressed_file}")
    
    # 显示信息
    print(f"共创建 {len(all_tables)} 个表格:")
    for uid, table in all_tables.items():
        print(f"  - {uid}: {table['name']}")
    
    return compressed_file

def main():
    print("开始创建完全正确的SillyTavern table_data格式...")
    print("="*60)
    
    import os
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        compressed_file = save_correct_format()
        
        # 显示文件大小
        file_size = os.path.getsize(compressed_file)
        print(f"\n📊 文件大小: {file_size / 1024:.1f} KB")
        
        print("\n" + "="*60)
        print("✅ 格式完全正确！包含所有必需的meta信息:")
        print("  - uid: sheet_XXXXXX")
        print("  - domain: chat")
        print("  - type: dynamic")  
        print("  - config: 完整配置")
        print("  - sourceData: 空对象")
        print("  - mate: chatSheets类型")
        print("="*60)
        print(f"请导入文件: {compressed_file}")
        
    except Exception as e:
        print(f"创建失败: {e}")

if __name__ == "__main__":
    main()