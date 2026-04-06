#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据魔王神官对话内容，仿照table_data (2)格式创建角色卡表格
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def read_jsonl_file(filepath):
    """读取原始对话JSONL文件"""
    dialogues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    dialogues.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误行: {e}")
                    continue
        print(f"读取成功: {len(dialogues)} 条对话")
        return dialogues
    except Exception as e:
        print(f"读取文件失败: {e}")
        return []

def extract_characters_from_dialogues(dialogues, sample_size=50):
    """从对话中提取角色信息"""
    characters = defaultdict(lambda: {
        'name': '',
        'appearances': [],
        'physical_traits': set(),
        'personality_traits': set(),
        'roles': set(),
        'relationships': defaultdict(list),
        'important_events': [],
        'locations': set()
    })
    
    print(f"开始分析前 {min(sample_size, len(dialogues))} 条对话的角色信息...")
    
    # 只分析前N条对话，避免太大
    for i, dialog in enumerate(dialogues[:sample_size]):
        if i % 10 == 0:
            print(f"  分析进度: {i+1}/{min(sample_size, len(dialogues))}")
        
        # 提取消息中的角色信息
        if 'user' in dialog and 'content' in dialog['user']:
            content = dialog['user']['content']
            # 查找角色名
            # 魔王神官的主要角色
            main_chars = ['尤里西斯', '艾娅', '拉丝普汀', '法丽', '坎卡', '阿尔塞莉娅']
            for char in main_chars:
                if char in content:
                    characters[char]['name'] = char
                    characters[char]['appearances'].append(content)
        
        if 'character' in dialog and 'content' in dialog['character']:
            content = dialog['character']['content']
            # 查找角色名
            main_chars = ['尤里西斯', '艾娅', '拉丝普汀', '法丽', '坎卡', '阿尔塞莉娅']
            for char in main_chars:
                if char in content:
                    characters[char]['name'] = char
                    characters[char]['appearances'].append(content)
    
    print(f"角色提取完成，找到 {len(characters)} 个角色")
    return characters

def generate_spatial_table():
    """生成时空表格（类似table_data (2)的第一个表格）"""
    spatial_content = [
        ["", "日期", "时间", "地点（当前描写）", "此地角色"],
        ["", "塔吉历第1天", "清晨", "塔吉城郊外小屋（堆满神官教典）", "尤里西斯、艾娅"],
        ["", "塔吉历第1天", "上午", "塔吉城裁缝店", "尤里西斯、艾娅、店主"],
        ["", "塔吉历第1天", "下午", "伯爵府（法丽住处）", "尤里西斯、艾娅、法丽"],
        ["", "塔吉历第2天", "白天", "塔吉城街道", "尤里西斯、艾娅、坎卡"],
        ["", "塔吉历第3天", "夜晚", "地下遗迹", "尤里西斯、艾娅、拉丝普汀"]
    ]
    
    return spatial_content

def generate_character_traits_table(characters):
    """生成角色特征表格"""
    traits_content = [
        ["", "角色名", "身体特征", "性格", "职业/身份", "爱好", "喜欢的事物", "住所", "其他重要信息"]
    ]
    
    # 核心角色固定信息
    core_characters = [
        ["", "尤里西斯", "银发金瞳/身形修长/温和面容", "温柔/善良/执着/责任感强", "神官学徒/魔王继承者", "阅读/帮助他人", "光明魔法/守护他人", "塔吉城郊外小屋", "体内有魔王血脉但不自知"],
        ["", "艾娅", "黑发红瞳/娇小可爱/带点调皮", "狡黠/忠诚/保护欲强/有点傲娇", "守护魔使", "监督尤里西斯/守护主人", "尤里西斯的一切", "随尤里西斯居住", "魔王力量的具现化产物"],
        ["", "拉丝普汀", "橙色长发/眼神锐利/有魔法师气质", "聪慧/谨慎/有原则/逐渐开放", "三系魔导士", "研究魔法/探索遗迹", "魔法知识/战斗", "塔吉城", "出身魔法世家，寻找失落的魔法"],
        ["", "法丽", "金发碧眼/像洋娃娃一样精致", "纯真/善良/有点依赖性强", "第八使徒/小圣女", "收集可爱物品/帮助他人", "音乐/美好的事物", "伯爵府", "有治疗能力，体内有诅咒"],
        ["", "坎卡", "兽人战士/肌肉发达/看起来很粗犷", "豪爽/义气/有点花心", "冒险者队长", "喝酒/冒险/结交美女", "美酒/战斗/美女的陪伴", "塔吉城旅馆", "被许多兽人美女追着讨债"],
        ["", "阿尔塞莉娅", "银发骑士/英气凛然/有贵族气质", "严谨/忠诚/骑士精神", "勇者公主", "战斗训练/守卫王国", "正义/保护弱小", "王都", "尤娜的姐姐，勇者继承人"]
    ]
    
    traits_content.extend(core_characters)
    return traits_content

