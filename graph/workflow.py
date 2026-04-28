"""
LangGraph工作流模块 (完整版)
集成所有Agent的完整工作流程
"""

from typing import Literal, Dict, Any

# 延迟导入LangGraph
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    MemorySaver = None

from graph.state import AgentState, AgentName, TaskType, create_initial_state
from graph.supervisor import supervisor_node, integrate_node
from agents.query_agent import query_agent_node
from agents.analysis_agent import analysis_agent_node
from agents.visualization_agent import visualization_agent_node
from memory import memory_manager


def create_workflow():
    """
    创建完整的LangGraph工作流
    
    包含所有Agent：
    - Supervisor: 任务规划和结果整合
    - Query Agent: 数据查询
    - Analysis Agent: 数据分析
    - Visualization Agent: 可视化生成
    
    Returns:
        StateGraph实例
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph未安装，请运行: pip install langgraph"
        )
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加所有节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("query_agent", query_agent_node)
    workflow.add_node("analysis_agent", analysis_agent_node)
    workflow.add_node("visualization_agent", visualization_agent_node)
    workflow.add_node("integrate", integrate_node)
    
    # 设置入口点
    workflow.set_entry_point("supervisor")
    
    # ============ 路由函数 ============
    
    def route_from_supervisor(state: AgentState) -> Literal[
        "supervisor", "query_agent", "analysis_agent", 
        "visualization_agent", "integrate", "__end__"
    ]:
        """
        Supervisor节点的路由函数
        """
        if not state.get("should_continue", True):
            return "integrate"
        
        next_agent = state.get("next_agent", AgentName.SUPERVISOR)
        
        if isinstance(next_agent, str):
            agent_name = next_agent
        else:
            agent_name = next_agent.value
        
        route_map = {
            "supervisor": "supervisor",
            "query_agent": "query_agent",
            "analysis_agent": "analysis_agent",
            "visualization_agent": "visualization_agent",
            "terminate": "integrate"
        }
        
        return route_map.get(agent_name, "integrate")
    
    def route_from_query(state: AgentState) -> Literal[
        "supervisor", "query_agent", "analysis_agent", 
        "visualization_agent", "integrate", "__end__"
    ]:
        """
        Query Agent节点的路由函数
        """
        if not state.get("should_continue", True):
            return "integrate"
        
        next_agent = state.get("next_agent", AgentName.SUPERVISOR)
        
        if isinstance(next_agent, str):
            agent_name = next_agent
        else:
            agent_name = next_agent.value
        
        route_map = {
            "supervisor": "supervisor",
            "query_agent": "query_agent",
            "analysis_agent": "analysis_agent",
            "visualization_agent": "visualization_agent",
            "terminate": "integrate"
        }
        
        return route_map.get(agent_name, "integrate")
    
    def route_from_analysis(state: AgentState) -> Literal[
        "supervisor", "query_agent", "analysis_agent", 
        "visualization_agent", "integrate", "__end__"
    ]:
        """
        Analysis Agent节点的路由函数
        """
        if not state.get("should_continue", True):
            return "integrate"
        
        next_agent = state.get("next_agent", AgentName.TERMINATE)
        
        if isinstance(next_agent, str):
            agent_name = next_agent
        else:
            agent_name = next_agent.value
        
        route_map = {
            "supervisor": "supervisor",
            "query_agent": "query_agent",
            "analysis_agent": "analysis_agent",
            "visualization_agent": "visualization_agent",
            "terminate": "integrate"
        }
        
        return route_map.get(agent_name, "integrate")
    
    def route_from_viz(state: AgentState) -> Literal[
        "supervisor", "query_agent", "analysis_agent", 
        "visualization_agent", "integrate", "__end__"
    ]:
        """
        Visualization Agent节点的路由函数
        """
        return "integrate"
    
    # ============ 添加条件边 ============
    
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "supervisor": "supervisor",
            "query_agent": "query_agent",
            "integrate": "integrate"
        }
    )
    
    workflow.add_conditional_edges(
        "query_agent",
        route_from_query,
        {
            "supervisor": "supervisor",
            "query_agent": "query_agent",
            "analysis_agent": "analysis_agent",
            "visualization_agent": "visualization_agent",
            "integrate": "integrate"
        }
    )
    
    workflow.add_conditional_edges(
        "analysis_agent",
        route_from_analysis,
        {
            "visualization_agent": "visualization_agent",
            "integrate": "integrate"
        }
    )
    
    workflow.add_conditional_edges(
        "visualization_agent",
        route_from_viz,
        {
            "integrate": "integrate"
        }
    )
    
    # 添加最终边
    workflow.add_edge("integrate", END)
    
    return workflow


def create_checkpointer():
    """
    创建状态持久化检查点
    
    Returns:
        MemorySaver实例
    """
    return MemorySaver()


class DataAnalysisWorkflow:
    """
    数据分析工作流封装类
    
    提供更高级的接口来使用LangGraph工作流
    """
    
    def __init__(self, use_checkpointer: bool = True):
        """
        初始化工作流
        
        Args:
            use_checkpointer: 是否使用检查点持久化
        """
        self.graph = create_workflow()
        
        if use_checkpointer:
            checkpointer = create_checkpointer()
            self.app = self.graph.compile(checkpointer=checkpointer)
        else:
            self.app = self.graph.compile()
    
    def run(self, query: str, session_id: str = "default", **kwargs):
        """
        运行工作流
        
        Args:
            query: 用户查询
            session_id: 会话ID
            **kwargs: 其他参数
            
        Returns:
            最终状态
        """
        # 创建初始状态
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id,
            turn=kwargs.get("turn", 0)
        )
        
        # 配置checkpointer所需的thread_id
        config = {"configurable": {"thread_id": session_id}}
        
        # 运行工作流
        final_state = None
        for state in self.app.stream(initial_state, config):
            final_state = state
        
        return final_state
    
    def run_with_config(
        self,
        query: str,
        session_id: str = "default",
        config: dict = None
    ):
        """
        使用配置运行工作流
        
        Args:
            query: 用户查询
            session_id: 会话ID
            config: LangGraph配置
            
        Returns:
            最终状态
        """
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id
        )
        
        # 默认配置
        if config is None:
            config = {"configurable": {"thread_id": session_id}}
        
        # 运行
        final_state = None
        for state in self.app.stream(initial_state, config):
            final_state = state
        
        return final_state
    
    def run_with_memory(
        self,
        query: str,
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        运行工作流并保存记忆
        
        Args:
            query: 用户查询
            session_id: 会话ID
            
        Returns:
            包含响应的结果字典
        """
        result = self.run(query, session_id)
        
        # 提取最终响应
        response = ""
        if result:
            for state in result.values():
                if "final_response" in state:
                    response = state["final_response"]
        
        # 保存到记忆
        memory_manager.save_interaction(
            query=query,
            response=response,
            session_id=session_id
        )
        
        return {
            "response": response,
            "raw_state": result
        }


