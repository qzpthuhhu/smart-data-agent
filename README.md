# 智能数据分析Agent - 项目说明

## 📋 项目概述

智能数据分析Agent是一个基于LangGraph和MiniMax大语言模型的数据分析系统，支持自然语言查询、数据分析和可视化。

## 🏗️ 项目结构

```
智能数据分析Agent/
├── agents/                    # Agent模块
│   ├── __init__.py
│   ├── query_agent.py        # Query Agent - 自然语言转SQL
│   ├── analysis_agent.py      # Analysis Agent - 数据分析
│   └── visualization_agent.py # Visualization Agent - 可视化
├── graph/                     # 工作流模块
│   ├── __init__.py
│   ├── state.py             # 状态定义
│   ├── supervisor.py        # Supervisor Agent
│   └── workflow.py           # LangGraph工作流
├── memory/                    # 记忆系统
│   ├── __init__.py
│   └── memory_manager.py
├── tools/                     # 工具模块
│   ├── __init__.py
│   ├── pandas_tools.py
│   └── plot_tools.py
├── ui/                       # Web界面模块
│   ├── __init__.py
│   ├── app.py               # Streamlit应用
│   └── logging_config.py     # 日志配置
├── tests/                    # 测试模块
│   ├── __init__.py
│   ├── test_suite.py        # 完整测试套件
│   └── reports/             # 测试报告
├── docs/                     # 文档
│   ├── DEPLOYMENT.md        # 部署文档
│   ├── USER_GUIDE.md        # 使用手册
│   └── ...
├── data/                     # 数据目录
│   └── sample.db            # 示例数据库
├── output/                   # 输出目录
│   └── charts/              # 生成的图表
├── logs/                    # 日志目录
├── config.py                # 配置模块
├── main.py                  # 主入口
├── test_minimax_api.py      # API测试工具
├── requirements.txt         # 依赖清单
├── .env                     # 环境变量
├── .env.example             # 环境变量示例
├── Dockerfile               # Docker配置
├── docker-compose.yml       # Docker Compose配置
├── deploy.sh                # 部署脚本
└── README.md                # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `.env` 文件：

```
MINIMAX_API_KEY=你的MiniMax密钥
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=MiniMax-M2.7
```

### 3. 运行应用

```bash
# Web界面
streamlit run ui/app.py

# 命令行模式
python main.py --interactive
```

### 4. 运行测试

```bash
# 基础测试
python tests/test_suite.py

# 连续10次测试
python tests/test_suite.py --count 10
```

## 📊 功能特性

### 🔍 数据查询
- 自然语言转SQL
- SQL执行和结果展示
- 数据导出（CSV/JSON）

### 📈 数据分析
- 统计分析
- 趋势分析
- 异常检测
- 对比分析

### 📊 可视化
- 折线图
- 柱状图
- 饼图
- 散点图
- 面积图
- 热力图

### 🧠 记忆系统
- 短期记忆（会话内）
- 长期记忆（向量数据库）

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MINIMAX_API_KEY | MiniMax API密钥 | - |
| MINIMAX_BASE_URL | MiniMax API地址 | https://api.minimax.chat/v1 |
| MINIMAX_MODEL | MiniMax模型 | MiniMax-M2.7 |
| DEEPSEEK_API_KEY | DeepSeek API密钥（备选） | - |

### 配置优先级

1. MiniMax API（优先）
2. DeepSeek API（备选）
3. 其他自定义API

## 📝 测试结果

### 连续10次测试汇总

- **总测试用例**: 50
- **通过**: 50 ✅
- **失败**: 0 ❌
- **通过率**: 100%
- **总耗时**: 约125秒
- **平均耗时**: 12.45秒/轮

### 测试项目

| 测试类别 | 测试内容 | 状态 |
|----------|----------|------|
| 功能测试 | API调用、NL转SQL、查询执行 | ✅ |
| 集成测试 | 工作流、完整流程 | ✅ |
| 边界测试 | 空查询、特殊字符 | ✅ |
| 性能测试 | 响应时间、并发能力 | ✅ |
| 可视化测试 | 图表生成、导出 | ✅ |

## 🐳 Docker部署

```bash
# 构建镜像
docker build -t smart-data-agent .

# 运行容器
docker-compose up -d

# 访问应用
http://localhost:8501
```

## 📚 文档

- [部署文档](docs/DEPLOYMENT.md)
- [使用手册](docs/USER_GUIDE.md)

## 🔗 相关技术

- **框架**: LangGraph, LangChain
- **数据库**: SQLite
- **可视化**: Matplotlib, Plotly
- **Web界面**: Streamlit
- **大语言模型**: MiniMax M2.7

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**版本**: v1.0.0  
**更新日期**: 2024-01-15
