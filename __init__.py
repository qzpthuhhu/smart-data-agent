"""
智能数据分析Agent系统

基于LangGraph的多Agent协作系统，用于智能数据分析。
支持自然语言查询、自动SQL转换、数据分析、可视化等功能。
"""

__version__ = "1.0.0"
__author__ = "AI Data Analysis Team"

# 导入核心组件
from config import config, validate_config, create_llm_call, get_llm_client
from graph.state import (
    AgentState,
    TaskType,
    IntentType,
    AgentName,
    Task,
    QueryResult,
    AnalysisResult,
    VisualizationResult,
    create_initial_state
)
from graph.workflow import (
    create_workflow,
    DataAnalysisWorkflow,
    default_workflow,
    run_query,
    run_query_full
)
from graph.supervisor import supervisor_agent, supervisor_node, integrate_node
from agents.query_agent import query_agent, query_agent_node
from agents.analysis_agent import analysis_agent, analysis_agent_node
from agents.visualization_agent import viz_agent, visualization_agent_node
from memory import memory_manager, ShortTermMemory, LongTermMemory, MemoryManager

# 导入API
from main import DataAnalysisAPI, create_api

__all__ = [
    # 版本信息
    "__version__",
    
    # 配置
    "config",
    "validate_config",
    "create_llm_call",
    "get_llm_client",
    
    # 状态定义
    "AgentState",
    "TaskType",
    "IntentType",
    "AgentName",
    "Task",
    "QueryResult",
    "AnalysisResult",
    "VisualizationResult",
    "create_initial_state",
    
    # 工作流
    "create_workflow",
    "DataAnalysisWorkflow",
    "default_workflow",
    "run_query",
    "run_query_full",
    
    # Supervisor
    "supervisor_agent",
    "supervisor_node",
    "integrate_node",
    
    # Query Agent
    "query_agent",
    "query_agent_node",
    
    # Analysis Agent
    "analysis_agent",
    "analysis_agent_node",
    
    # Visualization Agent
    "viz_agent",
    "visualization_agent_node",
    
    # 记忆模块
    "memory_manager",
    "ShortTermMemory",
    "LongTermMemory",
    "MemoryManager",
    
    # API
    "DataAnalysisAPI",
    "create_api"
]
