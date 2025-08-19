import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from openai import OpenAI  # 引入OpenAI客户端（用于调用DeepSeek API）

# 初始化DeepSeek客户端（使用你的API Key）
deepseek_client = OpenAI(
    api_key="",
    base_url="https://api.deepseek.com"
)

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
    stopwords = ["的", "了", "进行", "完成", "处理", "使用", "操作", "对", "在", "为"]
    return [word for word in text.lower().split() if len(word) > 1 and word not in stopwords]

def call_deepseek_for_fine_steps(subtask: str) -> List[str]:
    """调用DeepSeek API将子任务分解为更细的执行步骤（论文中的子代理分解逻辑）"""
    prompt = f"""
    请将以下建筑施工子任务分解为3-5个具体可执行的细步骤，每个步骤用简洁的自然语言描述，需体现动作和可能涉及的物品：
    子任务：{subtask}
    输出格式：以编号列表形式返回，例如：
    1. 步骤1描述（含动作和物品）
    2. 步骤2描述（含动作和物品）
    ...
    """
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是建筑施工细步骤分解专家，擅长将子任务拆分为具体可执行的原子级步骤。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4  # 控制输出稳定性
        )
        # 提取并解析细步骤（按编号列表格式处理）
        fine_steps_text = response.choices[0].message.content
        fine_steps = re.findall(r'\d+\. (.*?)(?=\n\d+\. |$)', fine_steps_text, re.DOTALL)
        return [step.strip() for step in fine_steps if step.strip()]
    except Exception as e:
        print(f"DeepSeek API调用失败：{str(e)}")
        return [f"未成功分解细步骤：{subtask}"]  # 失败时返回原始子任务

def extract_potential_action(step: str) -> str:
    """从细步骤中提取潜在原子动作（优先动词）"""
    action_verbs = ["勘察", "测量", "搬运", "安装", "调试", "检查", "清理", "准备", "布置", "连接", "拆卸", "操作", "划定", "标记", "记录"]
    keywords = extract_keywords(step)
    for verb in action_verbs:
        if verb in keywords:
            return verb
    return keywords[0] if keywords else f"未识别动作_{datetime.now().strftime('%H%M%S')}"

def extract_potential_item(step: str) -> str:
    """从细步骤中提取潜在环境物品（优先名词）"""
    item_nouns = ["场地", "设备", "工具", "材料", "仪器", "图纸", "零件", "配件", "区域", "设施", "卷尺", " marker笔", "全站仪", "防护栏"]
    keywords = extract_keywords(step)
    for noun in item_nouns:
        if noun in keywords:
            return noun
    return keywords[0] if keywords else f"未识别物品_{datetime.now().strftime('%H%M%S')}"

