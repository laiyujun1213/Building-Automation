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

## 项目结构
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









































