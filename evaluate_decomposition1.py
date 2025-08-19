import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from typing import Dict, List, Tuple, Any

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载任务分解相关的JSON文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"评估所需文件未找到：{file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"JSON文件格式错误：{file_path}")

def load_evaluation_model(model_path: str = "./all-MiniLM-L6-v2") -> SentenceTransformer:
    """加载预训练的Sentence Transformer模型"""
    try:
        return SentenceTransformer(model_path)
    except Exception as e:
        raise RuntimeError(f"模型加载失败，请检查模型路径是否正确：{str(e)}")

def extract_evaluation_texts(
    fine_grained_file: str, 
    main_agent_file: str
) -> Tuple[str, List[str], List[List[str]]]:
    """
    提取评估所需的文本数据（优化版）：
    - 原始任务
    - 主代理分解的子任务（中间结果）
    - 细粒度分解的步骤（按主代理子任务分组，每个子任务对应一组细步骤）
    """
    # 加载细粒度分解结果
    fine_data = load_json_file(fine_grained_file)
    original_task = fine_data["original_task"]
    
    # 加载主代理分解结果
    main_data = load_json_file(main_agent_file)
    main_subtasks = main_data["subtasks"]
    
    # 按主代理子任务分组提取细步骤（精准对应，而非平均分配）
    grouped_fine_steps = []
    for main_task in fine_data["fine_grained_tasks"]:
        # 过滤无效步骤（如"未成功分解细步骤"）
        valid_steps = [
            step["step_desc"] for step in main_task["fine_steps"] 
            if "未成功分解细步骤" not in step["step_desc"]
        ]
        grouped_fine_steps.append(valid_steps)
    
    return original_task, main_subtasks, grouped_fine_steps

def calculate_similarity_scores(
    model: SentenceTransformer,
    original_task: str,
    main_subtasks: List[str],
    grouped_fine_steps: List[List[str]]  # 按主代理子任务分组的细步骤
) -> Dict[str, Any]:
    """
    优化版相似度计算：
    1. 按主代理子任务分组计算细步骤与原始任务的相似度
    2. 精准计算每组细步骤与对应主代理子任务的相似度
    3. 调整权重为原始任务0.5 + 中间任务0.5
    """
    # 编码原始任务
    original_embedding = model.encode(original_task, convert_to_tensor=True)
    
    # 编码主代理子任务
    main_embeddings = model.encode(main_subtasks, convert_to_tensor=True)
    
    # 存储各组的相似度结果
    group_original_sims = []  # 每组细步骤与原始任务的平均相似度
    group_main_sims = []      # 每组细步骤与对应主代理子任务的平均相似度
    detailed_fine_to_original = []  # 所有细步骤与原始任务的相似度（详细）
    
    # 遍历每个主代理子任务及其对应的细步骤组
    for i, (main_subtask, fine_steps) in enumerate(zip(main_subtasks, grouped_fine_steps)):
        if not fine_steps:  # 跳过无有效步骤的组
            continue
        
        # 编码当前组的细步骤
        fine_embeddings = model.encode(fine_steps, convert_to_tensor=True)
        
        # 计算该组细步骤与原始任务的相似度（先平均组内相似度，再加入总列表）
        original_sims = util.cos_sim(fine_embeddings, original_embedding).cpu().numpy().flatten()
        group_original_avg = float(np.mean(original_sims))
        group_original_sims.append(group_original_avg)
        detailed_fine_to_original.extend([round(float(s), 4) for s in original_sims])
        
        # 计算该组细步骤与对应主代理子任务的相似度
        main_emb = main_embeddings[i]
        main_sims = util.cos_sim(fine_embeddings, main_emb).cpu().numpy().flatten()
        group_main_avg = float(np.mean(main_sims))
        group_main_sims.append(group_main_avg)
    
    # 计算整体平均相似度（过滤空组）
    avg_original_sim = float(np.mean(group_original_sims)) if group_original_sims else 0.0
    avg_main_fine_sim = float(np.mean(group_main_sims)) if group_main_sims else 0.0
    
    # 调整权重：原始任务和中间任务各占0.5（更贴近论文中对原始目标的重视）
    overall_score = 0.5 * avg_original_sim + 0.5 * avg_main_fine_sim
    
    return {
        "original_task": original_task,
        "similarity_scores": {
            "fine_to_original": round(avg_original_sim, 4),
            "fine_to_main": round(avg_main_fine_sim, 4),
            "overall_consistency": round(overall_score, 4)
        },
        "detailed_similarities": {
            "grouped_fine_to_original": [round(s, 4) for s in group_original_sims],
            "grouped_fine_to_main": [round(s, 4) for s in group_main_sims],
            "all_fine_to_original": detailed_fine_to_original
        }
    }

def save_evaluation_results(results: Dict[str, Any], output_file: str = "分解评估结果.json") -> None:
    """保存评估结果到JSON文件"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"评估结果已保存至：{output_file}")

def evaluate_task_decomposition():
    """执行任务分解评估的主函数"""
    print("===== 任务分解语义相似度评估 =====")
    
    # 1. 加载模型
    print("加载评估模型...")
    model = load_evaluation_model()
    
    # 2. 提取评估文本（按组提取细步骤）
    print("提取评估文本数据...")
    original_task, main_subtasks, grouped_fine_steps = extract_evaluation_texts(
        "细粒度任务分解结果.json",
        "主代理任务分解.json"
    )
    
    # 输出基本信息（含有效步骤统计）
    total_fine_steps = sum(len(steps) for steps in grouped_fine_steps)
    print(f"原始任务: {original_task}")
    print(f"主代理分解子任务数量: {len(main_subtasks)}")
    print(f"有效细粒度步骤总数: {total_fine_steps}")
    
    # 3. 计算相似度得分
    print("计算语义相似度...")
    evaluation_results = calculate_similarity_scores(
        model, original_task, main_subtasks, grouped_fine_steps
    )
    
    # 4. 输出评估结果
    print("\n===== 评估结果 =====")
    print(f"细粒度步骤与原始任务的平均相似度: {evaluation_results['similarity_scores']['fine_to_original']}")
    print(f"细粒度步骤与对应主代理子任务的平均相似度: {evaluation_results['similarity_scores']['fine_to_main']}")
    print(f"整体任务分解一致性得分: {evaluation_results['similarity_scores']['overall_consistency']}")
    
    # 5. 保存结果
    save_evaluation_results(evaluation_results)
    
    return evaluation_results

if __name__ == "__main__":
    evaluate_task_decomposition()