#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豪门惊情1914 - 跑团游戏
"""

import json
import os
import sys
import random
import time

# Windows 终端 UTF-8 支持
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')


def load_game_data():
    """加载游戏数据"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, 'game_data.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    input("\n按回车键继续...")


def print_divider(char='─', length=50):
    print(char * length)


def print_header(title):
    print()
    print_divider('═', 50)
    print(f"  {title}")
    print_divider('═', 50)


def print_choice(index, text):
    print(f"  [{index}] {text}")


def get_choice(max_val, allow_empty=False):
    while True:
        try:
            choice = input(f"\n请选择 (1-{max_val}): ").strip()
            if not choice and allow_empty:
                return 0
            num = int(choice)
            if 1 <= num <= max_val:
                return num
            print(f"请输入 1-{max_val} 之间的数字")
        except ValueError:
            print("请输入数字")


# ═══════════════════════════════════════════
# 角色创建
# ═══════════════════════════════════════════

def character_creation(game_data):
    clear_screen()
    print_header("选择你的身份")
    print()

    templates = game_data['player_templates']
    for i, t in enumerate(templates, 1):
        print(f"  【{t['name']}】")
        print(f"    {t['description']}")
        stats = t['stats']
        print(f"    智力:{stats['intelligence']}  魅力:{stats['charisma']}  敏捷:{stats['agility']}  感知:{stats['perception']}")
        print(f"    技能：{'、'.join(t['skills'])}")
        print()

    print_choice(len(templates) + 1, "自定义角色")
    print()

    choice = get_choice(len(templates) + 1)

    if choice <= len(templates):
        template = templates[choice - 1]
        clear_screen()
        print_header(f"角色预览：{template['name']}")
        print()
        print(f"  {template['background']}")
        print()
        print(f"  智力: {template['stats']['intelligence']}")
        print(f"  魅力: {template['stats']['charisma']}")
        print(f"  敏捷: {template['stats']['agility']}")
        print(f"  感知: {template['stats']['perception']}")
        print(f"  技能：{'、'.join(template['skills'])}")
        print()
        print_choice(1, "确认选择")
        print_choice(2, "返回重新选择")
        print()
        c = get_choice(2)
        if c == 1:
            return template
        else:
            return character_creation(game_data)
    else:
        return custom_character(game_data)


def custom_character(game_data):
    clear_screen()
    print_header("自定义角色")
    print()

    name = input("  请输入角色姓名: ").strip()
    if not name:
        name = "无名侦探"

    desc = input("  请输入角色描述: ").strip()
    if not desc:
        desc = "一位神秘的调查者"

    print()
    print("  请分配属性点（每项 5-15，总共 40 点）")
    print()

    stats = {}
    remaining = 40
    for stat_name, stat_key in [('智力', 'intelligence'), ('魅力', 'charisma'), ('敏捷', 'agility'), ('感知', 'perception')]:
        while True:
            try:
                val = int(input(f"  {stat_name} (剩余 {remaining} 点): ").strip())
                if 5 <= val <= 15 and val <= remaining:
                    stats[stat_key] = val
                    remaining -= val
                    break
                print(f"  请输入 5-15 之间的数字，且不超过剩余点数")
            except ValueError:
                print("  请输入数字")

    skills_input = input("\n  请输入技能（用逗号分隔）: ").strip()
    skills = [s.strip() for s in skills_input.split(',') if s.strip()]
    if not skills:
        skills = ["调查", "观察"]

    bg = input("\n  请输入角色背景故事: ").strip()
    if not bg:
        bg = f"你是一名叫做{name}的调查者，擅长{skills[0]}。"

    return {
        'id': 'custom',
        'name': name,
        'description': desc,
        'stats': stats,
        'skills': skills,
        'background': bg
    }


# ═══════════════════════════════════════════
# 案件选择
# ═══════════════════════════════════════════

def select_case(game_data):
    clear_screen()
    print_header("选择案件")
    print()

    cases = game_data['cases']
    for i, case in enumerate(cases, 1):
        stars = '★' * case['difficulty'] + '☆' * (5 - case['difficulty'])
        print(f"  [{i}] {case['name']}")
        print(f"      {case['date']} | {case['location']}")
        print(f"      {case['description']}")
        print(f"      难度: {stars}")
        print()

    choice = get_choice(len(cases))
    return cases[choice - 1]


