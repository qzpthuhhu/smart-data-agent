# 智能数据分析Agent系统 - 教学案例

## 📚 目录

1. [项目背景与目标](#项目背景与目标)
2. [架构设计思路](#架构设计思路)
3. [核心代码讲解](#核心代码讲解)
4. [使用示例](#使用示例)
5. [扩展方向](#扩展方向)

---

## 1. 项目背景与目标

### 1.1 业务场景

在企业的日常运营中，数据分析是决策的重要依据。然而，传统的数据分析方式存在以下痛点：

- **技术门槛高**：需要编写SQL或Python代码
- **流程繁琐**：查询→分析→可视化需要多工具配合
- **效率低下**：无法快速响应业务需求变化

### 1.2 项目目标

本项目旨在构建一个**智能数据分析Agent系统**，让用户通过自然语言即可完成数据分析全流程：

```
用户: "分析最近三个月的销售趋势" 
系统: 
  1. 理解查询意图 → 查询+分析
  2. 转换为SQL → SELECT * FROM sales WHERE ...
  3. 执行查询 → 获取数据
  4. 分析数据 → 趋势检测、统计分析
  5. 生成图表 → 可视化展示
  6. 整合响应 → 友好的自然语言回复
```

### 1.3 技术选型

| 组件 | 技术选型 | 选型理由 |
|------|----------|----------|
| Agent框架 | LangGraph | 状态机驱动，适合复杂工作流 |
| LLM | DeepSeek-V3 | 成本低，效果好 |
| 向量库 | Chroma | 轻量级，易集成 |
| 可视化 | Matplotlib | 功能丰富，稳定可靠 |
| 数据处理 | Pandas + SQLite | 轻量级，易部署 |

---

## 2. 架构设计思路

### 2.1 Multi-Agent协作模式

系统采用**Supervisor-Worker模式**：

```
                    ┌─────────────┐
                    │ Supervisor │
                    │   Agent    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │   Query    │  │  Analysis  │  │ Visualization│
    │   Agent    │  │   Agent    │  │    Agent     │
    └─────────────┘  └─────────────┘  └─────────────┘
```

**各Agent职责**：
- **Supervisor**：任务规划、意图识别、结果整合
- **Query Agent**：自然语言转SQL、执行查询
- **Analysis Agent**：统计分析、趋势检测、异常发现
- **Visualization Agent**：图表生成、样式定制

### 2.2 状态机驱动的工作流

使用LangGraph的状态机来管理Agent协作：

```python
# 定义状态
class AgentState(TypedDict):
    user_query: str           # 用户查询
    task_type: TaskType        # 任务类型
    tasks: List[Task]          # 子任务列表
    query_result: QueryResult  # 查询结果
    analysis_result: AnalysisResult  # 分析结果
    # ...更多字段
```

**工作流节点**：
1. **supervisor** → 意图识别 + 任务规划
2. **query_agent** → NL转SQL + 执行查询
3. **analysis_agent** → 数据分析
4. **visualization_agent** → 生成图表
5. **integrate** → 结果整合

**条件路由**：
```python
def route_agent(state):
    if state["next_agent"] == "query":
        return "query_agent"
    elif state["next_agent"] == "analysis":
        return "analysis_agent"
    # ...
```

### 2.3 记忆系统设计

系统采用双层记忆架构：

```
┌─────────────────────────────────────────┐
│              用户对话                   │
├─────────────────────────────────────────┤
│  短期记忆 (Short-term Memory)           │
│  - 对话历史 (最近N轮)                   │
│  - 当前会话上下文                       │
├─────────────────────────────────────────┤
│  长期记忆 (Long-term Memory)           │
│  - Chroma向量库存储                     │
│  - 语义相似度检索                       │
│  - 用户偏好学习                         │
└─────────────────────────────────────────┘
```

---

## 3. 核心代码讲解

### 3.1 状态定义 (graph/state.py)

状态是整个系统的核心数据结构：

```python
class AgentState(TypedDict):
    """
    LangGraph Agent状态定义
    这是整个系统的核心数据结构，在各Agent之间传递
    """
    # === 对话上下文 ===
    user_query: str           # 用户原始查询
    session_id: str           # 会话ID
    turn: int                 # 当前轮次
    
    # === 意图识别 ===
    task_type: TaskType       # 识别的任务类型
    intent: IntentType        # 具体意图
    
    # === 任务规划 ===
    tasks: List[Task]         # 拆解的子任务列表
    
    # === 查询相关 ===
    query_result: QueryResult  # Query Agent的结果
    
    # === 分析相关 ===
    analysis_result: AnalysisResult  # Analysis Agent的结果
    
    # === 可视化相关 ===
    visualization_result: VisualizationResult  # Viz Agent的结果
    
    # === 整合结果 ===
    final_response: str       # 最终整合的响应
    
    # === 控制流 ===
    next_agent: AgentName     # 下一个要调用的Agent
    should_continue: bool     # 是否继续执行
```

**设计要点**：
1. 使用TypedDict确保类型安全
2. 每个Agent负责更新自己相关字段
3. next_agent字段控制路由

### 3.2 Supervisor Agent (graph/supervisor.py)

Supervisor是系统的核心协调者：

```python
class SupervisorAgent:
    def recognize_intent(self, query: str) -> Dict[str, Any]:
        """
        意图识别
        使用LLM分析用户查询，判断意图类型
        """
        # 构建提示词
        prompt = SUPERVISOR_TASK_PROMPT.format(query=query)
        
        # 调用LLM
        response = create_llm_call(
            system_prompt=self.system_prompt,
            user_prompt=prompt
        )
        
        # 解析JSON结果
        return self._parse_json_response(response)
    
    def plan_tasks(self, query: str, intent_result: Dict) -> List[Task]:
        """
        任务规划
        根据意图拆解为可执行的子任务
        """
        # 从意图识别结果获取任务
        tasks_data = intent_result.get("tasks", [])
        
        # 转换为Task对象
        tasks = [
            Task(
                task_id=t["task_id"],
                task_type=TaskType(t["task_type"]),
                description=t["description"]
            )
            for t in tasks_data
        ]
        
        return tasks
```

**Supervisor节点函数**：
```python
def supervisor_node(state: AgentState) -> AgentState:
    """LangGraph节点函数"""
    # 1. 意图识别
    intent_result = supervisor_agent.recognize_intent(state["user_query"])
    
    # 2. 更新状态
    state["intent"] = IntentType(intent_result["intent"])
    state["task_type"] = TaskType(intent_result["task_type"])
    
    # 3. 任务规划
    tasks = supervisor_agent.plan_tasks(state["user_query"], intent_result)
    state["tasks"] = tasks
    
    # 4. 设置下一个Agent
    if tasks:
        first_task = tasks[0]
        state["current_task_id"] = first_task.task_id
        
        if first_task.task_type == TaskType.QUERY:
            state["next_agent"] = AgentName.QUERY
        # ...
    
    return state
```

### 3.3 Query Agent (agents/query_agent.py)

Query Agent负责NL转SQL：

```python
class QueryAgent:
    def nl_to_sql(self, query: str, context: Dict = None) -> Tuple[str, str]:
        """
        自然语言转SQL
        """
        # 构建提示词，包含数据库Schema
        prompt = f"""
        数据库Schema:
        {self.get_schema()}
        
        用户查询: {query}
        """
        
        # 调用LLM
        response = create_llm_call(
            system_prompt=QUERY_AGENT_SYSTEM_PROMPT,
            user_prompt=prompt
        )
        
        # 解析SQL
        result = self._parse_json_response(response)
        return result["sql"], result.get("reasoning", "")
    
    def execute_query(self, sql: str) -> QueryResult:
        """
        执行SQL查询
        """
        result = QueryResult()
        
        # 安全性检查
        if not self._is_safe_query(sql):
            result.error = "SQL存在安全风险"
            return result
        
        try:
            # 执行查询
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 获取结果
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # 转换为字典列表
            result.data = [dict(zip(columns, row)) for row in rows]
            result.executed = True
            result.row_count = len(result.data)
            
        except sqlite3.Error as e:
            result.error = str(e)
        
        return result
```

### 3.4 工作流编排 (graph/workflow.py)

完整的工作流定义：

```python
def create_workflow():
    """创建LangGraph工作流"""
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("query_agent", query_agent_node)
    workflow.add_node("analysis_agent", analysis_agent_node)
    workflow.add_node("visualization_agent", visualization_agent_node)
    workflow.add_node("integrate", integrate_node)
    
    # 设置入口点
    workflow.set_entry_point("supervisor")
    
    # 定义路由函数
    def route_agent(state):
        next_agent = state["next_agent"]
        
        route_map = {
            AgentName.QUERY: "query_agent",
            AgentName.ANALYSIS: "analysis_agent",
            AgentName.VISUALIZATION: "visualization_agent",
            AgentName.TERMINATE: "integrate"
        }
        
        return route_map.get(next_agent, "integrate")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "supervisor",
        route_agent,
        {...}
    )
    
    workflow.add_conditional_edges(
        "query_agent",
        route_agent,
        {...}
    )
    
    # 添加最终边
    workflow.add_edge("integrate", END)
    
    return workflow
```

---

## 4. 使用示例

### 4.1 命令行使用

```bash
# 基础查询
python main.py "显示最近一个月的销售额"

# 分析查询
python main.py "分析最近三个月的销售趋势"

# 可视化查询
python main.py "生成各地区销售额的图表"

# 交互模式
python main.py --interactive
```

### 4.2 Python API使用

```python
from main import create_api

# 创建API实例
api = create_api("my_session")

# 执行查询
result = api.query("显示最近一个月的销售额")

# 访问结果
print(result["response"])           # 最终响应
print(result["query_result"].data) # 查询数据
print(result["analysis_result"].insights)  # 分析洞察

# 简单查询
response = api.query_simple("分析销售趋势")
print(response)
```

### 4.3 直接使用Agent

```python
from agents.query_agent import query_agent
from agents.analysis_agent import analysis_agent

# 1. 执行查询
query_result = query_agent.query("显示各地区销售额")
print(f"SQL: {query_result.sql}")
print(f"数据: {query_result.data}")

# 2. 分析数据
analysis_result = analysis_agent.analyze(
    query="分析销售趋势",
    data=query_result.data
)
print(f"统计: {analysis_result.statistics}")
print(f"洞察: {analysis_result.insights}")
```

### 4.4 自定义工作流

```python
from graph.workflow import DataAnalysisWorkflow

# 创建自定义工作流
wf = DataAnalysisWorkflow(use_checkpointer=True)

# 运行查询
result = wf.run("查询销售额", session_id="my_session")

# 处理结果
for state in result.values():
    print(state["final_response"])
```

---

## 5. 扩展方向

### 5.1 支持更多数据源

```python
# 添加MySQL支持
class MySQLQueryAgent:
    def __init__(self, host, port, user, password, database):
        self.connection = pymysql.connect(
            host=host, port=port,
            user=user, password=password,
            database=database
        )

# 添加PostgreSQL支持
class PostgreSQLQueryAgent:
    def __init__(self, dsn):
        self.connection = psycopg2.connect(dsn=dsn)
```

### 5.2 添加更多Agent类型

```python
# 报表Agent - 生成详细报表
class ReportAgent:
    def generate_report(self, data, template):
        ...

# 预测Agent - 时间序列预测
class ForecastAgent:
    def forecast(self, data, periods):
        ...

# 推荐Agent - 智能推荐
class RecommendationAgent:
    def recommend(self, user_id, data):
        ...
```

### 5.3 增强可视化能力

```python
# 添加更多图表类型
- 地理热力图
- 桑基图
- 雷达图
- 词云图

# 交互式图表
- 使用Plotly替代Matplotlib
- 支持图表缩放、筛选
```

### 5.4 集成LLM Agent

```python
# 使用LangChain的Agent能力
from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool

# 创建自定义工具
def query_tool(query):
    return query_agent.query(query)

# 初始化Agent
tools = [
    Tool(name="SQL查询", func=query_tool, description="执行SQL查询")
]

agent = initialize_agent(
    tools, llm, agent=AgentType.CONVERSATIONAL_ZERO_SHOT_REACT_DESCRIPTION
)
```

### 5.5 性能优化

```python
# 1. 查询结果缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(sql):
    return execute_query(sql)

# 2. 并行查询
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(query, q) for q in queries]
    results = [f.result() for f in futures]

# 3. 异步工作流
import asyncio
from langgraph.graph import AsyncStateGraph

async def async_workflow():
    async_graph = AsyncStateGraph(AgentState)
    # ...
```

---

## 📚 总结

本项目展示了一个完整的Multi-Agent系统架构：

1. **状态机驱动**：使用LangGraph管理Agent协作
2. **清晰的职责划分**：每个Agent专注于特定任务
3. **灵活的扩展性**：易于添加新Agent和新功能
4. **完整的错误处理**：确保系统稳定运行

通过学习本项目，您可以掌握：
- LangGraph状态机编程
- Multi-Agent系统设计
- 自然语言处理应用
- 数据分析工作流

希望本教程对您有所帮助！🎉
