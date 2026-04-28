"""
Analysis Agent单元测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from datetime import datetime, timedelta

from agents.analysis_agent import AnalysisAgent, PandasAnalyzer, analysis_agent


class TestPandasAnalyzer(unittest.TestCase):
    """Pandas分析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = PandasAnalyzer()
        
        # 测试数据
        self.test_data = [
            {"id": 1, "name": "产品A", "amount": 100, "region": "华东"},
            {"id": 2, "name": "产品B", "amount": 200, "region": "华南"},
            {"id": 3, "name": "产品C", "amount": 150, "region": "华东"},
            {"id": 4, "name": "产品D", "amount": 300, "region": "华北"},
            {"id": 5, "name": "产品E", "amount": 250, "region": "华南"},
        ]
    
    def test_compute_statistics(self):
        """测试统计计算"""
        stats = self.analyzer.compute_statistics(self.test_data)
        
        self.assertIn("amount", stats)
        self.assertEqual(stats["amount"]["count"], 5)
        self.assertEqual(stats["amount"]["sum"], 1000)
        self.assertAlmostEqual(stats["amount"]["mean"], 200, places=0)
    
    def test_compute_statistics_empty_data(self):
        """测试空数据统计"""
        stats = self.analyzer.compute_statistics([])
        self.assertEqual(stats, {})
    
    def test_detect_trends(self):
        """测试趋势检测"""
        # 创建有时间序列的测试数据
        time_data = []
        base_date = datetime.now()
        
        for i in range(10):
            time_data.append({
                "date": (base_date - timedelta(days=10-i)).strftime("%Y-%m-%d"),
                "amount": 100 + i * 10  # 递增趋势
            })
        
        trends = self.analyzer.detect_trends(time_data, "date", "amount")
        
        self.assertIsInstance(trends, list)
        self.assertGreater(len(trends), 0)
    
    def test_detect_trends_no_time_column(self):
        """测试无时间列的趋势检测"""
        trends = self.analyzer.detect_trends(self.test_data, "date", "amount")
        self.assertEqual(trends, [])
    
    def test_detect_anomalies(self):
        """测试异常检测"""
        # 创建有异常值的数据
        anomaly_data = [
            {"amount": 100},
            {"amount": 110},
            {"amount": 105},
            {"amount": 200},  # 异常值
            {"amount": 102},
        ]
        
        anomalies = self.analyzer.detect_anomalies(anomaly_data, "amount")
        
        # 应该检测到至少一个异常
        self.assertIsInstance(anomalies, list)
    
    def test_find_time_column(self):
        """测试时间列识别"""
        data = [
            {"sale_date": "2024-01-01", "amount": 100},
            {"order_date": "2024-01-02", "amount": 200},
        ]
        
        time_col = self.analyzer._find_time_column(data)
        self.assertIn(time_col, ["sale_date", "order_date"])
    
    def test_find_value_column(self):
        """测试数值列识别"""
        value_col = self.analyzer._find_value_column(self.test_data)
        self.assertEqual(value_col, "amount")


class TestAnalysisAgent(unittest.TestCase):
    """Analysis Agent测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = AnalysisAgent()
        
        # 测试数据
        self.test_data = [
            {"id": 1, "product": "产品A", "amount": 100, "region": "华东"},
            {"id": 2, "product": "产品B", "amount": 200, "region": "华南"},
            {"id": 3, "product": "产品C", "amount": 150, "region": "华东"},
            {"id": 4, "product": "产品D", "amount": 300, "region": "华北"},
            {"id": 5, "product": "产品E", "amount": 250, "region": "华南"},
        ]
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.agent)
        self.assertIsInstance(self.agent.pandas_analyzer, PandasAnalyzer)
    
    def test_analyze_empty_data(self):
        """测试空数据分析"""
        result = self.agent.analyze("测试查询", [], "")
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.error)
    
    def test_analyze_with_data(self):
        """测试有数据的分析"""
        result = self.agent.analyze("分析销售数据", self.test_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result.statistics, dict)
        self.assertIn("amount", result.statistics)
    
    def test_analyze_generates_insights(self):
        """测试分析生成洞察"""
        result = self.agent.analyze("分析销售趋势", self.test_data)
        
        # 应该有统计信息或洞察
        has_result = (
            result.statistics or 
            result.insights or 
            result.trends
        )
        self.assertTrue(has_result)
    
    def test_fallback_insights_generation(self):
        """测试降级洞察生成"""
        insights = self.agent._generate_fallback_insights(self.test_data)
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        self.assertIn("共分析了", insights[0])


class TestAnalysisAgentIntegration(unittest.TestCase):
    """Analysis Agent集成测试"""
    
    def test_full_analysis_flow(self):
        """测试完整分析流程"""
        agent = AnalysisAgent()
        
        # 模拟查询结果数据
        query_data = [
            {"region": "华东", "amount": 1000, "date": "2024-01-01"},
            {"region": "华东", "amount": 1200, "date": "2024-01-02"},
            {"region": "华南", "amount": 800, "date": "2024-01-01"},
            {"region": "华南", "amount": 900, "date": "2024-01-02"},
        ]
        
        result = agent.analyze(
            query="分析各地区销售情况",
            data=query_data,
            context_summary=""
        )
        
        self.assertTrue(hasattr(result, 'statistics'))
        self.assertTrue(hasattr(result, 'insights'))
        self.assertTrue(hasattr(result, 'trends'))


if __name__ == '__main__':
    unittest.main()
