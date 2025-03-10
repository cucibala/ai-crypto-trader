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
- 🤖 AI模型：DeepSeek-V3
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

### 第一阶段：基础设施搭建 ✅
- [x] 项目初始化和目录结构创建
- [x] 环境配置（conda环境、依赖管理）
- [x] 配置管理模块（settings.py）
- [x] 环境变量模板（.env.example）
- [x] 环境配置脚本（setup_env.bat/sh）

### 第二阶段：AI模型集成（进行中）
- [x] 大模型配置和接入
- [x] 基础策略系统（SimpleMAStrategy）
- [x] 市场情绪分析模块
  - [x] 新闻数据采集
  - [x] 情绪分析处理
  - [x] 代理配置支持
- [x] 回测系统实现
  - [x] 回测引擎（Backtester）
  - [x] 数据获取模块（DataFetcher）
  - [x] 回测运行器（BacktestRunner）
  - [x] 参数优化功能
- [ ] 社交媒体数据分析

### 第三阶段：交易系统开发（待开始）
- [ ] 交易接口开发
- [ ] 订单管理系统
- [ ] 资产管理功能
- [ ] 风险控制模块

### 第四阶段：测试和优化（待开始）
- [ ] 系统测试
- [ ] 策略优化
- [ ] 性能调优
- [ ] 监控系统集成

### 已完成的核心功能
1. 配置管理
   - 环境变量管理
   - API密钥配置
   - 代理设置
   - 模型参数配置

2. AI模型集成
   - OpenAI API集成
   - 备选模型支持（Anthropic、Google AI）
   - 情绪分析模型

3. 策略系统
   - 移动平均线策略
   - RSI过滤器
   - 参数优化

4. 数据分析
   - 新闻数据采集
   - 情绪分析
   - 数据持久化

5. 回测系统
   - 历史数据管理
   - 交易模拟
   - 性能评估
   - 参数优化
   - 结果可视化

## 使用指南

### 回测系统使用

1. 运行简单回测
```bash
python scripts/test_backtest.py
```

2. 回测参数说明
- `symbol`: 交易对（默认 BTCUSDT）
- `timeframe`: 时间周期（支持 1m/3m/5m/15m/30m/1h/2h/4h/6h/8h/12h/1d/3d/1w/1M）
- `initial_capital`: 初始资金
- `commission_rate`: 手续费率

3. 回测结果指标
- 总收益率
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
- 交易次数
- 平均收益

4. 参数优化
- 支持多参数网格搜索
- 基于夏普比率优化
- 自动保存优化结果

5. 数据管理
- 自动缓存历史数据
- 支持在线获取数据
- 数据格式标准化

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

- 项目维护者：[cucibala]
- 邮箱：[cucibala@gmail.com]
- 项目地址：[https://github.com/cucibala/ai-crypto-trader]

# 币安 WebSocket API 测试工具

这个项目提供了一个用于测试币安 WebSocket API 的工具，支持测试行情数据和账户信息。

## 功能特点

### 1. 行情数据测试
- 获取实时价格信息
- 查询24小时价格统计
- 获取最新K线数据

### 2. 账户信息测试
- 获取账户状态和权限
- 查看账户佣金费率
- 显示账户资产余额

## 环境要求

- Python 3.7+
- aiohttp
- 币安 API 密钥（可选，仅账户测试需要）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

1. 创建 `.env` 文件并配置以下参数：

```env
# API配置（可选，仅账户测试需要）
BINANCE_API_KEY=你的API密钥
BINANCE_API_SECRET=你的API密钥密文

# 代理设置（可选）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

2. 或者在 `config/settings.py` 中配置：

```python
BINANCE_API_KEY = "你的API密钥"
BINANCE_API_SECRET = "你的API密钥密文"
```

## 使用方法

### 运行测试脚本

```bash
python scripts/test_binance_ws_api.py
```

### 测试输出示例

```
开始测试市场数据...
1. 获取交易对价格...
BTCUSDT当前价格: 42156.78

2. 获取24小时价格统计...
BTCUSDT 24小时统计:
最高价: 42500.00
最低价: 41800.00
成交量: 1234.5678
涨跌幅: 2.5%

3. 获取最新K线数据...
BTCUSDT 最新1分钟K线:
开盘价: 42156.78
最高价: 42160.00
最低价: 42155.55
收盘价: 42157.89
成交量: 12.3456

开始测试账户数据...
账户权限: ['SPOT']

账户佣金费率:
Maker费率: 0.001
Taker费率: 0.001

账户余额:
BTC: 可用=1.23456789, 冻结=0.00000000
USDT: 可用=1000.00, 冻结=0.00

测试完成 ✅
```

## 错误处理

1. API密钥未配置
```
警告: API密钥未配置，跳过账户数据测试
```

2. 网络连接错误
```
错误: WebSocket连接失败: [错误详情]
```

3. API请求错误
```
错误: 市场数据测试失败: [错误详情]
错误: 账户数据测试失败: [错误详情]
```

## 注意事项

1. 账户测试需要有效的 API 密钥
2. API 密钥需要有读取权限
3. 建议在测试网络环境下先进行测试
4. 如果使用代理，确保代理服务器正常运行

## 开发说明

### 项目结构
```
├── config/
│   └── settings.py         # 配置文件
├── scripts/
│   └── test_binance_ws_api.py  # 测试脚本
├── utils/
│   └── binance_client.py   # WebSocket客户端
└── README.md               # 说明文档
```

### 添加新的测试
1. 在 `test_binance_ws_api.py` 中添加新的测试函数
2. 在 `main()` 函数中调用新的测试函数
3. 更新相关文档

## 参考文档

- [币安 WebSocket API 文档](https://developers.binance.com/docs/zh-CN/binance-spot-api-docs/web-socket-api)
- [币安 API 错误代码](https://developers.binance.com/docs/zh-CN/binance-spot-api-docs/errors)

## 更新日志

### v1.0.0 (2024-03-10)
- 实现基本的行情数据测试
- 实现账户信息测试
- 添加详细的使用文档 