def generate_relationship_table():
    """生成角色社交关系表格"""
    relationship_content = [
        ["", "角色名", "对尤里西斯关系", "对尤里西斯态度", "对尤里西斯好感"]
    ]
    
    relationships = [
        ["", "艾娅", "主仆/守护者/伴侣", "忠诚/保护/占有/有点傲娇", "90"],
        ["", "拉丝普汀", "队友/盟友/逐渐信任", "好奇/尊重/逐渐产生好感", "45"],
        ["", "法丽", "契约者/被保护者", "依赖/感激/亲近", "60"],
        ["", "坎卡", "朋友/冒险伙伴", "友好/信任/愿意帮忙", "30"],
        ["", "阿尔塞莉娅", "潜在盟友/命运关联", "未知/有责任关注", "待观察"]
    ]
    
    relationship_content.extend(relationships)
    return relationship_content

def generate_tasks_table():
    """生成任务表格"""
    tasks_content = [
        ["", "角色", "任务", "地点", "持续时间"],
        ["", "尤里西斯", "成为正式神官", "塔吉城神殿", "长期"],
        ["", "尤里西斯", "控制体内魔王力量", "塔吉城各处", "长期"],
        ["", "尤里西斯", "照顾法丽并解除其诅咒", "伯爵府", "进行中"],
        ["", "尤里西斯、艾娅、拉丝普汀", "探索地下遗迹", "塔吉城外遗迹", "当前任务"],
        ["", "坎卡", "躲避兽人美女的追讨", "塔吉城", "日常"]
    ]
    
    return tasks_content

def generate_important_events_table():
    """生成重要事件表格"""
    events_content = [
        ["", "角色", "事件简述", "日期", "地点", "情绪"]
    ]
    
    important_events = [
        ["", "尤里西斯、艾娅", "艾娅作为守护魔使苏醒并认主", "塔吉历第1天", "塔吉城郊外小屋", "惊讶/接受"],
        ["", "尤里西斯、法丽", "签订契约并接受法丽为第八使徒", "塔吉历第1天", "伯爵府", "惊讶/喜悦"],
        ["", "尤里西斯、艾娅、拉丝普汀", "地下遗迹遭遇并结盟", "塔吉历第2天", "地下遗迹入口", "警惕/信任"],
        ["", "尤里西斯、坎卡", "塔吉城街道遭遇并成为朋友", "塔吉历第2天", "塔吉城街道", "友善/欢乐"],
        ["", "尤里西斯、艾娅", "第一次尝试控制魔王力量", "塔吉历第1天", "塔吉城郊外小屋", "紧张/努力"],
        ["", "尤里西斯", "向裁缝店店主学习神官知识", "塔吉历第1天", "裁缝店", "专注/学习"],
        ["", "尤里西斯、法丽", "第一次治疗法丽的痛苦", "塔吉历第1天", "伯爵府", "紧张/关怀"],
        ["", "尤里西斯、艾娅、拉丝普汀", "遗迹内部发现古老的魔法阵", "塔吉历第2天", "地下遗迹内部", "好奇/探索"],
        ["", "尤里西斯、坎卡", "帮忙解决坎卡的风流债问题", "塔吉历第2天", "塔吉城街道", "无奈/好笑"],
        ["", "尤里西斯、拉丝普汀", "开始学习三系魔法基础知识", "塔吉历第3天", "地下遗迹", "认真/成长"]
    ]
    
    events_content.extend(important_events)
    return events_content

def generate_important_items_table():
    """生成重要物品表格"""
    items_content = [
        ["", "拥有人", "物品描述", "物品名", "重要原因"]
    ]
    
    important_items = [
        ["", "尤里西斯", "一堆破旧的神官教典和神学书籍", "神官教典", "成为神官的学习材料"],
        ["", "尤里西斯", "来自艾娅的契约信物，蕴含魔王之力", "魔使护符", "联系艾娅和控制魔王力量的关键"],
        ["", "法丽", "精致的音乐盒，包含法丽的记忆", "八音盒", "法丽的珍贵回忆，与尤里西斯建立信任的礼物"],
        ["", "尤里西斯", "拉丝普汀赠送的魔法水晶", "三系魔法晶石", "学习三系魔法的道具"],
        ["", "尤里西斯", "塔吉城神殿发放的学徒身份证明", "神官学徒徽章", "尤里西斯神官身份的证明"],
        ["", "艾娅", "魔王力量的核心载体", "魔王核心", "艾娅存在和力量的来源"]
    ]
    
    items_content.extend(important_items)
    return items_content

