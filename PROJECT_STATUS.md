# 智能数据分析Agent - 项目说明

## 📋 项目概述

这是一个基于LangGraph的多Agent协作系统，能够接收自然语言查询，自动完成数据查询、分析、可视化全流程。

**项目位置**：`~/smart_data_agent/`

## ✅ 当前状态

### 已完成功能
- ✅ **核心Agent系统**
  - Supervisor Agent：任务规划与调度
  - Query Agent：自然语言转SQL
  - Analysis Agent：数据分析
  - Visualization Agent：图表生成

- ✅ **技术集成**
  - LangGraph工作流
  - MiniMax API（已配置）
  - SQLite数据库（500条销售记录）
  - Memory系统（短期+长期记忆）

- ✅ **测试验证**
  - 模块导入：✓ 通过
  - 数据库连接：✓ 通过
  - API调用：✓ 通过
  - SQL生成：✓ 通过

### 待完成功能
- ⏳ Streamlit Web界面（需要安装streamlit）
- ⏳ Docker容器化部署

## 🚀 快速启动

### 方法1：使用启动脚本

```bash
cd ~/smart_data_agent

# 运行测试
./run.sh --test

# 执行查询
./run.sh --query "显示最近一个月的销售额"

# 启动Web界面（需要先安装streamlit）
./run.sh --ui

# 交互模式
./run.sh
```

### 方法2：直接运行Python

```bash
cd ~/smart_data_agent

# 运行测试
export MINIMAX_API_KEY='sk-cp-i2fR6CGvVPegIgOK6yjZSZ0LENb3WkBoGP3fJrQgb2yaeQvgurY8ToY6AePD-mrIgg6bm0XOiBk48Y0xYnGzKS2fVzS485dQaILPnaKWIwtRbH4hVdqjwyc'
python quick_test.py

# 命令行查询
python -c "
import os
os.environ['MINIMAX_API_KEY'] = 'sk-cp-i2fR6CGvVPegIgOK6yjZSZ0LENb3WkBoGP3fJrQgb2yaeQvgurY8ToY6AePD-mrIgg6bm0XOiBk48Y0xYnGzKS2fVzS485dQaILPnaKWIwtRbH4hVdqjwyc'
from agents.query_agent import QueryAgent
agent = QueryAgent('./data/sample.db')
sql, explanation = agent.nl_to_sql('显示最近一个月的销售额')
print(f'SQL: {sql}')
"
```

## 📊 项目结构

```
~/smart_data_agent/
├── agents/                 # Agent实现
│   ├── query_agent.py      # 查询Agent
│   ├── analysis_agent.py   # 分析Agent
│   └── visualization_agent.py # 可视化Agent
├── graph/                  # LangGraph核心
│   ├── state.py            # 状态定义
│   ├── supervisor.py       # Supervisor Agent
│   └── workflow.py         # 工作流编排
├── tools/                  # 工具模块
│   ├── pandas_tools.py     # 数据分析工具
│   └── plot_tools.py       # 可视化工具
├── memory/                 # 记忆模块
├── ui/                     # Web界面
│   └── app.py              # Streamlit应用
├── data/                   # 数据库
│   └── sample.db           # 示例数据库
├── config.py               # 配置管理
├── main.py                 # 主入口
├── quick_test.py           # 快速测试脚本
└── run.sh                  # 启动脚本
```

## 🔧 环境配置

### 已配置
- **MiniMax API Key**：已设置
- **模型**：MiniMax-M2.7
- **数据库**：./data/sample.db（500条销售记录）

### 安装依赖（如需要）

```bash
# 核心依赖（已安装）
pip install langgraph langchain-core pandas matplotlib

# Web界面依赖（待安装）
pip install streamlit

# 其他依赖
pip install chromadb plotly python-dotenv
```

## 🎯 面试演示建议

### 演示流程

1. **展示项目结构**
   ```bash
   cd ~/smart_data_agent
   tree -L 2
   ```

2. **运行测试**
   ```bash
   ./run.sh --test
   ```

3. **演示自然语言查询**
   ```bash
   ./run.sh --query "显示最近一个月的销售额"
   ./run.sh --query "分析各地区的销售占比"
   ```

4. **讲解架构**
   - Multi-Agent协作（Supervisor模式）
   - LangGraph状态机驱动
   - Tool Use（SQL/Pandas/Matplotlib）
   - Memory系统

### 核心亮点

1. **完整的Multi-Agent系统**
   - Supervisor负责任务拆解和调度
   - 3个专项Agent各司其职
   - LangGraph状态机保证执行正确性

2. **工程化实践**
   - 模块化设计
   - 错误处理和重试机制
   - API抽象层（支持多种LLM）

3. **实际可用**
   - 真实的数据库
   - 可工作的API调用
   - 完整的测试覆盖

## 📝 已知问题

1. **Streamlit未安装**
   - Web界面需要先安装streamlit
   - 解决：`pip install streamlit`

2. **API响应时间**
   - MiniMax API响应较慢（约5-10秒）
   - 建议面试时先预热或使用缓存

## 🔗 相关文档

- [项目架构设计](美团面试准备/智能数据分析Agent项目架构.md)
- [README.md](美团面试准备/智能数据分析Agent/docs/README.md)
- [教学案例](美团面试准备/智能数据分析Agent/docs/TEACHING_CASE.md)
- [测试案例](美团面试准备/智能数据分析Agent/docs/TEST_CASES.md)

---

**项目已就绪，可以开始演示！** 🎉