# ═══════════════════════════════════════════
# 游戏主循环
# ═══════════════════════════════════════════

class GameState:
    def __init__(self, character, case):
        self.character = character
        self.case = case
        self.current_scene_id = case['scenes'][0]
        self.inventory = []
        self.clues = []
        self.relationships = {}
        self.suspicion = {}
        self.log = []

    def add_log(self, text):
        self.log.append(text)

    def add_clue(self, clue):
        if not any(c['id'] == clue['id'] for c in self.clues):
            self.clues.append(clue)
            self.add_log(f"获得线索：{clue['name']}")
            return True
        return False

    def get_stat(self, stat_name):
        return self.character['stats'].get(stat_name, 10)

    def skill_check(self, skill_name, difficulty):
        stat_map = {
            '调查': 'intelligence', '推理': 'intelligence',
            '观察': 'perception', '说服': 'charisma',
            '医疗': 'intelligence', '采访': 'charisma',
            '权谋': 'charisma', '战斗': 'agility',
            '毒理分析': 'intelligence'
        }
        stat = stat_map.get(skill_name, 'intelligence')
        value = self.get_stat(stat)
        roll = random.randint(1, 20)
        self.add_log(f"【{skill_name}判定】 属性:{value} 骰值:{roll} 难度:{difficulty}")
        return roll <= value or roll == 1


def get_scene(game_data, scene_id):
    return game_data.get('scenes', {}).get(scene_id)


def get_dialogue_by_npc(game_data, npc_name):
    for key, dialogue in game_data.get('dialogues', {}).items():
        if dialogue['speaker'] == npc_name:
            return key, dialogue
    return None, None


def scene_exploration(state, game_data):
    """场景探索主循环"""
    while True:
        scene = get_scene(game_data, state.current_scene_id)
        if not scene:
            print("  场景数据加载失败")
            return

        clear_screen()
        print_header(scene['name'])
        print()
        print(f"  {scene['description']}")
        print()

        # 显示角色状态
        print_divider('·', 50)
        print(f"  智力:{state.get_stat('intelligence')}  魅力:{state.get_stat('charisma')}  "
              f"敏捷:{state.get_stat('agility')}  感知:{state.get_stat('perception')}  "
              f"线索:{len(state.clues)}")
        print_divider('·', 50)
        print()

        # 操作菜单
        choices = []
        idx = 1

        # NPC 对话
        npcs = scene.get('npcs', [])
        for npc in npcs:
            print_choice(idx, f"与{npc}对话")
            choices.append(('talk', npc))
            idx += 1

        # 调查场景
        print_choice(idx, "调查场景")
        choices.append(('investigate', None))
        idx += 1

        # 查看线索
        if state.clues:
            print_choice(idx, f"查看已收集线索 ({len(state.clues)}条)")
            choices.append(('clues', None))
            idx += 1

        # 推理指认（需要至少2条线索）
        if len(state.clues) >= 2:
            print_choice(idx, "进行推理指认")
            choices.append(('deduce', None))
            idx += 1

        # 移动到其他场景
        connections = scene.get('connections', [])
        for conn_id in connections:
            conn_scene = get_scene(game_data, conn_id)
            if conn_scene:
                print_choice(idx, f"前往{conn_scene['name']}")
                choices.append(('move', conn_id))
                idx += 1

        # 查看日志
        if state.log:
            print_choice(idx, "查看日志")
            choices.append(('log', None))
            idx += 1

        # 存档
        print_choice(idx, "存档")
        choices.append(('save', None))
        idx += 1

        # 退出
        print_choice(idx, "返回主菜单")
        choices.append(('quit', None))
        idx += 1

        print()
        choice = get_choice(idx)

        action, data = choices[choice - 1]

        if action == 'talk':
            handle_dialogue(state, game_data, data)
        elif action == 'investigate':
            handle_investigate(state, game_data)
        elif action == 'clues':
            show_clues(state)
        elif action == 'deduce':
            result = handle_deduction(state, game_data)
            if result is not None:
                return result
        elif action == 'move':
            state.current_scene_id = data
            state.add_log(f"移动到{get_scene(game_data, data)['name']}")
        elif action == 'log':
            show_log(state)
        elif action == 'save':
            save_game(state)
        elif action == 'quit':
            return None


# ═══════════════════════════════════════════
# 对话系统
# ═══════════════════════════════════════════