# 创建默认工作流实例
default_workflow = DataAnalysisWorkflow(use_checkpointer=True)


def run_query(query: str, session_id: str = "default") -> str:
    """
    便捷函数：运行查询
    
    Args:
        query: 用户查询
        session_id: 会话ID
        
    Returns:
        最终响应文本
    """
    result = default_workflow.run_with_memory(query, session_id)
    return result.get("response", "处理失败")


# 便捷函数：运行查询并返回完整结果
def run_query_full(query: str, session_id: str = "default") -> Dict[str, Any]:
    """
    运行查询并返回完整结果
    
    Args:
        query: 用户查询
        session_id: 会话ID
        
    Returns:
        包含所有结果的字典
    """
    result = default_workflow.run(query, session_id)
    
    if not result:
        return {"error": "处理失败"}
    
    for state in result.values():
        return {
            "response": state.get("final_response", ""),
            "query_result": state.get("query_result"),
            "analysis_result": state.get("analysis_result"),
            "visualization_result": state.get("visualization_result"),
            "intermediate_steps": state.get("intermediate_steps", []),
            "tasks": state.get("tasks", [])
        }
    
    return {"error": "未找到结果"}


# 导出
__all__ = [
    "create_workflow",
    "create_checkpointer",
    "DataAnalysisWorkflow",
    "default_workflow",
    "run_query",
    "run_query_full"
]
