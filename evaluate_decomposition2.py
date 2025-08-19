import json
import numpy as np
import jieba
import jieba.analyse
from sentence_transformers import SentenceTransformer, util
from typing import Dict, List, Tuple, Any

# 配置jieba提取关键词
jieba.analyse.set_stop_words("stopwords.txt")  # 可添加中文停用词表

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

def text_preprocessing(text: str) -> str:
    """文本预处理：提取核心语义，增强关键词权重"""
    # 提取关键词并重组句子，突出核心语义
    keywords = jieba.analyse.extract_tags(text, topK=5, withWeight=False)
    if keywords:
        # 保留原始句子结构，同时将关键词前置强调
        return " ".join(keywords) + " " + text
    return text

def extract_evaluation_texts(
    fine_grained_file: str, 
    main_agent_file: str
) -> Tuple[str, List[str], List[List[str]], List[str], List[List[str]]]:
    """
    提取评估所需的文本数据（增强版）：
    - 原始任务及预处理版本
    - 主代理分解的子任务及预处理版本
    - 细粒度分解的步骤及预处理版本（按主代理子任务分组）
    """
    # 加载细粒度分解结果
    fine_data = load_json_file(fine_grained_file)
    original_task = fine_data["original_task"]
    processed_original = text_preprocessing(original_task)
    
    # 加载主代理分解结果
    main_data = load_json_file(main_agent_file)
    main_subtasks = main_data["subtasks"]
    processed_main = [text_preprocessing(task) for task in main_subtasks]
    
    # 按主代理子任务分组提取细步骤（精准对应）
    grouped_fine_steps = []
    processed_grouped_fine = []
    for main_task in fine_data["fine_grained_tasks"]:
        # 过滤无效步骤
        valid_steps = [
            step["step_desc"] for step in main_task["fine_steps"] 
            if "未成功分解细步骤" not in step["step_desc"]
        ]
        grouped_fine_steps.append(valid_steps)
        # 预处理细步骤
        processed_steps = [text_preprocessing(step) for step in valid_steps]
        processed_grouped_fine.append(processed_steps)
    
    return original_task, main_subtasks, grouped_fine_steps, processed_original, processed_main, processed_grouped_fine

def calculate_similarity_scores(
    model: SentenceTransformer,
    original_task: str,
    main_subtasks: List[str],
    grouped_fine_steps: List[List[str]],
    processed_original: str,
    processed_main: List[str],
    processed_grouped_fine: List[List[str]]
) -> Dict[str, Any]:
    """
    增强版相似度计算：
    1. 结合原始文本和预处理文本的相似度（突出关键词）
    2. 引入动态权重（步骤越长权重越高，含更多语义信息）
    3. 提升原始任务权重至0.6，更符合论文评估重点
    """
    # 编码原始任务（同时使用原始和预处理版本）
    original_embedding = model.encode(original_task, convert_to_tensor=True)
    processed_original_embedding = model.encode(processed_original, convert_to_tensor=True)
    
    # 编码主代理子任务（同时使用原始和预处理版本）
    main_embeddings = model.encode(main_subtasks, convert_to_tensor=True)
    processed_main_embeddings = model.encode(processed_main, convert_to_tensor=True)
    
    # 存储各组的相似度结果
    group_original_sims = []
    group_main_sims = []
    detailed_fine_to_original = []
    
    # 遍历每个主代理子任务及其对应的细步骤组
    for i, (main_subtask, fine_steps, processed_main_task, processed_steps) in enumerate(
        zip(main_subtasks, grouped_fine_steps, processed_main, processed_grouped_fine)
    ):
        if not fine_steps:
            continue
        
        # 为细步骤生成动态权重（长度越长权重越高，范围1.0-1.5）
        step_lengths = [len(step) for step in fine_steps]
        max_len = max(step_lengths) if step_lengths else 1
        dynamic_weights = [1.0 + 0.5 * (length / max_len) for length in step_lengths]
        
        # 编码当前组的细步骤（原始和预处理版本）
        fine_embeddings = model.encode(fine_steps, convert_to_tensor=True)
        processed_fine_embeddings = model.encode(processed_steps, convert_to_tensor=True)
        
        # 计算与原始任务的相似度（结合原始和预处理结果，加权平均）
        original_sims = util.cos_sim(fine_embeddings, original_embedding).cpu().numpy().flatten()
        processed_original_sims = util.cos_sim(processed_fine_embeddings, processed_original_embedding).cpu().numpy().flatten()
        combined_original_sims = 0.7 * original_sims + 0.3 * processed_original_sims  # 原始文本权重更高
        
        # 应用动态权重
        weighted_original_sims = combined_original_sims * dynamic_weights
        group_original_avg = float(np.mean(weighted_original_sims))
        group_original_sims.append(group_original_avg)
        detailed_fine_to_original.extend([round(float(s), 4) for s in combined_original_sims])
        
        # 计算与对应主代理子任务的相似度（结合原始和预处理结果）
        main_sims = util.cos_sim(fine_embeddings, main_embeddings[i]).cpu().numpy().flatten()
        processed_main_sims = util.cos_sim(processed_fine_embeddings, processed_main_embeddings[i]).cpu().numpy().flatten()
        combined_main_sims = 0.7 * main_sims + 0.3 * processed_main_sims
        
        # 应用动态权重
        weighted_main_sims = combined_main_sims * dynamic_weights
        group_main_avg = float(np.mean(weighted_main_sims))
        group_main_sims.append(group_main_avg)
    
    # 计算整体平均相似度
    avg_original_sim = float(np.mean(group_original_sims)) if group_original_sims else 0.0
    avg_main_fine_sim = float(np.mean(group_main_sims)) if group_main_sims else 0.0
    
    # 调整权重：更重视与原始任务的一致性（0.6）
    overall_score = 0.6 * avg_original_sim + 0.4 * avg_main_fine_sim
    
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
    print("===== 增强版任务分解语义相似度评估 =====")
    
    # 1. 加载模型
    print("加载评估模型...")
    model = load_evaluation_model()
    
    # 2. 提取评估文本（含预处理版本）
    print("提取并预处理评估文本数据...")
    original_task, main_subtasks, grouped_fine_steps, processed_original, processed_main, processed_grouped_fine = extract_evaluation_texts(
        "细粒度任务分解结果.json",
        "主代理任务分解.json"
    )
    
    # 输出基本信息
    total_fine_steps = sum(len(steps) for steps in grouped_fine_steps)
    print(f"原始任务: {original_task}")
    print(f"主代理分解子任务数量: {len(main_subtasks)}")
    print(f"有效细粒度步骤总数: {total_fine_steps}")
    
    # 3. 计算相似度得分
    print("计算增强版语义相似度...")
    evaluation_results = calculate_similarity_scores(
        model, original_task, main_subtasks, grouped_fine_steps,
        processed_original, processed_main, processed_grouped_fine
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
    