def update_atomic_actions(atomic_actions: Dict[str, Any], new_action: str, step: str) -> Dict[str, Any]:
    """更新原子动作库，添加未匹配的新动作（去重并标记补充信息）"""
    for category, actions in atomic_actions["categories"].items():
        if new_action in actions:
            return atomic_actions
    supplement_info = {
        "action": new_action,
        "supplement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_step": step
    }
    atomic_actions["categories"]["basic_operations"].append(new_action)
    atomic_actions["total_actions"] += 1
    atomic_actions["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    if "supplement_history" not in atomic_actions:
        atomic_actions["supplement_history"] = []
    atomic_actions["supplement_history"].append(supplement_info)
    return atomic_actions

def update_environment_items(environment_items: Dict[str, Any], new_item: str, step: str) -> Dict[str, Any]:
    """更新环境物品库，添加未匹配的新物品（去重并标记补充信息）"""
    for category, items in environment_items["categories"].items():
        if new_item in items:
            return environment_items
    supplement_info = {
        "item": new_item,
        "supplement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_step": step
    }
    environment_items["categories"]["construction_materials"].append(new_item)
    environment_items["total_items"] += 1
    environment_items["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    if "supplement_history" not in environment_items:
        environment_items["supplement_history"] = []
    environment_items["supplement_history"].append(supplement_info)
    return environment_items

def match_atomic_action(step: str, atomic_actions: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """匹配原子动作，未匹配则生成新动作并更新库"""
    step_keywords = extract_keywords(step)
    for _, actions in atomic_actions["categories"].items():
        for action in actions:
            if len(set(step_keywords) & set(extract_keywords(action))) >= 1:
                return action, atomic_actions
    new_action = extract_potential_action(step)
    updated_actions = update_atomic_actions(atomic_actions, new_action, step)
    return new_action, updated_actions

def match_environment_item(step: str, environment_items: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """匹配环境物品，未匹配则生成新物品并更新库"""
    step_keywords = extract_keywords(step)
    for _, items in environment_items["categories"].items():
        for item in items:
            if len(set(step_keywords) & set(extract_keywords(item))) >= 1:
                return item, environment_items
    new_item = extract_potential_item(step)
    updated_items = update_environment_items(environment_items, new_item, step)
    return new_item, updated_items

def generate_action_desc(action: str, item: str, step: str) -> str:
    """生成动作-物品执行描述"""
    return f"执行[{action}]动作，使用[{item}]，完成细步骤：{step}"

def build_fine_grained_decomposition():
    # 1. 加载核心文件
    decomposed_tasks = load_json_file("主代理任务分解.json")
    original_task = decomposed_tasks["original_task"]
    main_subtasks = decomposed_tasks["subtasks"]  # 主代理分解的子任务
    environment_items = load_json_file("construction_environment_items.json")
    atomic_actions = load_json_file("construction_atomic_actions.json")

    print(f"开始细粒度分解：原始任务「{original_task}」，共{len(main_subtasks)}个主代理子任务")
    fine_grained_results = {
        "original_task": original_task,
        "main_agent_subtasks_count": len(main_subtasks),
        "fine_grained_tasks": [],  # 存储每个主代理子任务的细步骤分解结果
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "supplement_note": "本次分解中未匹配的动作/物品已自动补充至对应库中"
    }

    # 2. 处理每个主代理子任务：调用DeepSeek生成细步骤，再关联动作和物品
    for main_idx, main_subtask in enumerate(main_subtasks, 1):
        print(f"\n处理主代理子任务 {main_idx}/{len(main_subtasks)}: {main_subtask}")
        
        # 2.1 调用DeepSeek生成细步骤（论文中的子代理动态分解）
        fine_steps = call_deepseek_for_fine_steps(main_subtask)
        print(f"  DeepSeek生成细步骤数量：{len(fine_steps)}")

        # 2.2 处理每个细步骤，关联原子动作和环境物品
        main_subtask_results = {
            "main_subtask_id": main_idx,
            "main_subtask_desc": main_subtask,
            "fine_steps_count": len(fine_steps),
            "fine_steps": []
        }

        for step_idx, step in enumerate(fine_steps, 1):
            print(f"  处理细步骤 {step_idx}/{len(fine_steps)}: {step}")
            # 匹配原子动作（未匹配则自动补充）
            action, atomic_actions = match_atomic_action(step, atomic_actions)
            # 匹配环境物品（未匹配则自动补充）
            item, environment_items = match_environment_item(step, environment_items)
            # 生成描述
            desc = generate_action_desc(action, item, step)
            # 添加到结果
            main_subtask_results["fine_steps"].append({
                "step_id": step_idx,
                "step_desc": step,
                "atomic_action": action,
                "environment_item": item,
                "execution_description": desc
            })

        # 将当前主代理子任务的细步骤结果加入总结果
        fine_grained_results["fine_grained_tasks"].append(main_subtask_results)

    # 3. 保存更新后的库和分解结果
    save_json_file(atomic_actions, "construction_atomic_actions.json")
    save_json_file(environment_items, "construction_environment_items.json")
    save_json_file(fine_grained_results, "细粒度任务分解结果.json")

    print(f"\n分解完成！结果已保存至「细粒度任务分解结果.json」")
    print(f"原子动作库已更新，当前共{atomic_actions['total_actions']}个动作")
    print(f"环境物品库已更新，当前共{environment_items['total_items']}个物品")
    return fine_grained_results

if __name__ == "__main__":
    build_fine_grained_decomposition()