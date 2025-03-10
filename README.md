# AI-Driven Crypto Trading Bot (AI智能加密货币交易机器人)

基于大模型驱动的智能加密货币交易系统，集成市场分析、策略生成、自动交易等功能。

## 项目概述

本项目旨在构建一个智能化的加密货币交易系统，通过结合大语言模型的分析能力与传统量化交易策略，实现智能化的市场分析和交易决策。

### 核心特性

- 🤖 基于大模型的市场分析
- 📊 实时行情数据监控
- 📈 智能交易策略生成
- 🛡️ 风险控制系统
- 📱 自动化交易执行
- 📉 策略回测分析

## 系统架构

### 1. 数据采集层
- 实时行情数据获取
- 历史交易数据收集
- 市场新闻和情绪分析
- 社交媒体数据整合

### 2. 数据处理层
- 数据清洗和标准化
- 特征工程处理
- 时序数据分析
- 市场情绪指标计算

### 3. AI决策层
- 大模型市场分析
- 交易策略生成
- 风险评估系统
- 投资建议输出

### 4. 交易执行层
- 自动交易接口
- 风控模块
- 订单管理系统
- 资产管理功能

### 5. 监控反馈层
- 性能监控
- 策略回测
- 收益分析
- 风险预警

## 技术栈

- 💻 主要语言：Python 3.9+
- 🗄️ 数据库：
  - MongoDB (历史数据存储)
  - Redis (实时数据缓存)
- 🤖 AI模型：OpenAI GPT-4
- 📊 数据分析：
  - pandas
  - numpy
  - scikit-learn
- 📈 可视化：
  - Plotly
  - Dash
- 📡 监控：
  - Prometheus
  - Grafana

## 环境要求

```bash
Python >= 3.9
MongoDB >= 4.4
Redis >= 6.0
Conda
```

## 快速开始

### 1. 环境配置

1. 克隆项目
```bash
git clone https://github.com/yourusername/ai-crypto-trader.git
cd ai-crypto-trader
```

2. 配置和激活Conda环境

Windows用户：
```bash
# 运行环境配置脚本
setup_env.bat
```

Linux/Mac用户：
```bash
# 添加执行权限
chmod +x setup_env.sh
# 运行环境配置脚本
./setup_env.sh
```

或者手动配置：
```bash
# 配置conda清华源
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --set show_channel_urls yes

# 创建并激活环境
conda env create -f environment.yml
conda activate ai-crypto-trader
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥和配置信息
```

### 2. 基础配置

1. 配置数据库
```bash
# 确保MongoDB和Redis服务已启动
python scripts/init_db.py
```

2. 配置交易所API
- 在币安创建API密钥
- 将API密钥添加到配置文件

### 3. 运行系统

1. 启动数据采集服务
```bash
python services/data_collector.py
```

2. 启动交易系统
```bash
python main.py
```

## 项目结构

```
ai-crypto-trader/
├── config/                 # 配置文件
├── data/                   # 数据存储
├── docs/                   # 文档
├── models/                # AI模型
├── services/              # 核心服务
│   ├── collector/         # 数据采集
│   ├── analyzer/         # 数据分析
│   ├── trader/           # 交易执行
│   └── monitor/          # 系统监控
├── tests/                 # 测试用例
├── utils/                 # 工具函数
├── main.py               # 主程序
├── requirements.txt      # 项目依赖
└── README.md            # 项目文档
```

## 开发路线图

### 第一阶段：基础设施搭建（进行中）
- [x] 项目初始化
- [ ] 环境配置
- [ ] 数据采集系统
- [ ] 基础框架开发

### 第二阶段：AI模型集成
- [ ] 大模型接入
- [ ] 策略系统开发
- [ ] 回测系统实现

### 第三阶段：交易系统开发
- [ ] 交易接口开发
- [ ] 订单管理系统
- [ ] 资产管理功能

### 第四阶段：测试和优化
- [ ] 系统测试
- [ ] 策略优化
- [ ] 性能调优

## 风险提示

⚠️ 加密货币交易具有高风险，本项目仅供学习研究使用。在使用本系统进行实盘交易时，请注意：

1. 资金管理：合理配置资金，不要投入超过承受能力的资金
2. 风险控制：建议先使用小额资金测试系统
3. 系统风险：技术系统可能存在bug或延迟，请做好风险控制
4. 市场风险：加密货币市场波动剧烈，请谨慎操作

## 贡献指南

欢迎提交 Pull Request 或 Issue。在提交之前，请确保：

1. 代码符合PEP 8规范
2. 添加了必要的测试用例
3. 更新了相关文档

## 许可证

MIT License

## 联系方式

- 项目维护者：[Your Name]
- 邮箱：[Your Email]
- 项目地址：[GitHub Repository URL] 