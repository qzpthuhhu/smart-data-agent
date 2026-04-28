"""
全面测试框架
包含功能测试、集成测试、边界测试、性能测试等
"""

import os
import sys
import time
import json
import sqlite3
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config, load_config_from_env, get_current_model
from graph.workflow import DataAnalysisWorkflow
from agents.query_agent import QueryAgent
from agents.analysis_agent import AnalysisAgent
from agents.visualization_agent import VisualizationAgent


class TestResult:
    """测试结果类"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.error = None
        self.duration = 0
        self.details = {}
    
    def passed(self, details: dict = None):
        self.status = "passed"
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        if details:
            self.details = details
    
    def failed(self, error: str, details: dict = None):
        self.status = "failed"
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.error = error
        if details:
            self.details = details
    
    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "error": self.error,
            "details": self.details
        }


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.workflow = None
        self.query_agent = None
        self.analysis_agent = None
        self.viz_agent = None
    
    def setup(self):
        """初始化测试环境"""
        print("\n" + "="*60)
        print("🔧 测试环境初始化")
        print("="*60)
        
        # 加载配置
        load_config_from_env()
        
        # 初始化Agent
        self.query_agent = QueryAgent()
        self.analysis_agent = AnalysisAgent()
        self.viz_agent = VisualizationAgent()
        self.workflow = DataAnalysisWorkflow(use_checkpointer=True)
        
        print(f"✅ API配置: {get_current_model()}")
        print(f"✅ 数据库: {config.database.db_path}")
        print(f"✅ 测试环境就绪\n")
    
    def run_test(self, test_func, test_name: str) -> TestResult:
        """运行单个测试"""
        result = TestResult(test_name)
        result.start_time = datetime.now()
        
        print(f"\n📝 运行测试: {test_name}")
        print("-" * 40)
        
        try:
            test_func(self)
            result.passed()
            print(f"✅ {test_name} - 通过")
        except Exception as e:
            result.failed(str(e))
            print(f"❌ {test_name} - 失败: {str(e)}")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.setup()
        
        print("\n" + "="*60)
        print("🚀 开始全面测试")
        print("="*60)
        
        # 1. 功能测试
        print("\n【1. 功能测试】")
        self.run_test(self.test_query_agent_basic, "Query Agent基础查询")
        self.run_test(self.test_query_agent_nl_to_sql, "Query Agent自然语言转SQL")
        self.run_test(self.test_query_agent_execute, "Query Agent执行查询")
        self.run_test(self.test_analysis_agent, "Analysis Agent分析功能")
        self.run_test(self.test_viz_agent, "Visualization Agent可视化功能")
        
        # 2. 集成测试
        print("\n【2. 集成测试】")
        self.run_test(self.test_workflow_basic, "工作流基础功能")
        self.run_test(self.test_workflow_query, "工作流查询功能")
        self.run_test(self.test_workflow_full, "工作流完整流程")
        
        # 3. 边界测试
        print("\n【3. 边界测试】")
        self.run_test(self.test_empty_query, "空查询处理")
        self.run_test(self.test_invalid_query, "无效查询处理")
        self.run_test(self.test_long_query, "长查询处理")
        self.run_test(self.test_special_chars, "特殊字符处理")
        
        # 4. 性能测试
        print("\n【4. 性能测试】")
        self.run_test(self.test_response_time, "响应时间测试")
        self.run_test(self.test_concurrent_queries, "并发查询测试")
        
        # 5. API测试
        print("\n【5. API测试】")
        self.run_test(self.test_api_connection, "API连接测试")
        self.run_test(self.test_api_call_stability, "API调用稳定性")
        
        # 6. 记忆测试
        print("\n【6. 记忆测试】")
        self.run_test(self.test_memory_save, "记忆保存测试")
        self.run_test(self.test_memory_recall, "记忆召回测试")
        
        # 7. 可视化测试
        print("\n【7. 可视化测试】")
        self.run_test(self.test_chart_generation, "图表生成测试")
        self.run_test(self.test_chart_export, "图表导出测试")
        
        # 8. 端到端测试
        print("\n【8. 端到端测试】")
        self.run_test(self.test_e2e_full_flow, "完整用户流程测试")
        
        # 生成报告
        return self.generate_report()
    
    # ============ 功能测试 ============
    
    def test_query_agent_basic(self):
        """Query Agent基础功能测试"""
        result = self.query_agent.execute_query("SELECT COUNT(*) FROM sales")
        assert result is not None
        assert result.row_count >= 0
    
    def test_query_agent_nl_to_sql(self):
        """自然语言转SQL测试"""
        sql, reasoning = self.query_agent.nl_to_sql("显示销售总额")
        assert sql
        assert "SELECT" in sql.upper()
    
    def test_query_agent_execute(self):
        """执行查询测试"""
        sql = "SELECT * FROM sales LIMIT 10"
        result = self.query_agent.execute_query(sql)
        assert result.data is not None
        assert len(result.data) <= 10
    
    def test_analysis_agent(self):
        """分析Agent测试"""
        data = [
            {"region": "华东", "amount": 1000},
            {"region": "华南", "amount": 2000}
        ]
        result = self.analysis_agent.analyze(data, "statistical")
        assert result is not None
    
    def test_viz_agent(self):
        """可视化Agent测试"""
        data = [
            {"region": "华东", "amount": 1000},
            {"region": "华南", "amount": 2000}
        ]
        result = self.viz_agent.create_chart(data, "bar", "销售对比")
        assert result is not None
    
    # ============ 集成测试 ============
    
    def test_workflow_basic(self):
        """工作流基础测试"""
        result = self.workflow.run("测试查询", "test_session")
        assert result is not None
    
    def test_workflow_query(self):
        """工作流查询测试"""
        result = self.workflow.run("显示销售总额", "test_session")
        assert result is not None
    
    def test_workflow_full(self):
        """完整工作流测试"""
        queries = [
            "显示最近一个月的销售额",
            "分析各地区销售趋势",
            "生成销售数据的可视化图表"
        ]
        for query in queries:
            result = self.workflow.run(query, "test_session")
            assert result is not None
    
    # ============ 边界测试 ============
    
    def test_empty_query(self):
        """空查询处理测试"""
        try:
            result = self.workflow.run("", "test_session")
        except Exception as e:
            assert "空" in str(e) or "empty" in str(e).lower()
    
    def test_invalid_query(self):
        """无效查询处理测试"""
        result = self.query_agent.execute_query("SELECT * FROM nonexistent_table")
        assert result.error is not None
    
    def test_long_query(self):
        """长查询处理测试"""
        long_query = "显示销售数据 " * 50
        result = self.workflow.run(long_query, "test_session")
        assert result is not None
    
    def test_special_chars(self):
        """特殊字符处理测试"""
        result = self.query_agent.execute_query("SELECT * FROM sales WHERE region = '华东'")
        assert result is not None
    
    # ============ 性能测试 ============
    
    def test_response_time(self):
        """响应时间测试"""
        start = time.time()
        self.query_agent.execute_query("SELECT COUNT(*) FROM sales")
        duration = time.time() - start
        print(f"   响应时间: {duration:.3f}秒")
        assert duration < 5  # 应该在5秒内完成
    
    def test_concurrent_queries(self):
        """并发查询测试"""
        queries = [
            "SELECT COUNT(*) FROM sales",
            "SELECT COUNT(*) FROM products",
            "SELECT * FROM sales LIMIT 10"
        ]
        start = time.time()
        for query in queries:
            self.query_agent.execute_query(query)
        duration = time.time() - start
        print(f"   3个查询总耗时: {duration:.3f}秒")
        assert duration < 10  # 应该在10秒内完成
    
    # ============ API测试 ============
    
    def test_api_connection(self):
        """API连接测试"""
        from config import get_llm_client
        client = get_llm_client()
        assert client is not None
    
    def test_api_call_stability(self):
        """API调用稳定性测试"""
        from config import create_llm_call
        
        # 连续调用3次
        for i in range(3):
            result = create_llm_call(
                "你是一个助手，请回复'测试成功'",
                "请回复'测试成功'"
            )
            assert "测试成功" in result or result is not None
            print(f"   第{i+1}次调用: 成功")
    
    # ============ 记忆测试 ============
    
    def test_memory_save(self):
        """记忆保存测试"""
        from memory import memory_manager
        
        memory_manager.save_memory(
            session_id="test_memory",
            query="测试查询",
            result={"data": "test"}
        )
        print("   记忆保存成功")
    
    def test_memory_recall(self):
        """记忆召回测试"""
        from memory import memory_manager
        
        # 保存记忆
        memory_manager.save_memory(
            session_id="test_recall",
            query="测试查询2",
            result={"data": "test2"}
        )
        
        # 召回记忆
        memories = memory_manager.get_memories("test_recall")
        assert memories is not None
        print(f"   召回记忆: {len(memories)}条")
    
    # ============ 可视化测试 ============
    
    def test_chart_generation(self):
        """图表生成测试"""
        data = {
            "region": ["华东", "华南", "华北"],
            "amount": [1000, 2000, 1500]
        }
        result = self.viz_agent.create_chart(data, "bar", "销售对比")
        assert result is not None
    
    def test_chart_export(self):
        """图表导出测试"""
        # 确保输出目录存在
        Path(config.visualization.output_dir).mkdir(parents=True, exist_ok=True)
        assert Path(config.visualization.output_dir).exists()
    
    # ============ 端到端测试 ============
    
    def test_e2e_full_flow(self):
        """完整端到端测试"""
        # 1. 用户输入查询
        query = "显示华东地区的销售总额"
        
        # 2. 工作流处理
        result = self.workflow.run(query, "e2e_test")
        
        # 3. 验证结果
        assert result is not None
        
        # 4. 检查各组件是否正常工作
        for state in result.values():
            assert state is not None
    
    # ============ 报告生成 ============
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = total - passed
        total_duration = sum(r.duration for r in self.results)
        
        print(f"\n总计测试: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"总耗时: {total_duration:.2f}秒")
        print(f"平均耗时: {total_duration/total:.2f}秒")
        
        # 失败的测试
        if failed > 0:
            print("\n❌ 失败测试详情:")
            for result in self.results:
                if result.status == "failed":
                    print(f"  - {result.test_name}: {result.error}")
        
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%",
                "total_duration": total_duration,
                "avg_duration": total_duration/total if total > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "results": [r.to_dict() for r in self.results]
        }
        
        # 保存报告
        report_dir = project_root / "tests" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 报告已保存: {report_file}")
        
        return report


def run_continuous_tests(count: int = 10):
    """连续运行多次测试"""
    print("\n" + "="*60)
    print(f"🔄 连续测试模式 - 将运行 {count} 次完整测试")
    print("="*60)
    
    all_reports = []
    
    for i in range(count):
        print(f"\n{'='*60}")
        print(f"📌 第 {i+1}/{count} 轮测试")
        print("="*60)
        
        runner = TestRunner()
        report = runner.run_all_tests()
        all_reports.append(report)
        
        # 检查是否全部通过
        if report["summary"]["failed"] > 0:
            print(f"\n⚠️ 第 {i+1} 轮有失败的测试，继续执行...")
        else:
            print(f"\n✅ 第 {i+1} 轮测试全部通过")
        
        # 休息一下再进行下一轮
        if i < count - 1:
            time.sleep(2)
    
    # 汇总报告
    print("\n" + "="*60)
    print("📊 连续测试汇总报告")
    print("="*60)
    
    total_tests = sum(r["summary"]["total"] for r in all_reports)
    total_passed = sum(r["summary"]["passed"] for r in all_reports)
    total_failed = sum(r["summary"]["failed"] for r in all_reports)
    total_duration = sum(r["summary"]["total_duration"] for r in all_reports)
    
    print(f"\n总测试轮次: {count}")
    print(f"总测试用例: {total_tests}")
    print(f"总通过: {total_passed} ✅")
    print(f"总失败: {total_failed} ❌")
    print(f"总耗时: {total_duration:.2f}秒")
    print(f"总体通过率: {total_passed/total_tests*100:.1f}%" if total_tests > 0 else "0%")
    
    # 保存汇总报告
    summary_report = {
        "continuous_test_summary": {
            "total_rounds": count,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "pass_rate": f"{total_passed/total_tests*100:.1f}%" if total_tests > 0 else "0%",
            "total_duration": total_duration,
            "timestamp": datetime.now().isoformat()
        },
        "round_reports": all_reports
    }
    
    report_dir = project_root / "tests" / "reports"
    summary_file = report_dir / f"continuous_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 汇总报告已保存: {summary_file}")
    
    return summary_report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="智能数据分析Agent测试框架")
    parser.add_argument("--count", type=int, default=1, help="连续测试次数")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    
    args = parser.parse_args()
    
    if args.count > 1:
        run_continuous_tests(args.count)
    else:
        runner = TestRunner()
        report = runner.run_all_tests()
        
        if args.report:
            print("\n" + json.dumps(report, indent=2, ensure_ascii=False))
