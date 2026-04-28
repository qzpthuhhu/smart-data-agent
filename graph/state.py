"""
LangGraph状态定义模块
定义整个Agent系统的状态结构
"""

from typing import TypedDict, Annotated, Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import operator


class TaskType(Enum):
    """任务类型枚举"""
    QUERY = "query"           # 数据查询
    ANALYSIS = "analysis"     # 数据分析
    VISUALIZATION = "visualization"  # 可视化
    MIXED = "mixed"           # 混合任务
    UNKNOWN = "unknown"       # 未知


class IntentType(Enum):
    """意图类型枚举"""
    DIRECT_QUERY = "direct_query"     # 直接查询
    TREND_ANALYSIS = "trend_analysis" # 趋势分析
    COMPARISON = "comparison"         # 对比分析
    ANOMALY_DETECTION = "anomaly_detection"  # 异常检测
    REPORT_GENERATION = "report_generation"   # 报告生成
    QUESTION = "question"            # 问答


class AgentName(Enum):
    """Agent名称枚举"""
    SUPERVISOR = "supervisor"
    QUERY = "query_agent"
    ANALYSIS = "analysis_agent"
    VISUALIZATION = "visualization_agent"
    TERMINATE = "terminate"


@dataclass
class QueryResult:
    """查询结果数据结构"""
    sql: str = ""                           # 生成的SQL
    executed: bool = False                  # 是否执行成功
    data: Optional[List[Dict]] = None       # 查询结果数据
    row_count: int = 0                      # 结果行数
    error: Optional[str] = None             # 错误信息
    execution_time: float = 0.0             # 执行时间（秒）


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    statistics: Dict[str, Any] = field(default_factory=dict)  # 统计指标
    trends: List[Dict[str, Any]] = field(default_factory=list)  # 趋势数据
    anomalies: List[Dict[str, Any]] = field(default_factory=list)  # 异常点
    insights: List[str] = field(default_factory=list)  # 洞察发现
    error: Optional[str] = None


@dataclass
class VisualizationResult:
    """可视化结果数据结构"""
    chart_type: str = ""                    # 图表类型
    file_path: Optional[str] = None         # 图表文件路径
    description: str = ""                   # 图表描述
    saved: bool = False                     # 是否已保存
    error: Optional[str] = None


@dataclass
class Task:
    """子任务数据结构"""
    task_id: str                            # 任务ID
    task_type: TaskType                      # 任务类型
    description: str                         # 任务描述
    status: str = "pending"                  # 状态：pending/running/completed/failed
    result: Optional[Any] = None            # 任务结果
    error: Optional[str] = None             # 错误信息
    dependencies: List[str] = field(default_factory=list)  # 依赖任务ID


class AgentState(TypedDict):
    """
    LangGraph Agent状态定义
    这是整个系统的核心数据结构，在各Agent之间传递
    """
    # === 对话上下文 ===
    user_query: str                          # 用户原始查询
    session_id: str                          # 会话ID
    turn: int                                 # 当前轮次
    
    # === 意图识别 ===
    task_type: TaskType                       # 识别的任务类型
    intent: IntentType                         # 具体意图
    confidence: float                          # 置信度
    
    # === 任务规划 ===
    tasks: List[Task]                          # 拆解的子任务列表
    current_task_id: str                       # 当前执行的任务ID
    
    # === 查询相关 ===
    query_result: QueryResult                  # Query Agent的结果
    
    # === 分析相关 ===
    analysis_result: AnalysisResult            # Analysis Agent的结果
    
    # === 可视化相关 ===
    visualization_result: VisualizationResult  # Visualization Agent的结果
    
    # === 整合结果 ===
    final_response: str                         # 最终整合的响应
    intermediate_steps: List[Dict[str, Any]]   # 中间步骤记录
    
    # === 记忆相关 ===
    short_term_memory: List[Dict[str, str]]    # 短期记忆（对话历史）
    context_summary: str                       # 上下文摘要
    
    # === 控制流 ===
    next_agent: AgentName                       # 下一个要调用的Agent
    should_continue: bool                       # 是否继续执行
    error: Optional[str]                        # 错误信息


def create_initial_state(
    user_query: str,
    session_id: str = "default",
    turn: int = 0
) -> AgentState:
    """
    创建初始状态
    
    Args:
        user_query: 用户查询
        session_id: 会话ID
        turn: 轮次
        
    Returns:
        初始化的AgentState
    """
    return AgentState(
        user_query=user_query,
        session_id=session_id,
        turn=turn,
        task_type=TaskType.UNKNOWN,
        intent=IntentType.QUESTION,
        confidence=0.0,
        tasks=[],
        current_task_id="",
        query_result=QueryResult(),
        analysis_result=AnalysisResult(),
        visualization_result=VisualizationResult(),
        final_response="",
        intermediate_steps=[],
        short_term_memory=[],
        context_summary="",
        next_agent=AgentName.SUPERVISOR,
        should_continue=True,
        error=None
    )


# 状态更新操作符
def add_intermediate_step(state: AgentState, step: Dict[str, Any]) -> AgentState:
    """添加中间步骤"""
    state["intermediate_steps"].append(step)
    return state


def update_query_result(state: AgentState, result: QueryResult) -> AgentState:
    """更新查询结果"""
    state["query_result"] = result
    return state


def update_analysis_result(state: AgentState, result: AnalysisResult) -> AgentState:
    """更新分析结果"""
    state["analysis_result"] = result
    return state


def update_visualization_result(state: AgentState, result: VisualizationResult) -> AgentState:
    """更新可视化结果"""
    state["visualization_result"] = result
    return state


def add_to_short_term_memory(state: AgentState, entry: Dict[str, str]) -> AgentState:
    """添加到短期记忆"""
    state["short_term_memory"].append(entry)
    # 限制短期记忆大小
    max_turns = 10
    if len(state["short_term_memory"]) > max_turns:
        state["short_term_memory"] = state["short_term_memory"][-max_turns:]
    return state


def set_next_agent(state: AgentState, agent: AgentName) -> AgentState:
    """设置下一个Agent"""
    state["next_agent"] = agent
    return state


def set_error(state: AgentState, error: str) -> AgentState:
    """设置错误"""
    state["error"] = error
    state["should_continue"] = False
    return state
