"""
Visualization Agent单元测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
import tempfile
import shutil

from agents.visualization_agent import VisualizationAgent, ChartGenerator, viz_agent


class TestChartGenerator(unittest.TestCase):
    """图表生成器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = ChartGenerator()
        self.test_dir = tempfile.mkdtemp()
        
        # 测试数据
        self.test_data = [
            {"region": "华东", "amount": 1000},
            {"region": "华南", "amount": 800},
            {"region": "华北", "amount": 1200},
            {"region": "华西", "amount": 600},
        ]
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.plt)
    
    def test_prepare_data(self):
        """测试数据准备"""
        x, y, x_col = self.generator._prepare_data(self.test_data)
        
        self.assertEqual(len(x), 4)
        self.assertEqual(len(y), 4)
        self.assertEqual(x_col, "region")
    
    def test_prepare_aggregate_data(self):
        """测试聚合数据准备"""
        labels, values = self.generator._prepare_aggregate_data(
            self.test_data, "region", "amount"
        )
        
        self.assertEqual(len(labels), 4)
        self.assertEqual(len(values), 4)
    
    def test_create_line_chart(self):
        """测试折线图创建"""
        # 添加时间序列数据
        line_data = [
            {"date": "2024-01-01", "amount": 100},
            {"date": "2024-01-02", "amount": 120},
            {"date": "2024-01-03", "amount": 110},
            {"date": "2024-01-04", "amount": 130},
        ]
        
        save_path = os.path.join(self.test_dir, "line_test.png")
        result = self.generator.create_line_chart(
            line_data,
            title="销售趋势",
            save_path=save_path
        )
        
        self.assertEqual(result, save_path)
        self.assertTrue(os.path.exists(save_path))
    
    def test_create_bar_chart(self):
        """测试柱状图创建"""
        save_path = os.path.join(self.test_dir, "bar_test.png")
        result = self.generator.create_bar_chart(
            self.test_data,
            group_col="region",
            value_col="amount",
            title="地区销售对比",
            save_path=save_path
        )
        
        self.assertEqual(result, save_path)
        self.assertTrue(os.path.exists(save_path))
    
    def test_create_pie_chart(self):
        """测试饼图创建"""
        save_path = os.path.join(self.test_dir, "pie_test.png")
        result = self.generator.create_pie_chart(
            self.test_data,
            group_col="region",
            value_col="amount",
            title="地区销售占比",
            save_path=save_path
        )
        
        self.assertEqual(result, save_path)
        self.assertTrue(os.path.exists(save_path))
    
    def test_create_scatter_chart(self):
        """测试散点图创建"""
        scatter_data = [
            {"quantity": 10, "amount": 100},
            {"quantity": 20, "amount": 200},
            {"quantity": 15, "amount": 150},
            {"quantity": 25, "amount": 250},
        ]
        
        save_path = os.path.join(self.test_dir, "scatter_test.png")
        result = self.generator.create_scatter_chart(
            scatter_data,
            x_col="quantity",
            y_col="amount",
            title="数量金额关系",
            save_path=save_path
        )
        
        self.assertEqual(result, save_path)
        self.assertTrue(os.path.exists(save_path))
    
    def test_generate_colors(self):
        """测试颜色生成"""
        colors = self.generator._generate_colors(3)
        self.assertEqual(len(colors), 3)
        
        # 测试颜色数量超过预设
        colors_many = self.generator._generate_colors(15)
        self.assertEqual(len(colors_many), 15)


class TestVisualizationAgent(unittest.TestCase):
    """可视化Agent测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = VisualizationAgent(output_dir=tempfile.mkdtemp())
        self.test_data = [
            {"region": "华东", "amount": 1000, "category": "电子产品"},
            {"region": "华南", "amount": 800, "category": "电子产品"},
            {"region": "华北", "amount": 1200, "category": "服装"},
        ]
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.chart_generator)
    
    def test_analyze_data_features(self):
        """测试数据特征分析"""
        features = self.agent._analyze_data_features(self.test_data)
        
        self.assertIn("numeric_columns", features)
        self.assertIn("categorical_columns", features)
        self.assertIn("amount", features["numeric_columns"])
    
    def test_recommend_chart(self):
        """测试图表推荐"""
        # 注意：这个测试需要mock LLM调用
        # 这里测试默认值
        features = {"time_column": "date", "numeric_columns": ["amount"]}
        recommendation = self.agent._get_default_recommendation(features)
        
        self.assertIn("chart_type", recommendation)
    
    def test_generate_chart(self):
        """测试图表生成"""
        result = self.agent.generate_chart(
            data=self.test_data,
            chart_type="bar",
            title="测试图表",
            x_axis="region",
            y_axis="amount"
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result.saved)
        self.assertIsNotNone(result.file_path)
    
    def test_generate_invalid_chart_type(self):
        """测试无效图表类型"""
        result = self.agent.generate_chart(
            data=self.test_data,
            chart_type="invalid_type",
            title="测试图表"
        )
        
        # 应该降级到柱状图
        self.assertTrue(result.saved)
    
    def test_visualize(self):
        """测试完整可视化流程"""
        result = self.agent.visualize(
            query="显示各地区销售对比",
            data=self.test_data,
            chart_type="bar"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.chart_type, "bar")
        self.assertTrue(result.saved)


class TestVisualizationAgentIntegration(unittest.TestCase):
    """可视化Agent集成测试"""
    
    def test_full_visualization_flow(self):
        """测试完整可视化流程"""
        agent = VisualizationAgent(output_dir=tempfile.mkdtemp())
        
        # 模拟查询结果
        query_data = [
            {"region": "华东", "amount": 5000, "quantity": 50},
            {"region": "华南", "amount": 4500, "quantity": 45},
            {"region": "华北", "amount": 6000, "quantity": 60},
            {"region": "华西", "amount": 3000, "quantity": 30},
            {"region": "华中", "amount": 4000, "quantity": 40},
        ]
        
        result = agent.visualize(
            query="分析各地区销售数据",
            data=query_data
        )
        
        self.assertTrue(hasattr(result, 'chart_type'))
        self.assertTrue(hasattr(result, 'file_path'))
        self.assertTrue(result.saved)


if __name__ == '__main__':
    unittest.main()
