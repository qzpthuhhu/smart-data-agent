"""
Graph模块
包含状态定义、工作流和Supervisor Agent
"""

from .state import (
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

from .supervisor import (
    SupervisorAgent,
    supervisor_agent,
    supervisor_node,
    integrate_node
)

# 工作流相关（可能需要LangGraph）
try:
    from .workflow import (
        create_workflow,
        create_checkpointer,
        DataAnalysisWorkflow,
        default_workflow,
        run_query,
        run_query_full
    )
    WORKFLOW_AVAILABLE = True
except ImportError as e:
    WORKFLOW_AVAILABLE = False
    create_workflow = None
    create_checkpointer = None
    DataAnalysisWorkflow = None
    default_workflow = None
    run_query = None
    run_query_full = None

__all__ = [
    # 状态
    "AgentState",
    "TaskType",
    "IntentType", 
    "AgentName",
    "Task",
    "QueryResult",
    "AnalysisResult",
    "VisualizationResult",
    "create_initial_state",
    
    # Supervisor
    "SupervisorAgent",
    "supervisor_agent",
    "supervisor_node",
    "integrate_node",
    
    # 工作流
    "create_workflow",
    "create_checkpointer",
    "DataAnalysisWorkflow",
    "default_workflow",
    "run_query",
    "run_query_full",
    "WORKFLOW_AVAILABLE"
]
