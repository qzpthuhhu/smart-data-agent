"""
Query Agent单元测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import patch, MagicMock

from agents.query_agent import QueryAgent, query_agent


class TestQueryAgent(unittest.TestCase):
    """Query Agent测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = QueryAgent(db_path=":memory:")  # 使用内存数据库
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.db_path)
    
    def test_nl_to_sql_conversion(self):
        """测试自然语言转SQL"""
        # 这个测试需要LLM API，实际使用时可以mock
        pass
    
    def test_execute_query(self):
        """测试查询执行"""
        # 先创建表和数据
        conn = self.agent.execute_query("""
            CREATE TABLE IF NOT EXISTS test_sales (
                id INTEGER PRIMARY KEY,
                product_name TEXT,
                amount REAL
            )
        """)
        
        # 执行查询
        result = self.agent.execute_query("SELECT * FROM test_sales")
        
        self.assertTrue(result.executed)
        self.assertIsNone(result.error)
    
    def test_safe_query_detection(self):
        """测试安全查询检测"""
        # 安全查询
        self.assertTrue(self.agent._is_safe_query("SELECT * FROM sales"))
        self.assertTrue(self.agent._is_safe_query("SELECT amount FROM sales WHERE region = '华东'"))
        
        # 危险查询
        self.assertFalse(self.agent._is_safe_query("DROP TABLE sales"))
        self.assertFalse(self.agent._is_safe_query("DELETE FROM sales"))
        self.assertFalse(self.agent._is_safe_query("UPDATE sales SET amount = 0"))
        self.assertFalse(self.agent._is_safe_query("INSERT INTO sales VALUES (1, 2, 3)"))
    
    def test_get_schema(self):
        """测试获取数据库Schema"""
        schema = self.agent.get_schema()
        self.assertIsInstance(schema, str)
        self.assertIn("sales", schema)
        self.assertIn("products", schema)
    
    def test_get_sample_data(self):
        """测试获取示例数据"""
        sample = self.agent.get_sample_data("sales", limit=5)
        self.assertIsInstance(sample, str)
        self.assertIn("sales", sample)
    
    def test_query_result_structure(self):
        """测试QueryResult数据结构"""
        from graph.state import QueryResult
        
        result = QueryResult()
        result.executed = True
        result.data = [{"id": 1, "name": "test"}]
        result.row_count = 1
        
        self.assertTrue(result.executed)
        self.assertEqual(result.row_count, 1)
        self.assertEqual(len(result.data), 1)


class TestQueryAgentIntegration(unittest.TestCase):
    """Query Agent集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = QueryAgent(db_path=":memory:")
        
        # 创建测试数据
        self.agent.execute_query("""
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                category TEXT,
                value REAL,
                sale_date TEXT
            )
        """)
        
        # 插入测试数据
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                category TEXT,
                value REAL,
                sale_date TEXT
            )
        """)
        conn.execute("INSERT INTO test_data VALUES (1, 'A', 100, '2024-01-01')")
        conn.execute("INSERT INTO test_data VALUES (2, 'B', 200, '2024-01-02')")
        conn.execute("INSERT INTO test_data VALUES (3, 'A', 150, '2024-01-03')")
        conn.commit()
        conn.close()
    
    def test_full_query_flow(self):
        """测试完整查询流程"""
        # 注意：这里需要mock LLM调用
        pass


if __name__ == '__main__':
    unittest.main()
