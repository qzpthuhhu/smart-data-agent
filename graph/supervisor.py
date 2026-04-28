"""
Supervisor Agent模块
负责任务规划、意图识别和结果整合
"""

import json
import re
from typing import Dict, Any, List, Optional
from .state import AgentState, TaskType, IntentType, AgentName, Task, create_initial_state
from config import config, create_llm_call


# ============ 提示词模板 ============

SUPERVISOR_SYSTEM_PROMPT = """你是一个智能数据分析系统的Supervisor Agent。你的职责是：

1. **意图识别**：分析用户的查询，判断其意图类型
2. **任务规划**：将复杂任务拆解为可执行的子任务
3. **结果整合**：将多个Agent的结果整合为最终响应

## 意图类型定义：
- direct_query: 直接查询数据（如"显示销售额"、"查询库存"）
- trend_analysis: 趋势分析（如"分析销售趋势"、"查看增长情况"）
- comparison: 对比分析（如"对比不同地区的销售"）
- anomaly_detection: 异常检测（如"找出异常数据"）
- report_generation: 报告生成（如"生成销售报告"）
- question: 一般问答

## 任务类型定义：
- query: 数据查询任务
- analysis: 数据分析任务
- visualization: 可视化任务
- mixed: 混合任务（包含多个子任务）
- unknown: 未知任务

## 输出格式：
请严格按照以下JSON格式输出，不要包含其他内容：
```json
{
    "intent": "意图类型",
    "task_type": "任务类型", 
    "confidence": 0.0-1.0的置信度,
    "tasks": [
        {
            "task_id": "task_1",
            "task_type": "任务类型",
            "description": "任务描述",
            "dependencies": []
        }
    ],
    "reasoning": "推理过程说明"
}
```
"""

SUPERVISOR_TASK_PROMPT = """分析以下用户查询，识别意图并规划任务：

用户查询：{query}

请分析并输出JSON格式的结果。"""


RESPONSE_INTEGRATION_PROMPT = """你是一个智能数据分析系统的Supervisor Agent。请将以下信息整合为最终的用户响应。

## 用户原始查询：
{query}

## 查询结果：
{query_result}

## 分析结果：
{analysis_result}

## 可视化结果：
{visualization_result}

## 中间步骤：
{intermediate_steps}

请用自然语言向用户解释结果，确保：
1. 回答直接针对用户的问题
2. 突出显示关键发现和洞察
3. 解释分析方法（如有）
4. 说明生成的图表（如有）
5. 保持友好、专业的语气

如果有任何错误或问题，也要清晰地告知用户。"""