def handle_dialogue(state, game_data, npc_name):
    dialogue_key, dialogue = get_dialogue_by_npc(game_data, npc_name)

    if not dialogue:
        clear_screen()
        print_header(f"与{npc_name}对话")
        print()
        print(f"  {npc_name}看着你，似乎没有什么要说的。")
        pause()
        return

    while True:
        clear_screen()
        print_header(f"与{npc_name}对话")
        print()
        state.add_log(f"与{npc_name}交谈")

        options = dialogue['options']
        print(f"  {npc_name}：「{options[0]['response']}」")
        print()

        for i, opt in enumerate(options, 1):
            print_choice(i, opt['text'])
        print_choice(len(options) + 1, "结束对话")
        print()

        choice = get_choice(len(options) + 1)

        if choice > len(options):
            break

        option = options[choice - 1]
        clear_screen()
        print_header(f"与{npc_name}对话")
        print()
        print(f"  你：「{option['text']}」")
        print()
        print(f"  {npc_name}：「{option['response']}」")

        # 处理效果
        effect = option.get('effect', {})
        if effect:
            print()
            if 'relationship' in effect and 'change' in effect:
                rel_name = effect['relationship']
                change = effect['change']
                state.relationships[rel_name] = state.relationships.get(rel_name, 0) + change
                if change > 0:
                    print(f"  ▲ 与{rel_name}的关系 +{change}")
                else:
                    print(f"  ▼ 与{rel_name}的关系 {change}")

            if 'suspicion' in effect and 'change' in effect:
                sus_name = effect['suspicion']
                change = effect['change']
                state.suspicion[sus_name] = state.suspicion.get(sus_name, 0) + change
                state.add_log(f"对{sus_name}的怀疑 +{change}")
                print(f"  ▲ 对{sus_name}的怀疑 +{change}")

            if 'clue' in effect:
                clue_id = effect['clue']
                case_clues = state.case.get('clues', [])
                for clue in case_clues:
                    if clue['id'] == clue_id:
                        if state.add_clue(clue):
                            print(f"  🔍 获得线索：{clue['name']}")
                            print(f"     {clue['description']}")
                        break

            if 'alibi_check' in effect:
                print(f"  📋 调查结果：{effect['result']}")
                state.add_log(f"不在场证明调查：{effect['result']}")

            if 'confession' in effect:
                print(f"  ⚡ {npc_name}似乎说漏了什么...")
                state.add_log(f"{npc_name}的供述出现矛盾")

        pause()
        break


# ═══════════════════════════════════════════
# 调查系统
# ═══════════════════════════════════════════

def handle_investigate(state, game_data):
    scene_id = state.current_scene_id
    case_clues = state.case.get('clues', [])
    scene_clues = [c for c in case_clues if c.get('location') == scene_id]

    # 也检查场景物品
    scene = get_scene(game_data, scene_id)
    items = scene.get('items', []) if scene else []

    clear_screen()
    print_header("调查场景")
    print()

    if not scene_clues and not items:
        print("  你仔细搜索了这个区域，没有发现什么特别的东西。")
        pause()
        return

    found_any = False

    # 检查线索
    for clue in scene_clues:
        if any(c['id'] == clue['id'] for c in state.clues):
            continue  # 已收集

        required_skill = clue.get('required_skill', '调查')
        difficulty = clue.get('difficulty', 5)

        print(f"  你注意到一个可疑的地方...")
        print(f"  需要使用【{required_skill}】技能进行调查（难度:{difficulty}）")
        print()

        print_choice(1, f"使用{required_skill}调查")
        print_choice(2, "放弃调查")
        print()

        c = get_choice(2)
        if c == 1:
            if state.skill_check(required_skill, difficulty):
                print()
                print(f"  ✓ 调查成功！")
                print(f"  你发现了：{clue['name']}")
                print(f"  {clue['description']}")
                if clue.get('hint'):
                    print(f"  提示：{clue['hint']}")
                state.add_clue(clue)
                found_any = True
            else:
                print()
                print(f"  ✗ 调查失败...")
                print(f"  你没能在这个区域发现有用的线索。")
        else:
            print(f"  你决定暂时放弃调查。")
        print()
        pause()
        return  # 一次调查只找一个线索

    # 显示场景物品
    if items and not found_any:
        print("  场景中可以检查的物品：")
        print()
        for i, item in enumerate(items, 1):
            print_choice(i, item)
        print_choice(len(items) + 1, "离开")
        print()

        c = get_choice(len(items) + 1)
        if c <= len(items):
            item = items[c - 1]
            print(f"\n  你检查了【{item}】。")
            # 根据物品名尝试匹配线索
            for clue in scene_clues:
                if clue['name'] in item or item in clue['name']:
                    if not any(c['id'] == clue['id'] for c in state.clues):
                        if state.skill_check(clue.get('required_skill', '调查'), clue.get('difficulty', 5)):
                            print(f"  ✓ 你在这个物品上发现了线索！")
                            state.add_clue(clue)
                            pause()
                            return
            print(f"  没有发现特别的东西。")
            pause()


