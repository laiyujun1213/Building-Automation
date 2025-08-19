基于大语言模型的建筑施工任务分解系统，可将笼统的施工任务自动拆解为可执行的细粒度步骤，并关联原子动作与环境物品。

项目概述
本项目实现了一个分层任务分解框架，通过主代理（Main Agent）和子代理（Subagent）协同工作，将复杂的建筑施工任务逐步分解为具体可执行的操作步骤。核心功能包括：
主代理将原始任务分解为子任务
子代理进一步将子任务拆解为细粒度步骤
自动匹配原子动作与环境物品
动态更新动作库与物品库
生成规范化的任务分解结果
多版本评估脚本支持任务分解质量分析

环境配置
前置要求
Python 3.8+
Anaconda 或 Miniconda 环境
有效的 DeepSeek API 密钥（需自行申请）
all-MiniLM-L6-v2预训练模型（需从官方渠道下载）


模型下载与放置
下载all-MiniLM-L6-v2模型文件
将下载的模型解压至项目根目录，确保路径为：./all-MiniLM-L6-v2（评估脚本将默认从该路径加载模型）

Conda 虚拟环境配置与依赖安装
创建并激活虚拟环境
# 克隆仓库（若使用版本控制）
git clone <仓库地址>
cd <仓库目录>

# 创建Conda虚拟环境
conda create -n construction-env python=3.8 -y

# 激活虚拟环境
conda activate construction-env


安装项目依赖
# 通过requirements.txt安装所有依赖
pip install -r requirements.txt

# 注意：若存在PyTorch相关安装问题，可根据CUDA版本单独安装
# 例如CUDA 11.8版本：
# pip install torch==2.5.1+cu118 torchaudio==2.5.1+cu118 torchvision==0.20.1+cu118 -f https://download.pytorch.org/whl/cu118/torch_stable.html



使用指南
1. 配置 API 密钥
在运行项目前，需替换代码中的 DeepSeek API 密钥：
打开Ming_Agent.py文件，替换api_key参数值
# 示例（在Ming_Agent.py中）
deepseek_client = OpenAI(
    api_key="你的DeepSeek API密钥",  # 替换为实际密钥
    base_url="https://api.deepseek.com"
)

2. 修改任务内容（可选）
如需分解自定义建筑任务，可修改Ming_Agent.py中的construction_task变量：
# 在Ming_Agent.py中
construction_task = "你的建筑施工任务描述"  # 例如："将水泥搬运到搅拌机旁边，并且开始粉刷围墙。"

3. 运行项目
通过主入口脚本逻辑启动整个任务分解流程（确保已激活 Conda 环境）：
# 首先运行主代理进行任务分解
python Ming_Agent.py

# 然后运行子代理进行细粒度分解
python subagent2.py

# 最后运行评估脚本（以增强版为例）
python evaluate_decomposition2.py

# 或者直接执行app.py：
python app.py

运行流程说明：
执行Ming_Agent.py进行主任务分解，生成主代理任务分解.json
执行subagent2.py进行细粒度分解，生成细粒度任务分解结果.json
自动更新construction_environment_items.json（环境物品库）和construction_atomic_actions.json（原子动作库）
执行评估脚本生成分解评估结果.json

4. 评估脚本说明
项目提供多版本的评估脚本，用于分析任务分解质量：
evaluate_decomposition.py：基础版，计算细粒度步骤与原始任务、主代理子任务的语义相似度
evaluate_decomposition1.py：优化版，按主代理子任务分组计算相似度，提升匹配精度
evaluate_decomposition2.py：增强版，结合文本预处理（提取核心语义，增强关键词权重）和动态权重，更贴近实际业务场景


项目结构

├── Ming_Agent.py                  # 主代理模块，负责初始任务分解
├── Subagent.py                    # 原子动作-物品描述生成模块
├── subagent1.py                   # 基础版子代理，生成动作-物品关联
├── subagent2.py                   # 增强版子代理，调用API生成细步骤
├── app.py                         # 脚本运行工具函数
├── evaluate_decomposition.py      # 基础版评估脚本
├── evaluate_decomposition1.py     # 优化版评估脚本
├── evaluate_decomposition2.py     # 增强版评估脚本（含文本预处理）
├── requirements.txt               # 项目依赖列表
├── construction_environment_items.json  # 环境物品库（自动更新）
├── construction_atomic_actions.json     # 原子动作库（自动更新）
├── 主代理任务分解.json              # 主代理分解结果（运行后生成）
├── 细粒度任务分解结果.json          # 细粒度分解结果（运行后生成）
├── 分解评估结果.json                # 评估结果（运行后生成）
└── all-MiniLM-L6-v2/              # 预训练模型目录（需自行下载）