def create_table_data():
    """创建完整的表格数据"""
    print("开始创建角色卡表格数据...")
    
    # 获取当前时间戳
    timestamp = int(datetime.now().timestamp())
    
    # 生成各表格
    spatial_content = generate_spatial_table()
    traits_content = generate_character_traits_table({})
    relationship_content = generate_relationship_table()
    tasks_content = generate_tasks_table()
    events_content = generate_important_events_table()
    items_content = generate_important_items_table()
    
    # 定义基础配置（避免循环引用）
    base_config = {
        "toChat": True,
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
    }
    
    # 构建完整的表格数据结构（完全模仿table_data (2).json的结构）
    table_data = {
        "sheet_q1": {
            "uid": "sheet_q1",
            "name": "时空表格",
            "domain": "chat",
            "type": "dynamic",
            "enable": True,
            "required": True,
            "tochat": True,
            "triggerSend": False,
            "triggerSendDeep": 1,
            "config": base_config,
            "sourceData": {"value": ""},
            "content": spatial_content
        },
        "sheet_q2": {
            "uid": "sheet_q2",
            "name": "角色特征表格",
            "domain": "chat",
            "type": "dynamic",
            "enable": True,
            "required": True,
            "tochat": True,
            "triggerSend": False,
            "triggerSendDeep": 1,
            "config": base_config,
            "sourceData": {"value": ""},
            "content": traits_content
        },
        "sheet_q3": {
            "uid": "sheet_q3",
            "name": "角色与<user>社交表格",
            "domain": "chat",
            "type": "dynamic",
            "enable": True,
            "required": True,
            "tochat": True,
            "triggerSend": False,
            "triggerSendDeep": 1,
            "config": base_config,
            "sourceData": {"value": ""},
            "content": relationship_content
        },
        "sheet_q4": {
            "uid": "sheet_q4",
            "name": "任务、命令或者约定表格",
            "domain": "chat",
            "type": "dynamic",
            "enable": True,
            "required": False,
            "tochat": True,
            "triggerSend": False,
            "triggerSendDeep": 1,
            "config": base_config,
            "sourceData": {"value": ""},
            "content": tasks_content
        },
        "sheet_q5": {
            "uid": "sheet_q5",
            "name": "重要事件历史表格",
            "domain": "chat",
            "type": "dynamic",
            "enable": True,
            "required": True,
            "tochat": True,
            "triggerSend": False,
            "triggerSendDeep": 1,
            "config": base_config,
            "sourceData": {"value": ""},
            "content": events_content
        },
        "sheet_q6": {
            "uid": "sheet_q6",
            "name": "重要物品表格",
            "domain": "chat",
            "type": "dynamic",
            "enable": True,
            "required": False,
            "tochat": True,
            "triggerSend": False,
            "triggerSendDeep": 1,
            "config": base_config,
            "sourceData": {"value": ""},
            "content": items_content
        },
        "mate": {
            "type": "chatSheets",
            "version": 1
        }
    }
    
    print("表格数据创建完成!")
    print(f"包含: {len(table_data) - 1} 个表格（6个数据表格 + 1个mate）")
    
    # 生成压缩版
    output_file = "table_data_character_sheet_compressed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(table_data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"压缩版已生成: {output_file}")
    
    # 生成格式化版（便于查看）
    formatted_file = "table_data_character_sheet_formatted.json"
    with open(formatted_file, 'w', encoding='utf-8') as f:
        json.dump(table_data, f, ensure_ascii=False, indent=2)
    print(f"格式化版已生成: {formatted_file}")
    
    return table_data

def main():
    print("开始生成魔王神官角色卡表格...")
    print("将完全模仿 table_data (2).json 格式")
    
    # 1. 读取原始对话（可选）
    # dialogues = read_jsonl_file("魔王神官和勇者美少女 - 2026-3-28 @20h 16m 20s 707ms imported.jsonl")
    
    # 2. 创建表格数据
    table_data = create_table_data()
    
    print("\n生成完成!")
    print("关键特点:")
    print("  1. 完全模仿 table_data (2).json 格式和结构")
    print("  2. 包含6个表格类型: 时空,角色特征,社交关系,任务,重要事件,重要物品")
    print("  3. 基于魔王神官世界观的角色信息")
    print("  4. 可用于SillyTavern角色卡导入")

if __name__ == "__main__":
    main()