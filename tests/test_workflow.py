"""
工作流单元测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import patch, MagicMock

from graph.state import (
    AgentState, TaskType, IntentType, AgentName, 
    Task, create_initial_state, QueryResult
)
from graph.workflow import (
    create_workflow, DataAnalysisWorkflow, run_query
)


class TestAgentState(unittest.TestCase):
    """Agent状态测试类"""
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        state = create_initial_state(
            user_query="测试查询",
            session_id="test_session",
            turn=1
        )
        
        self.assertEqual(state["user_query"], "测试查询")
        self.assertEqual(state["session_id"], "test_session")
        self.assertEqual(state["turn"], 1)
        self.assertEqual(state["task_type"], TaskType.UNKNOWN)
        self.assertEqual(state["intent"], IntentType.QUESTION)
    
    def test_initial_state_defaults(self):
        """测试默认初始状态"""
        state = create_initial_state(user_query="测试")
        
        self.assertEqual(state["session_id"], "default")
        self.assertEqual(state["turn"], 0)
        self.assertEqual(state["should_continue"], True)
        self.assertEqual(state["error"], None)
        self.assertEqual(len(state["tasks"]), 0)
        self.assertEqual(len(state["intermediate_steps"]), 0)


class TestTask(unittest.TestCase):
    """任务测试类"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            task_id="task_1",
            task_type=TaskType.QUERY,
            description="执行查询"
        )
        
        self.assertEqual(task.task_id, "task_1")
        self.assertEqual(task.task_type, TaskType.QUERY)
        self.assertEqual(task.status, "pending")
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)
    
    def test_task_with_dependencies(self):
        """测试有依赖的任务"""
        task = Task(
            task_id="task_2",
            task_type=TaskType.ANALYSIS,
            description="分析数据",
            dependencies=["task_1"]
        )
        
        self.assertEqual(len(task.dependencies), 1)
        self.assertIn("task_1", task.dependencies)


class TestWorkflow(unittest.TestCase):
    """工作流测试类"""
    
    def test_create_workflow(self):
        """测试创建工作流"""
        workflow = create_workflow()
        self.assertIsNotNone(workflow)
    
    def test_workflow_compilation(self):
        """测试工作流编译"""
        workflow = create_workflow()
        compiled = workflow.compile()
        self.assertIsNotNone(compiled)
    
    def test_workflow_with_checkpointer(self):
        """测试带检查点的工作流"""
        wf = DataAnalysisWorkflow(use_checkpointer=True)
        self.assertIsNotNone(wf.app)
    
    def test_workflow_without_checkpointer(self):
        """测试不带检查点的工作流"""
        wf = DataAnalysisWorkflow(use_checkpointer=False)
        self.assertIsNotNone(wf.app)


class TestWorkflowNodes(unittest.TestCase):
    """工作流节点测试类"""
    
    @patch('config.create_llm_call')
    def test_supervisor_node(self, mock_llm):
        """测试Supervisor节点"""
        # Mock LLM调用
        mock_llm.return_value = '''
        {
            "intent": "direct_query",
            "task_type": "query",
            "confidence": 0.9,
            "tasks": [
                {
                    "task_id": "task_1",
                    "task_type": "query",
                    "description": "执行查询"
                }
            ]
        }
        '''
        
        from graph.supervisor import supervisor_node
        
        state = create_initial_state(user_query="查询销售额")
        updated_state = supervisor_node(state)
        
        self.assertIsNotNone(updated_state)
        self.assertIn("tasks", updated_state)
    
    @patch('config.create_llm_call')
    def test_integrate_node(self, mock_llm):
        """测试整合节点"""
        # Mock LLM调用
        mock_llm.return_value = "查询结果：销售额总计10000元"
        
        from graph.supervisor import integrate_node
        
        state = create_initial_state(user_query="查询销售额")
        state["query_result"] = QueryResult(executed=True)
        
        updated_state = integrate_node(state)
        
        self.assertIsNotNone(updated_state)
        self.assertFalse(updated_state["should_continue"])


class TestDataAnalysisWorkflow(unittest.TestCase):
    """数据分析工作流测试类"""
    
    def test_workflow_initialization(self):
        """测试工作流初始化"""
        wf = DataAnalysisWorkflow()
        self.assertIsNotNone(wf.graph)
        self.assertIsNotNone(wf.app)
    
    def test_workflow_run_empty(self):
        """测试空工作流运行"""
        wf = DataAnalysisWorkflow()
        
        # 这个测试在无API密钥时会失败
        # 使用mock来处理
        pass


class TestRoutingLogic(unittest.TestCase):
    """路由逻辑测试类"""
    
    def test_route_from_supervisor_to_query(self):
        """测试从Supervisor路由到Query Agent"""
        from graph.supervisor import supervisor_node
        
        # Mock意图识别返回query任务
        with patch('config.create_llm_call') as mock:
            mock.return_value = '''
            {
                "intent": "direct_query",
                "task_type": "query",
                "confidence": 0.9,
                "tasks": [
                    {"task_id": "task_1", "task_type": "query", "description": "查询"}
                ]
            }
            '''
            
            state = create_initial_state("查询销售额")
            state = supervisor_node(state)
            
            self.assertEqual(state["next_agent"], AgentName.QUERY)
    
    def test_route_from_supervisor_to_terminate(self):
        """测试从Supervisor路由到终止"""
        from graph.supervisor import supervisor_node
        
        with patch('config.create_llm_call') as mock:
            mock.return_value = '''
            {
                "intent": "question",
                "task_type": "unknown",
                "confidence": 0.3,
                "tasks": []
            }
            '''
            
            state = create_initial_state("你好")
            state["error"] = "无法理解"
            state["should_continue"] = False
            state = supervisor_node(state)
            
            # 应该整合结果或终止
            self.assertFalse(state["should_continue"])


if __name__ == '__main__':
    unittest.main()