# ═══════════════════════════════════════════
# 推理系统
# ═══════════════════════════════════════════

def handle_deduction(state, game_data):
    clear_screen()
    print_header("推理指认")
    print()
    print("  根据你收集的线索，指认你认为的凶手。")
    print()
    print_divider('·', 50)
    print("  已收集的线索：")
    for clue in state.clues:
        print(f"  • {clue['name']}：{clue['description']}")
    print_divider('·', 50)
    print()

    suspects = state.case.get('suspects', [])
    print("  嫌疑人列表：")
    print()
    for i, suspect in enumerate(suspects, 1):
        sus_val = state.suspicion.get(suspect['name'], 0)
        print(f"  [{i}] {suspect['name']}")
        print(f"      {suspect['description']}")
        print(f"      动机：{suspect['motive']}")
        print(f"      不在场证明：{suspect['alibi']}")
        if sus_val > 0:
            print(f"      可疑度：{'!' * min(sus_val // 5, 5)}")
        print()

    print_choice(len(suspects) + 1, "返回场景继续调查")
    print()

    choice = get_choice(len(suspects) + 1)
    if choice > len(suspects):
        return None

    accused = suspects[choice - 1]

    clear_screen()
    print_header("确认指认")
    print()
    print(f"  你确定要指认【{accused['name']}】为凶手吗？")
    print(f"  {accused['description']}")
    print()
    print_choice(1, "确认指认")
    print_choice(2, "再想想")
    print()

    c = get_choice(2)
    if c == 2:
        return None

    # 判断结果
    real_killer = next(s for s in suspects if s['is_guilty'])
    solved = accused['name'] == real_killer['name']

    clear_screen()
    if solved:
        print_header("案件破解！")
        print()
        print(f"  恭喜你成功破解了「{state.case['name']}」！")
        print()
        print(f"  真相：{state.case['solution']}")
        print()
        print_divider('·', 50)
        print(f"  线索收集：{len(state.clues)} 条")
        print(f"  日志记录：{len(state.log)} 条")
        print(f"  案件难度：{'★' * state.case['difficulty']}")
        print_divider('·', 50)
    else:
        print_header("指认错误")
        print()
        print(f"  你指认的{accused['name']}并非真凶。")
        print()
        print(f"  真相：{state.case['solution']}")
        print()
        print(f"  真正的凶手是：{real_killer['name']}")
        print(f"  {real_killer['description']}")

    pause()
    return solved


# ═══════════════════════════════════════════
# 显示系统
# ═══════════════════════════════════════════

def show_clues(state):
    clear_screen()
    print_header("已收集线索")
    print()
    if not state.clues:
        print("  暂无线索")
    else:
        for i, clue in enumerate(state.clues, 1):
            print(f"  [{i}] {clue['name']}")
            print(f"      {clue['description']}")
            if clue.get('hint'):
                print(f"      提示：{clue['hint']}")
            print()
    pause()


def show_log(state):
    clear_screen()
    print_header("游戏日志")
    print()
    if not state.log:
        print("  暂无日志")
    else:
        for entry in state.log:
            print(f"  • {entry}")
    pause()


# ═══════════════════════════════════════════
# 存档系统
# ═══════════════════════════════════════════

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saves')