class SupervisorAgent:
    """
    Supervisor Agent
    
    核心职责：
    - 意图识别：分析用户查询，判断意图类型
    - 任务规划：拆解复杂任务为子任务
    - 结果整合：整合各Agent结果，生成最终响应
    """
    
    def __init__(self):
        """初始化Supervisor Agent"""
        self.system_prompt = SUPERVISOR_SYSTEM_PROMPT
        self.llm_config = config.llm
        self.max_retries = 3
    
    def recognize_intent(self, query: str) -> Dict[str, Any]:
        """
        意图识别
        
        Args:
            query: 用户查询
            
        Returns:
            意图识别结果，包含intent、task_type、confidence等
        """
        prompt = SUPERVISOR_TASK_PROMPT.format(query=query)
        
        for attempt in range(self.max_retries):
            try:
                response = create_llm_call(
                    system_prompt=self.system_prompt,
                    user_prompt=prompt,
                    temperature=0.3  # 意图识别使用较低的随机性
                )
                
                # 解析JSON响应
                result = self._parse_json_response(response)
                if result:
                    return result
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败，返回默认值
                    return self._get_default_intent(query)
                continue
        
        return self._get_default_intent(query)
    
    def plan_tasks(self, query: str, intent_result: Dict[str, Any]) -> List[Task]:
        """
        任务规划
        
        Args:
            query: 用户查询
            intent_result: 意图识别结果
            
        Returns:
            任务列表
        """
        # 从意图识别结果中获取任务
        tasks_data = intent_result.get("tasks", [])
        tasks = []
        
        for task_data in tasks_data:
            task = Task(
                task_id=task_data.get("task_id", f"task_{len(tasks)}"),
                task_type=TaskType(task_data.get("task_type", "unknown")),
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        # 如果没有规划出任务，生成默认任务
        if not tasks:
            tasks = self._generate_default_tasks(query, intent_result)
        
        return tasks
    
    def integrate_response(
        self,
        query: str,
        query_result: Optional[Dict[str, Any]] = None,
        analysis_result: Optional[Dict[str, Any]] = None,
        visualization_result: Optional[Dict[str, Any]] = None,
        intermediate_steps: Optional[List[Dict]] = None
    ) -> str:
        """
        整合响应
        
        Args:
            query: 用户查询
            query_result: 查询结果
            analysis_result: 分析结果
            visualization_result: 可视化结果
            intermediate_steps: 中间步骤
            
        Returns:
            整合后的响应文本
        """
        # 格式化查询结果
        query_str = "无"
        if query_result:
            if isinstance(query_result, dict):
                if query_result.get("executed") and query_result.get("data"):
                    query_str = self._format_query_result(query_result)
                elif query_result.get("error"):
                    query_str = f"查询失败: {query_result['error']}"
        
        # 格式化分析结果
        analysis_str = "无"
        if analysis_result:
            if isinstance(analysis_result, dict):
                if analysis_result.get("insights"):
                    analysis_str = "\n".join([
                        f"- {insight}" for insight in analysis_result.get("insights", [])
                    ])
                elif analysis_result.get("error"):
                    analysis_str = f"分析失败: {analysis_result['error']}"
        
        # 格式化可视化结果
        viz_str = "无"
        if visualization_result:
            if isinstance(visualization_result, dict):
                if visualization_result.get("file_path"):
                    viz_str = f"已生成图表: {visualization_result['file_path']}"
                    if visualization_result.get("description"):
                        viz_str += f"\n{visualization_result['description']}"
                elif visualization_result.get("error"):
                    viz_str = f"可视化失败: {visualization_result['error']}"
        
        # 格式化中间步骤
        steps_str = "无"
        if intermediate_steps:
            steps_list = []
            for step in intermediate_steps[-3:]:  # 只显示最近3步
                if isinstance(step, dict):
                    agent = step.get("agent", "未知")
                    action = step.get("action", "执行操作")
                    steps_list.append(f"- {agent}: {action}")
            steps_str = "\n".join(steps_list) if steps_list else "无"
        
        prompt = RESPONSE_INTEGRATION_PROMPT.format(
            query=query,
            query_result=query_str,
            analysis_result=analysis_str,
            visualization_result=viz_str,
            intermediate_steps=steps_str
        )
        
        try:
            response = create_llm_call(
                system_prompt="你是一个数据分析助手，擅长用简洁清晰的语言解释数据和结果。",
                user_prompt=prompt,
                temperature=0.7
            )
            return response
        except Exception as e:
            # LLM调用失败时，返回降级响应
            return self._generate_fallback_response(
                query, query_result, analysis_result, visualization_result
            )
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析JSON响应
        
        Args:
            response: LLM响应文本
            
        Returns:
            解析后的字典，解析失败返回None
        """
        try:
            # 尝试提取JSON块
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # 验证必要字段
            if "intent" in result and "task_type" in result:
                return result
            return None
            
        except (json.JSONDecodeError, AttributeError) as e:
            return None
    
    def _get_default_intent(self, query: str) -> Dict[str, Any]:
        """
        获取默认意图（当LLM解析失败时使用）
        
        Args:
            query: 用户查询
            
        Returns:
            默认意图结果
        """
        query_lower = query.lower()
        
        # 简单的关键词匹配
        if any(kw in query_lower for kw in ["分析", "趋势", "变化"]):
            task_type = "analysis"
            intent = "trend_analysis"
        elif any(kw in query_lower for kw in ["显示", "查询", "查看", "获取"]):
            task_type = "query"
            intent = "direct_query"
        elif any(kw in query_lower for kw in ["图表", "可视化", "画图", "绘制"]):
            task_type = "visualization"
            intent = "question"
        else:
            task_type = "mixed"
            intent = "question"
        
        return {
            "intent": intent,
            "task_type": task_type,
            "confidence": 0.5,
            "tasks": [],
            "reasoning": "基于关键词匹配的默认意图识别"
        }
    
    def _generate_default_tasks(
        self,
        query: str,
        intent_result: Dict[str, Any]
    ) -> List[Task]:
        """
        生成默认任务
        
        Args:
            query: 用户查询
            intent_result: 意图识别结果
            
        Returns:
            任务列表
        """
        task_type_str = intent_result.get("task_type", "query")
        tasks = []
        
        # 根据任务类型生成对应任务
        if task_type_str == "query":
            tasks.append(Task(
                task_id="task_query",
                task_type=TaskType.QUERY,
                description=f"执行数据查询: {query}",
                dependencies=[]
            ))
        elif task_type_str == "analysis":
            tasks.append(Task(
                task_id="task_query",
                task_type=TaskType.QUERY,
                description=f"获取分析所需数据: {query}",
                dependencies=[]
            ))
            tasks.append(Task(
                task_id="task_analysis",
                task_type=TaskType.ANALYSIS,
                description=f"执行数据分析: {query}",
                dependencies=["task_query"]
            ))
        elif task_type_str == "visualization":
            tasks.append(Task(
                task_id="task_query",
                task_type=TaskType.QUERY,
                description=f"获取可视化所需数据: {query}",
                dependencies=[]
            ))
            tasks.append(Task(
                task_id="task_viz",
                task_type=TaskType.VISUALIZATION,
                description=f"生成可视化图表: {query}",
                dependencies=["task_query"]
            ))
        else:  # mixed
            tasks.append(Task(
                task_id="task_query",
                task_type=TaskType.QUERY,
                description=f"执行数据查询: {query}",
                dependencies=[]
            ))
            tasks.append(Task(
                task_id="task_analysis",
                task_type=TaskType.ANALYSIS,
                description=f"执行数据分析: {query}",
                dependencies=["task_query"]
            ))
            tasks.append(Task(
                task_id="task_viz",
                task_type=TaskType.VISUALIZATION,
                description=f"生成可视化图表: {query}",
                dependencies=["task_query"]
            ))
        
        return tasks
    
    def _format_query_result(self, query_result: Dict[str, Any]) -> str:
        """
        格式化查询结果
        
        Args:
            query_result: 查询结果字典
            
        Returns:
            格式化的字符串
        """
        data = query_result.get("data", [])
        sql = query_result.get("sql", "")
        row_count = query_result.get("row_count", 0)
        
        lines = []
        
        if sql:
            lines.append(f"执行的SQL:\n{sql}\n")
        
        if data:
            lines.append(f"查询到 {row_count} 条记录:")
            
            # 表格形式展示数据（最多10条）
            display_data = data[:10]
            
            # 获取列名
            if isinstance(display_data[0], dict):
                headers = list(display_data[0].keys())
                lines.append(" | ".join(headers))
                lines.append("-" * (len(" | ".join(headers))))
                
                for row in display_data:
                    lines.append(" | ".join(str(row.get(h, "")) for h in headers))
            
            if row_count > 10:
                lines.append(f"\n... (还有 {row_count - 10} 条记录)")
        
        return "\n".join(lines)
    
    def _generate_fallback_response(
        self,
        query: str,
        query_result: Optional[Dict] = None,
        analysis_result: Optional[Dict] = None,
        visualization_result: Optional[Dict] = None
    ) -> str:
        """
        生成降级响应（当LLM不可用时）
        
        Args:
            query: 用户查询
            query_result: 查询结果
            analysis_result: 分析结果
            visualization_result: 可视化结果
            
        Returns:
            降级响应文本
        """
        parts = [f"针对您的查询「{query}」，以下是结果："]
        
        if query_result and query_result.get("executed"):
            data = query_result.get("data", [])
            if data:
                parts.append(f"\n\n共查询到 {len(data)} 条记录。")
                if isinstance(data[0], dict):
                    parts.append("数据摘要:")
                    for key in list(data[0].keys())[:5]:
                        values = [str(row.get(key, "")) for row in data[:5]]
                        parts.append(f"- {key}: {', '.join(values)}")
        
        if analysis_result and analysis_result.get("insights"):
            parts.append("\n\n关键洞察:")
            for insight in analysis_result.get("insights", [])[:3]:
                parts.append(f"- {insight}")
        
        if visualization_result and visualization_result.get("file_path"):
            parts.append(f"\n\n已生成图表: {visualization_result['file_path']}")
        
        return "".join(parts)


# 创建全局实例
supervisor_agent = SupervisorAgent()


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor Agent的LangGraph节点函数
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    user_query = state["user_query"]
    
    # 记录开始步骤
    state["intermediate_steps"].append({
        "agent": "supervisor",
        "action": "开始处理查询",
        "query": user_query
    })
    
    # 意图识别
    intent_result = supervisor_agent.recognize_intent(user_query)
    
    # 更新状态
    state["intent"] = IntentType(intent_result.get("intent", "question"))
    state["task_type"] = TaskType(intent_result.get("task_type", "unknown"))
    state["confidence"] = intent_result.get("confidence", 0.0)
    
    # 任务规划
    tasks = supervisor_agent.plan_tasks(user_query, intent_result)
    state["tasks"] = tasks
    
    # 记录任务规划
    state["intermediate_steps"].append({
        "agent": "supervisor",
        "action": "完成任务规划",
        "tasks": [t.task_id for t in tasks],
        "intent": intent_result.get("intent"),
        "task_type": intent_result.get("task_type")
    })
    
    # 如果有任务，设置第一个任务的Agent
    if tasks:
        first_task = tasks[0]
        state["current_task_id"] = first_task.task_id
        
        # 根据任务类型设置下一个Agent
        if first_task.task_type == TaskType.QUERY:
            state["next_agent"] = AgentName.QUERY
        elif first_task.task_type == TaskType.ANALYSIS:
            state["next_agent"] = AgentName.QUERY  # 先查询数据
        elif first_task.task_type == TaskType.VISUALIZATION:
            state["next_agent"] = AgentName.QUERY  # 先查询数据
        else:
            state["next_agent"] = AgentName.QUERY
    else:
        # 没有任务，检查是否需要整合结果
        if state["query_result"].executed or state["analysis_result"].statistics:
            state["next_agent"] = AgentName.TERMINATE
        else:
            state["error"] = "无法理解您的查询，请尝试重新描述"
            state["should_continue"] = False
    
    return state


def integrate_node(state: AgentState) -> AgentState:
    """
    结果整合节点
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    # 整合响应
    response = supervisor_agent.integrate_response(
        query=state["user_query"],
        query_result={
            "executed": state["query_result"].executed,
            "data": state["query_result"].data,
            "sql": state["query_result"].sql,
            "row_count": state["query_result"].row_count,
            "error": state["query_result"].error
        } if state["query_result"] else None,
        analysis_result={
            "statistics": state["analysis_result"].statistics,
            "insights": state["analysis_result"].insights,
            "trends": state["analysis_result"].trends,
            "anomalies": state["analysis_result"].anomalies,
            "error": state["analysis_result"].error
        } if state["analysis_result"] else None,
        visualization_result={
            "file_path": state["visualization_result"].file_path,
            "description": state["visualization_result"].description,
            "chart_type": state["visualization_result"].chart_type,
            "error": state["visualization_result"].error
        } if state["visualization_result"] else None,
        intermediate_steps=state["intermediate_steps"]
    )
    
    state["final_response"] = response
    state["should_continue"] = False
    state["next_agent"] = AgentName.TERMINATE
    
    return state
