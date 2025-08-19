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
- `all-MiniLM-L6-v2`预训练模型（需从官方渠道下载）

### 模型下载与放置

1. 下载 `all-MiniLM-L6-v2` 模型文件
2. 将下载的模型解压至项目根目录，确保路径为：`./all-MiniLM-L6-v2`（评估脚本将默认从该路径加载模型）

## 克隆仓库
git clone https://github.com/laiyujun1213/Building-Automation.git
cd Building-Automation

## Conda 虚拟环境配置与依赖安装

### 创建并激活虚拟环境

### 创建Conda虚拟环境
conda create -n construction-env python=3.8 -y

### 激活虚拟环境
conda activate construction-env

### 安装依赖
pip install -r requirements.txt

## 配置 API 密钥
在运行项目前，需替换代码中的 DeepSeek API 密钥：
打开Ming_Agent.py文件，替换api_key参数值
打开subagent2.py文件，替换api_key参数值
# 示例（在Ming_Agent.py和subagent2.py中）
deepseek_client = OpenAI(
    api_key="你的DeepSeek API密钥",  # 替换为实际密钥
    base_url="https://api.deepseek.com"
)













































