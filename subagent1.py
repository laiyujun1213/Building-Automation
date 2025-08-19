import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件（主代理任务、原子动作库、环境物品库）"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"文件未找到：{file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"JSON格式错误：{file_path}")

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """保存数据到JSON文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_keywords(text: str) -> List[str]:
    """提取文本关键词（过滤短词和无意义词汇）"""
    text = re.sub(r'[^\w\s]', '', text)
    stopwords = ["的", "了", "进行", "完成", "处理", "使用", "操作", "对", "在", "为"]  # 自定义停用词
    return [word for word in text.lower().split() if len(word) > 1 and word not in stopwords]

def extract_potential_action(subtask: str) -> str:
    """从子任务中提取潜在原子动作（优先动词）"""
    # 简单动词提取规则（可根据实际场景扩展）
    action_verbs = ["勘察", "测量", "搬运", "安装", "调试", "检查", "清理", "准备", "布置", "连接", "拆卸", "操作"]
    keywords = extract_keywords(subtask)
    for verb in action_verbs:
        if verb in keywords:
            return verb
    return keywords[0] if keywords else f"未识别动作_{datetime.now().strftime('%H%M%S')}"

def extract_potential_item(subtask: str) -> str:
    """从子任务中提取潜在环境物品（优先名词）"""
    # 简单名词提取规则（可根据实际场景扩展）
    item_nouns = ["场地", "设备", "工具", "材料", "仪器", "图纸", "零件", "配件", "区域", "设施"]
    keywords = extract_keywords(subtask)
    for noun in item_nouns:
        if noun in keywords:
            return noun
    return keywords[0] if keywords else f"未识别物品_{datetime.now().strftime('%H%M%S')}"

def update_atomic_actions(atomic_actions: Dict[str, Any], new_action: str, subtask: str) -> Dict[str, Any]:
    """更新原子动作库，添加未匹配的新动作（去重并标记补充信息）"""
    # 检查是否已存在该动作
    for category, actions in atomic_actions["categories"].items():
        if new_action in actions:
            return atomic_actions  # 已存在则不重复添加
    # 新增动作（默认添加到基础操作分类，可根据需求调整）
    supplement_info = {
        "action": new_action,
        "supplement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_subtask": subtask
    }
    atomic_actions["categories"]["basic_operations"].append(new_action)
    atomic_actions["total_actions"] += 1
    atomic_actions["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    # 记录补充历史（新增字段，方便追踪）
    if "supplement_history" not in atomic_actions:
        atomic_actions["supplement_history"] = []
    atomic_actions["supplement_history"].append(supplement_info)
    return atomic_actions

def update_environment_items(environment_items: Dict[str, Any], new_item: str, subtask: str) -> Dict[str, Any]:
    """更新环境物品库，添加未匹配的新物品（去重并标记补充信息）"""
    # 检查是否已存在该物品
    for category, items in environment_items["categories"].items():
        if new_item in items:
            return environment_items  # 已存在则不重复添加
    # 新增物品（默认添加到施工材料分类，可根据需求调整）
    supplement_info = {
        "item": new_item,
        "supplement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_subtask": subtask
    }
    environment_items["categories"]["construction_materials"].append(new_item)
    environment_items["total_items"] += 1
    environment_items["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    # 记录补充历史
    if "supplement_history" not in environment_items:
        environment_items["supplement_history"] = []
    environment_items["supplement_history"].append(supplement_info)
    return environment_items

def match_atomic_action(subtask: str, atomic_actions: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """匹配原子动作，未匹配则生成新动作并更新库"""
    subtask_keywords = extract_keywords(subtask)
    # 尝试匹配现有动作
    for _, actions in atomic_actions["categories"].items():
        for action in actions:
            if len(set(subtask_keywords) & set(extract_keywords(action))) >= 1:
                return action, atomic_actions
    # 未匹配：生成新动作并更新库
    new_action = extract_potential_action(subtask)
    updated_actions = update_atomic_actions(atomic_actions, new_action, subtask)
    return new_action, updated_actions

def match_environment_item(subtask: str, environment_items: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """匹配环境物品，未匹配则生成新物品并更新库"""
    subtask_keywords = extract_keywords(subtask)
    # 尝试匹配现有物品
    for _, items in environment_items["categories"].items():
        for item in items:
            if len(set(subtask_keywords) & set(extract_keywords(item))) >= 1:
                return item, environment_items
    # 未匹配：生成新物品并更新库
    new_item = extract_potential_item(subtask)
    updated_items = update_environment_items(environment_items, new_item, subtask)
    return new_item, updated_items

def generate_action_desc(action: str, item: str, subtask: str) -> str:
    """生成动作-物品执行描述"""
    return f"执行[{action}]动作，使用[{item}]，完成子任务：{subtask}"

def build_fine_grained_decomposition():
    # 1. 加载核心文件
    decomposed_tasks = load_json_file("主代理任务分解.json")
    original_task = decomposed_tasks["original_task"]
    subtasks = decomposed_tasks["subtasks"]
    environment_items = load_json_file("construction_environment_items.json")
    atomic_actions = load_json_file("construction_atomic_actions.json")

    print(f"开始细粒度分解：原始任务「{original_task}」，共{len(subtasks)}个子任务")
    fine_grained_results = {
        "original_task": original_task,
        "main_agent_subtasks_count": len(subtasks),
        "fine_grained_tasks": [],
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "supplement_note": "本次分解中未匹配的动作/物品已自动补充至对应库中"
    }

    # 2. 逐个子任务处理（动态更新库）
    for idx, subtask in enumerate(subtasks, 1):
        print(f"处理子任务 {idx}/{len(subtasks)}: {subtask}")
        # 匹配原子动作（未匹配则自动补充）
        action, atomic_actions = match_atomic_action(subtask, atomic_actions)
        # 匹配环境物品（未匹配则自动补充）
        item, environment_items = match_environment_item(subtask, environment_items)
        # 生成描述
        desc = generate_action_desc(action, item, subtask)
        # 添加到结果
        fine_grained_results["fine_grained_tasks"].append({
            "subtask_id": idx,
            "main_agent_subtask": subtask,
            "atomic_action": action,
            "environment_item": item,
            "execution_description": desc
        })

    # 3. 保存更新后的库和分解结果
    save_json_file(atomic_actions, "construction_atomic_actions.json")
    save_json_file(environment_items, "construction_environment_items.json")
    save_json_file(fine_grained_results, "细粒度任务分解结果.json")

    print(f"分解完成！结果已保存至「细粒度任务分解结果.json」")
    print(f"原子动作库已更新，当前共{atomic_actions['total_actions']}个动作")
    print(f"环境物品库已更新，当前共{environment_items['total_items']}个物品")
    return fine_grained_results

if __name__ == "__main__":
    build_fine_grained_decomposition()