def save_game(state):
    os.makedirs(SAVE_DIR, exist_ok=True)

    clear_screen()
    print_header("存档")
    print()

    saves = []
    for i in range(1, 4):
        save_file = os.path.join(SAVE_DIR, f'slot{i}.json')
        if os.path.exists(save_file):
            with open(save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            char_name = data.get('character', {}).get('name', '未知')
            case_name = data.get('case', {}).get('name', '未知')
            print_choice(i, f"存档{i}: {char_name} - {case_name}")
            saves.append(True)
        else:
            print_choice(i, f"存档{i}: 空")
            saves.append(False)

    print_choice(4, "返回")
    print()

    choice = get_choice(4)
    if choice == 4:
        return

    slot = choice
    save_file = os.path.join(SAVE_DIR, f'slot{slot}.json')
    data = {
        'character': state.character,
        'case': state.case,
        'current_scene_id': state.current_scene_id,
        'inventory': state.inventory,
        'clues': state.clues,
        'relationships': state.relationships,
        'suspicion': state.suspicion,
        'log': state.log
    }

    with open(save_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ 游戏已保存到存档{slot}")
    pause()


def load_game_menu(game_data):
    os.makedirs(SAVE_DIR, exist_ok=True)

    clear_screen()
    print_header("读取存档")
    print()

    saves = []
    for i in range(1, 4):
        save_file = os.path.join(SAVE_DIR, f'slot{i}.json')
        if os.path.exists(save_file):
            with open(save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            char_name = data.get('character', {}).get('name', '未知')
            case_name = data.get('case', {}).get('name', '未知')
            print_choice(i, f"存档{i}: {char_name} - {case_name}")
            saves.append(data)
        else:
            print_choice(i, f"存档{i}: 空")
            saves.append(None)

    print_choice(4, "返回")
    print()

    choice = get_choice(4)
    if choice == 4 or saves[choice - 1] is None:
        return None

    data = saves[choice - 1]
    state = GameState(data['character'], data['case'])
    state.current_scene_id = data.get('current_scene_id', data['case']['scenes'][0])
    state.inventory = data.get('inventory', [])
    state.clues = data.get('clues', [])
    state.relationships = data.get('relationships', {})
    state.suspicion = data.get('suspicion', {})
    state.log = data.get('log', [])

    return state


# ═══════════════════════════════════════════
# 主菜单
# ═══════════════════════════════════════════

def main_menu(game_data):
    while True:
        clear_screen()
        print_header("豪门惊情1914")
        print()
        print("  1914年，中华大地正值乱世。")
        print("  北洋政府统治下的中国，表面繁荣，暗流涌动。")
        print("  在这风云变幻的年代，一系列离奇的案件接连发生...")
        print()
        print_divider('─', 50)
        print()
        print_choice(1, "开始新游戏")
        print_choice(2, "读取存档")
        print_choice(3, "游戏说明")
        print_choice(4, "退出游戏")
        print()

        choice = get_choice(4)

        if choice == 1:
            character = character_creation(game_data)
            if character:
                case = select_case(game_data)
                state = GameState(character, case)
                state.add_log(f"开始调查「{case['name']}」")
                result = scene_exploration(state, game_data)
                if result is not None:
                    # 返回主菜单
                    pass
        elif choice == 2:
            state = load_game_menu(game_data)
            if state:
                state.add_log("读取存档成功")
                scene_exploration(state, game_data)
        elif choice == 3:
            show_instructions()
        elif choice == 4:
            clear_screen()
            print()
            print("  感谢游玩「豪门惊情1914」")
            print("  版权所有 © 遥光")
            print()
            break


def show_instructions():
    clear_screen()
    print_header("游戏说明")
    print()
    print("  操作说明：")
    print("  • 输入数字选择对应的选项")
    print("  • 在场景中探索可以发现线索和物品")
    print("  • 与NPC对话可以获取关键信息")
    print("  • 收集足够线索后可以进行推理指认")
    print("  • 正确指认凶手即可破案")
    print()
    print("  属性说明：")
    print("  • 智力：影响推理、调查、医疗等技能")
    print("  • 魅力：影响说服、采访、权谋等技能")
    print("  • 敏捷：影响战斗等技能")
    print("  • 感知：影响观察等技能")
    print()
    print("  技能判定：")
    print("  • 每次判定掷1-20的骰子")
    print("  • 骰值 <= 属性值 即为成功")
    print("  • 骰值为1 必定成功（大成功）")
    print()
    print_divider('─', 50)
    print("  版权所有 © 遥光")
    pause()


# ═══════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════

if __name__ == '__main__':
    try:
        game_data = load_game_data()
        main_menu(game_data)
    except KeyboardInterrupt:
        print("\n\n  游戏已退出")
    except Exception as e:
        print(f"\n  游戏出错：{e}")
        import traceback
        traceback.print_exc()
