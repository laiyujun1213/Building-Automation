import json
import re
from typing import List, Dict, Any

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件（含主代理任务分解结果、环境物品库、原子动作库）"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"关键文件未找到，请确认路径：{file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"文件格式错误，无法解析：{file_path}")

def extract_keywords(text: str) -> List[str]:
    """提取文本关键词，用于匹配原子动作和环境物品"""
    text = re.sub(r'[^\w\s]', '', text)  # 移除标点符号
    return [word for word in text.lower().split() if len(word) > 1]  # 过滤短词

def match_atomic_action(subtask: str, atomic_actions: Dict[str, Any]) -> str:
    """根据子任务描述匹配原子动作库中的最小动作单元（参考文档原子任务定义）"""
    subtask_keywords = extract_keywords(subtask)
    # 遍历原子动作库所有分类，优先匹配语义相关度最高的动作
    for _, actions in atomic_actions["categories"].items():
        for action in actions:
            action_keywords = extract_keywords(action)
            if len(set(subtask_keywords) & set(action_keywords)) >= 1:
                return action
    return "未匹配原子动作（需补充至原子动作库）"

def match_environment_item(subtask: str, environment_items: Dict[str, Any]) -> str:
    """根据子任务描述匹配环境物品库中的现场资源（参考文档环境物品约束）"""
    subtask_keywords = extract_keywords(subtask)
    # 遍历环境物品库所有分类，匹配相关物品
    for _, items in environment_items["categories"].items():
        for item in items:
            item_keywords = extract_keywords(item)
            if len(set(subtask_keywords) & set(item_keywords)) >= 1:
                return item
    return "未匹配环境物品（需补充至环境物品库）"

def generate_action_desc(action: str, item: str, subtask: str) -> str:
    """生成原子动作-物品的使用描述，明确执行逻辑（参考文档可执行原子任务要求）"""
    if "未匹配" in action or "未匹配" in item:
        return f"子任务：{subtask}（提示：需补充对应原子动作或环境物品）"
    return f"执行[{action}]动作，使用[{item}]，完成子任务：{subtask}"

def build_fine_grained_decomposition():
    # 1. 核心输入：读取主代理分解的子任务结果（必须先完成主代理分解）
    print("正在读取主代理任务分解结果...")
    decomposed_tasks = load_json_file("主代理任务分解.json")  # 主代理分解的子任务输入
    original_task = decomposed_tasks["original_task"]
    subtasks = decomposed_tasks["subtasks"]
    print(f"成功读取主代理分解结果：原始任务为「{original_task}」，共分解出{len(subtasks)}个子任务")

    # 2. 加载环境物品库和原子动作库（作为分解约束与依据）
    environment_items = load_json_file("construction_environment_items.json")  # 环境资源约束
    atomic_actions = load_json_file("construction_atomic_actions.json")        # 原子动作单元

    # 3. 对每个子任务进行细粒度分解：关联原子动作、物品及描述
    fine_grained_results = {
        "original_task": original_task,
        "main_agent_subtasks_count": len(subtasks),  # 主代理分解的子任务数量
        "fine_grained_tasks": [],                    # 细粒度分解结果
        "last_updated": "2025-08-07"
    }

    for idx, subtask in enumerate(subtasks, 1):
        print(f"正在处理子任务 {idx}/{len(subtasks)}: {subtask}")
        action = match_atomic_action(subtask, atomic_actions)
        item = match_environment_item(subtask, environment_items)
        desc = generate_action_desc(action, item, subtask)
        
        fine_grained_results["fine_grained_tasks"].append({
            "subtask_id": idx,
            "main_agent_subtask": subtask,  # 主代理分解的子任务原文
            "atomic_action": action,        # 匹配的原子动作
            "environment_item": item,       # 匹配的环境物品
            "execution_description": desc   # 动作-物品使用描述
        })

    # 4. 保存细粒度分解结果
    with open("细粒度任务分解结果.json", "w", encoding="utf-8") as f:
        json.dump(fine_grained_results, f, ensure_ascii=False, indent=2)
    
    print(f"细粒度分解完成，结果已保存至「细粒度任务分解结果.json」，共生成{len(fine_grained_results['fine_grained_tasks'])}条细粒度任务")
    return fine_grained_results

if __name__ == "__main__":
    build_fine_grained_decomposition()