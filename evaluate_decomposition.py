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
) -> Tuple[str, List[str], List[str]]:
    """
    提取评估所需的文本数据：
    - 原始任务
    - 主代理分解的子任务（中间结果）
    - 细粒度分解的所有步骤（最终结果）
    """
    # 加载细粒度分解结果
    fine_data = load_json_file(fine_grained_file)
    original_task = fine_data["original_task"]
    
    # 加载主代理分解结果
    main_data = load_json_file(main_agent_file)
    main_subtasks = main_data["subtasks"]
    
    # 提取细粒度分解的所有步骤描述
    fine_steps = []
    for main_task in fine_data["fine_grained_tasks"]:
        for step in main_task["fine_steps"]:
            fine_steps.append(step["step_desc"])
    
    return original_task, main_subtasks, fine_steps

def calculate_similarity_scores(
    model: SentenceTransformer,
    original_task: str,
    main_subtasks: List[str],
    fine_steps: List[str]
) -> Dict[str, Any]:
    """
    计算语义相似度得分：
    1. 细粒度步骤与原始任务的平均相似度
    2. 细粒度步骤与对应主代理子任务的平均相似度
    3. 整体任务分解一致性得分（加权平均）
    """
    # 编码所有文本
    original_embedding = model.encode(original_task, convert_to_tensor=True)
    main_embeddings = model.encode(main_subtasks, convert_to_tensor=True)
    fine_embeddings = model.encode(fine_steps, convert_to_tensor=True)
    
    # 1. 计算细粒度步骤与原始任务的平均相似度
    original_similarities = util.cos_sim(fine_embeddings, original_embedding).cpu().numpy().flatten()
    avg_original_sim = float(np.mean(original_similarities))
    
    # 2. 计算细粒度步骤与对应主代理子任务的平均相似度
    # 按主代理子任务分配细步骤（假设数量对应）
    steps_per_main = len(fine_steps) // len(main_subtasks)
    main_fine_sims = []
    
    for i, main_emb in enumerate(main_embeddings):
        start_idx = i * steps_per_main
        end_idx = start_idx + steps_per_main if i < len(main_subtasks) - 1 else len(fine_steps)
        step_embeddings = fine_embeddings[start_idx:end_idx]
        
        if len(step_embeddings) > 0:
            sims = util.cos_sim(step_embeddings, main_emb).cpu().numpy().flatten()
            main_fine_sims.append(np.mean(sims))
    
    avg_main_fine_sim = float(np.mean(main_fine_sims))
    
    # 3. 计算整体一致性得分（原始任务相似度权重0.3，中间任务相似度权重0.7）
    overall_score = 0.3 * avg_original_sim + 0.7 * avg_main_fine_sim
    
    return {
        "original_task": original_task,
        "similarity_scores": {
            "fine_to_original": round(avg_original_sim, 4),  # 细步骤与原始任务相似度
            "fine_to_main": round(avg_main_fine_sim, 4),     # 细步骤与中间任务相似度
            "overall_consistency": round(overall_score, 4)   # 整体一致性得分
        },
        "detailed_similarities": {
            "fine_step_to_original": [round(float(s), 4) for s in original_similarities],
            "main_to_fine_avg": [round(float(s), 4) for s in main_fine_sims]
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
    
    # 2. 提取评估文本
    print("提取评估文本数据...")
    original_task, main_subtasks, fine_steps = extract_evaluation_texts(
        "细粒度任务分解结果.json",
        "主代理任务分解.json"
    )
    
    print(f"原始任务: {original_task}")
    print(f"主代理分解子任务数量: {len(main_subtasks)}")
    print(f"细粒度分解步骤数量: {len(fine_steps)}")
    
    # 3. 计算相似度得分
    print("计算语义相似度...")
    evaluation_results = calculate_similarity_scores(
        model, original_task, main_subtasks, fine_steps
    )
    
    # 4. 输出评估结果
    print("\n===== 评估结果 =====")
    print(f"细粒度步骤与原始任务的平均相似度: {evaluation_results['similarity_scores']['fine_to_original']}")
    print(f"细粒度步骤与中间任务的平均相似度: {evaluation_results['similarity_scores']['fine_to_main']}")
    print(f"整体任务分解一致性得分: {evaluation_results['similarity_scores']['overall_consistency']}")
    
    # 5. 保存结果
    save_evaluation_results(evaluation_results)
    
    return evaluation_results

if __name__ == "__main__":
    evaluate_task_decomposition()
