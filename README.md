# Building-Automation
This is the corresponding paper An adaptive task decomposition framework for complex construction projects based on large language models The fine-grained decomposition method and the code project of the main agent are presented.

# 基于大语言模型的建筑施工任务分解系统

## 📖 项目概述

本项目实现了一个分层任务分解框架，通过**主代理（Main Agent）** 和**子代理（Subagent）** 协同工作，将复杂的建筑施工任务逐步分解为具体可执行的操作步骤。

### ✨ 核心功能

- 主代理将原始任务分解为子任务
- 子代理进一步将子任务拆解为细粒度步骤
- 自动匹配原子动作与环境物品
- 动态更新动作库与物品库
- 生成规范化的任务分解结果
- 多版本评估脚本支持任务分解质量分析

## 🛠️ 环境配置

### 前置要求

- Python 3.8+
- Anaconda 或 Miniconda 环境
- 有效的 DeepSeek API 密钥（需自行申请）
- `all-MiniLM-L6-v2`预训练模型（需从官方渠道下载、或者魔塔社区下载）
- https://modelscope.cn/models/sentence-transformers/all-MiniLM-L6-v2
- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

### 模型下载与放置

1. 下载 `all-MiniLM-L6-v2` 模型文件
2. 将下载的模型解压至项目根目录，确保路径为：`./all-MiniLM-L6-v2`（评估脚本将默认从该路径加载模型）

## 克隆仓库
```
git clone https://github.com/laiyujun1213/Building-Automation.git
cd Building-Automation
```

## Conda 虚拟环境配置与依赖安装

## 创建并激活虚拟环境

### 创建Conda虚拟环境
```
conda create -n construction python=3.8 -y
```

### 激活虚拟环境
```
conda activate construction
```

### 安装依赖
```
pip install -r requirements.txt
```

## 配置 API 密钥
在运行项目前，需替换代码中的 DeepSeek API 密钥：
打开Ming_Agent.py文件，替换api_key参数值
打开subagent2.py文件，替换api_key参数值
####示例（在Ming_Agent.py和subagent2.py中）
```
deepseek_client = OpenAI(
    api_key="你的DeepSeek API密钥",  # 替换为实际密钥
    base_url="https://api.deepseek.com"
)
```

### 修改任务内容（可选）
如需分解自定义建筑任务，可修改Ming_Agent.py中的construction_task变量：
#### 在Ming_Agent.py中

```
construction_task = "你的建筑施工任务描述"  # 例如："规划建筑施工场地的临时设施布置..."
```


## 📋运行项目
### 通过主入口脚本app.py启动整个任务分解流程：
```
python3 app.py
```
首先执行Ming_Agent.py进行主任务分解，生成主代理任务分解.json
接着执行subagent2.py进行细粒度分解，生成细粒度任务分解结果.json
自动更新construction_environment_items.json（环境物品库）和construction_atomic_actions.json（原子动作库）
最后执行评估脚本（默认使用evaluate_decomposition2.py）生成分解评估结果.json

### 分模块执行项目
通过主入口脚本逻辑启动整个任务分解流程（确保已激活 Conda 环境）：
#### 首先运行主代理进行任务分解
```
python3 Ming_Agent.py
```

#### 然后运行子代理进行细粒度分解
```
python3 subagent2.py
```

#### 最后运行评估脚本（以增强版为例）
```
python3 evaluate_decomposition2.py
```



## 📁 项目结构

```
├── Ming_Agent.py                  # 主代理模块，负责初始任务分解
├── subagent2.py                   # 核心子代理模块，负责细粒度步骤分解（调用API）
├── subagent1.py                   # 辅助子模块，生成动作-物品执行描述
├── app.py                         # 项目主入口，协调各模块执行
├── evaluate_decomposition.py      # 基础版评估脚本
├── evaluate_decomposition1.py     # 优化版评估脚本
├── evaluate_decomposition2.py     # 增强版评估脚本
├── requirements.txt               # 项目依赖列表
├── construction_environment_items.json  # 环境物品库（自动更新）
├── construction_atomic_actions.json     # 原子动作库（自动更新）
├── 主代理任务分解.json              # 主代理分解结果（运行后生成）
├── 细粒度任务分解结果.json          # 细粒度分解结果（运行后生成）
├── 分解评估结果.json                # 评估结果（运行后生成）
└── all-MiniLM-L6-v2/              # 预训练模型目录（需自行下载）
```
















































