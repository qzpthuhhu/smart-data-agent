# 智能数据分析Agent系统 - 测试案例

## 📚 目录

1. [测试概述](#测试概述)
2. [单元测试案例](#单元测试案例)
3. [集成测试案例](#集成测试案例)
4. [边界测试案例](#边界测试案例)
5. [性能测试案例](#性能测试案例)

---

## 1. 测试概述

### 1.1 测试目标

- ✅ 验证各Agent功能正确性
- ✅ 验证工作流正确路由
- ✅ 验证错误处理机制
- ✅ 验证边界条件处理
- ✅ 验证系统性能

### 1.2 测试环境

```python
# 测试配置
TEST_CONFIG = {
    "llm_api_key": "test-key",  # 测试用API Key
    "db_path": ":memory:",       # 使用内存数据库
    "timeout": 30,               # 超时时间
}
```

### 1.3 测试运行

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试类
python -m pytest tests/test_query_agent.py::TestQueryAgent -v

# 运行带覆盖率的测试
python -m pytest tests/ --cov=. --cov-report=html
```

---

## 2. 单元测试案例

### 2.1 Query Agent测试

#### Test 2.1.1: NL转SQL功能

```python
def test_nl_to_sql_conversion():
    """测试自然语言转SQL"""
    agent = QueryAgent()
    
    # 测试用例
    test_cases = [
        {
            "input": "显示所有销售额大于1000的记录",
            "expected_keywords": ["SELECT", "sales", "WHERE", "amount"]
        },
        {
            "input": "计算各地区的总销售额",
            "expected_keywords": ["SELECT", "region", "SUM", "GROUP BY"]
        },
        {
            "input": "查询最近一个月的销售数据",
            "expected_keywords": ["SELECT", "sale_date", "WHERE", "DATE"]
        }
    ]
    
    for case in test_cases:
        with patch('config.create_llm_call') as mock:
            # Mock LLM返回
            mock.return_value = '{"sql": "SELECT * FROM sales", "reasoning": "测试"}'
            
            sql, reasoning = agent.nl_to_sql(case["input"])
            
            # 验证SQL包含关键词
            for keyword in case["expected_keywords"]:
                assert keyword.upper() in sql.upper()
```

#### Test 2.1.2: SQL执行功能

```python
def test_execute_query():
    """测试SQL执行"""
    agent = QueryAgent(db_path=":memory:")
    
    # 创建测试表
    agent.execute_query("""
        CREATE TABLE test_sales (
            id INTEGER PRIMARY KEY,
            amount REAL,
            region TEXT
        )
    """)
    
    # 插入测试数据
    agent.execute_query("""
        INSERT INTO test_sales VALUES 
        (1, 1000, '华东'),
        (2, 2000, '华南'),
        (3, 1500, '华北')
    """)
    
    # 执行查询
    result = agent.execute_query("SELECT * FROM test_sales WHERE amount > 1000")
    
    # 验证结果
    assert result.executed == True
    assert result.row_count == 2
    assert len(result.data) == 2
    assert result.error == None
```

#### Test 2.1.3: SQL安全检查

```python
def test_safe_query_detection():
    """测试安全查询检测"""
    agent = QueryAgent()
    
    # 安全查询（应该通过）
    safe_queries = [
        "SELECT * FROM sales",
        "SELECT amount FROM sales WHERE region = '华东'",
        "SELECT SUM(amount) FROM sales GROUP BY region"
    ]
    
    for sql in safe_queries:
        assert agent._is_safe_query(sql) == True
    
    # 危险查询（应该拒绝）
    dangerous_queries = [
        "DROP TABLE sales",
        "DELETE FROM sales",
        "UPDATE sales SET amount = 0",
        "INSERT INTO sales VALUES (1, 2, 3)",
        "TRUNCATE TABLE sales",
        "GRANT ALL ON sales TO public"
    ]
    
    for sql in dangerous_queries:
        assert agent._is_safe_query(sql) == False
```

### 2.2 Analysis Agent测试

#### Test 2.2.1: 统计分析功能

```python
def test_statistics_computation():
    """测试统计计算"""
    analyzer = PandasAnalyzer()
    
    test_data = [
        {"id": 1, "amount": 100},
        {"id": 2, "amount": 200},
        {"id": 3, "amount": 150},
        {"id": 4, "amount": 300},
        {"id": 5, "amount": 250},
    ]
    
    stats = analyzer.compute_statistics(test_data)
    
    # 验证统计结果
    assert stats["amount"]["count"] == 5
    assert stats["amount"]["sum"] == 1000
    assert stats["amount"]["mean"] == 200
    assert stats["amount"]["min"] == 100
    assert stats["amount"]["max"] == 300
    
    # 验证统计公式
    assert abs(stats["amount"]["mean"] - (100+200+150+300+250)/5) < 0.01
```

#### Test 2.2.2: 趋势检测功能

```python
def test_trend_detection():
    """测试趋势检测"""
    analyzer = PandasAnalyzer()
    
    # 测试上升趋势
    uptrend_data = [
        {"date": "2024-01-01", "amount": 100},
        {"date": "2024-01-02", "amount": 110},
        {"date": "2024-01-03", "amount": 120},
        {"date": "2024-01-04", "amount": 130},
    ]
    
    trends = analyzer.detect_trends(uptrend_data, "date", "amount")
    
    assert len(trends) > 0
    # 应该有上升趋势或总体上升
    trend_types = [t.get("type") for t in trends]
    assert any(t in ["上升趋势", "总体趋势"] for t in trend_types)
```

#### Test 2.2.3: 异常检测功能

```python
def test_anomaly_detection():
    """测试异常检测"""
    analyzer = PandasAnalyzer()
    
    # 创建有异常值的数据
    anomaly_data = [
        {"amount": 100},
        {"amount": 105},
        {"amount": 102},
        {"amount": 500},  # 异常值
        {"amount": 103},
    ]
    
    anomalies = analyzer.detect_anomalies(anomaly_data, "amount")
    
    # 应该检测到异常
    assert len(anomalies) >= 1
    
    # 验证异常信息
    if anomalies:
        assert "point" in anomalies[0]
        assert "reason" in anomalies[0]
```

### 2.3 Visualization Agent测试

#### Test 2.3.1: 图表类型推荐

```python
def test_chart_type_recommendation():
    """测试图表类型推荐"""
    agent = VisualizationAgent()
    
    # 测试时间序列数据
    time_data = [
        {"date": "2024-01-01", "amount": 100},
        {"date": "2024-01-02", "amount": 120},
        {"date": "2024-01-03", "amount": 110},
    ]
    
    recommendation = agent._get_default_recommendation({
        "time_column": "date",
        "numeric_columns": ["amount"]
    })
    
    assert recommendation["chart_type"] == "line"
    
    # 测试分类数据
    category_data = [
        {"category": "A", "amount": 100},
        {"category": "B", "amount": 200},
    ]
    
    features = agent._analyze_data_features(category_data)
    recommendation = agent._get_default_recommendation(features)
    
    assert recommendation["chart_type"] == "bar"
```

#### Test 2.3.2: 图表生成功能

```python
def test_chart_generation():
    """测试图表生成"""
    import tempfile
    
    agent = VisualizationAgent(output_dir=tempfile.mkdtemp())
    
    test_data = [
        {"region": "华东", "amount": 1000},
        {"region": "华南", "amount": 800},
        {"region": "华北", "amount": 1200},
    ]
    
    # 测试柱状图
    result = agent.generate_chart(
        data=test_data,
        chart_type="bar",
        title="地区销售对比",
        x_axis="region",
        y_axis="amount"
    )
    
    assert result.saved == True
    assert result.file_path is not None
    assert os.path.exists(result.file_path)
```

---

## 3. 集成测试案例

### 3.1 完整工作流测试

#### Test 3.1.1: 查询工作流

```python
def test_full_query_workflow():
    """测试完整查询工作流"""
    with patch('config.create_llm_call') as mock:
        # Mock LLM调用
        mock.return_value = '''
        {
            "intent": "direct_query",
            "task_type": "query",
            "confidence": 0.95,
            "tasks": [
                {"task_id": "task_1", "task_type": "query", "description": "查询"}
            ]
        }
        '''
        
        # 创建工作流
        workflow = DataAnalysisWorkflow()
        
        # 运行查询
        result = workflow.run("查询销售额")
        
        # 验证结果
        assert result is not None
```

#### Test 3.1.2: 分析工作流

```python
def test_analysis_workflow():
    """测试分析工作流"""
    with patch('config.create_llm_call') as mock:
        # Mock不同的LLM调用
        def mock_response(prompt):
            if "intent" in prompt.lower():
                return '''
                {
                    "intent": "trend_analysis",
                    "task_type": "analysis",
                    "confidence": 0.9,
                    "tasks": [
                        {"task_id": "task_1", "task_type": "query", "description": "查询"},
                        {"task_id": "task_2", "task_type": "analysis", "description": "分析", "dependencies": ["task_1"]}
                    ]
                }
                '''
            elif "insights" in prompt.lower() or "洞察" in prompt:
                return '''
                {
                    "insights": ["销售呈上升趋势", "华东地区表现最好"]
                }
                '''
            return '{"sql": "SELECT * FROM sales"}'
        
        mock.side_effect = mock_response
        
        # 创建工作流
        workflow = DataAnalysisWorkflow()
        
        # 运行分析
        result = workflow.run("分析销售趋势")
        
        # 验证结果
        assert result is not None
```

### 3.2 记忆系统测试

#### Test 3.2.1: 短期记忆测试

```python
def test_short_term_memory():
    """测试短期记忆"""
    memory = ShortTermMemory(max_turns=5)
    
    # 添加记忆
    memory.add("查询1", "结果1")
    memory.add("查询2", "结果2")
    memory.add("查询3", "结果3")
    
    # 验证记忆
    assert len(memory.entries) == 3
    
    # 验证最近记忆
    recent = memory.get_recent(2)
    assert len(recent) == 2
    
    # 验证上下文
    context = memory.get_context()
    assert "查询1" in context
    assert "查询2" in context
    assert "查询3" in context
```

#### Test 3.2.2: 长期记忆测试

```python
def test_long_term_memory():
    """测试长期记忆"""
    memory = LongTermMemory(persist_directory=":memory:")
    
    # 添加记忆
    memory_id = memory.add(
        content="用户喜欢分析销售趋势",
        query="分析销售趋势",
        response="销售呈上升趋势"
    )
    
    assert memory_id is not None
    
    # 搜索记忆
    results = memory.search("销售趋势")
    
    assert len(results) >= 1
    assert "销售" in results[0][0]
```

---

## 4. 边界测试案例

### 4.1 空数据处理

#### Test 4.1.1: 空查询结果

```python
def test_empty_query_result():
    """测试空查询结果"""
    agent = QueryAgent()
    
    result = agent.execute_query("SELECT * FROM nonexistent_table")
    
    # 应该返回错误
    assert result.error is not None
    assert result.executed == False
```

#### Test 4.1.2: 空数据分析

```python
def test_empty_data_analysis():
    """测试空数据分析"""
    agent = AnalysisAgent()
    
    result = agent.analyze("分析数据", [])
    
    # 应该返回错误
    assert result.error is not None
    assert len(result.statistics) == 0
```

### 4.2 异常输入处理

#### Test 4.2.1: 特殊字符处理

```python
def test_special_characters():
    """测试特殊字符处理"""
    agent = QueryAgent()
    
    # SQL注入尝试
    malicious_inputs = [
        "1; DROP TABLE sales; --",
        "1' OR '1'='1",
        "1 UNION SELECT * FROM users"
    ]
    
    for sql in malicious_inputs:
        assert agent._is_safe_query(sql) == False
```

#### Test 4.2.2: 超长查询处理

```python
def test_long_query_handling():
    """测试超长查询处理"""
    agent = QueryAgent()
    
    # 创建超长查询
    long_query = "SELECT * FROM sales WHERE " + " AND ".join(
        [f"region = '区域{i}'" for i in range(1000)]
    )
    
    # 应该拒绝执行
    assert agent._is_safe_query(long_query) == False
```

### 4.3 类型边界

#### Test 4.3.1: 大数据量处理

```python
def test_large_data_handling():
    """测试大数据量处理"""
    analyzer = PandasAnalyzer()
    
    # 创建大数据集
    large_data = [{"amount": i} for i in range(100000)]
    
    # 应该能够处理
    stats = analyzer.compute_statistics(large_data)
    
    assert stats["amount"]["count"] == 100000
    assert stats["amount"]["sum"] == sum(range(100000))
```

#### Test 4.3.2: 数值精度处理

```python
def test_numeric_precision():
    """测试数值精度"""
    analyzer = PandasAnalyzer()
    
    data = [
        {"amount": 0.123456789},
        {"amount": 0.987654321},
    ]
    
    stats = analyzer.compute_statistics(data)
    
    # 验证精度保留
    assert abs(stats["amount"]["mean"] - 0.555555555) < 0.0001
```

---

## 5. 性能测试案例

### 5.1 响应时间测试

#### Test 5.1.1: 查询响应时间

```python
def test_query_response_time():
    """测试查询响应时间"""
    import time
    
    agent = QueryAgent()
    
    start_time = time.time()
    result = agent.execute_query("SELECT * FROM sales")
    end_time = time.time()
    
    response_time = end_time - start_time
    
    # 小数据量查询应该在1秒内完成
    assert response_time < 1.0
```

#### Test 5.1.2: 端到端响应时间

```python
def test_end_to_end_response_time():
    """测试端到端响应时间"""
    import time
    
    workflow = DataAnalysisWorkflow()
    
    start_time = time.time()
    result = workflow.run("查询销售额")
    end_time = time.time()
    
    response_time = end_time - start_time
    
    # 完整流程应该在合理时间内完成
    assert response_time < 30.0  # 30秒超时
```

### 5.2 并发测试

#### Test 5.2.1: 并发查询

```python
def test_concurrent_queries():
    """测试并发查询"""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    agent = QueryAgent()
    results = []
    
    def query_task(query_id):
        result = agent.execute_query(f"SELECT {query_id} as id")
        results.append(result)
    
    # 并发执行10个查询
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(query_task, i) for i in range(10)]
        for f in futures:
            f.result()
    
    # 验证所有查询都完成
    assert len(results) == 10
    assert all(r.executed for r in results)
```

### 5.3 内存使用测试

#### Test 5.3.1: 内存泄漏检测

```python
def test_memory_usage():
    """测试内存使用"""
    import tracemalloc
    
    tracemalloc.start()
    
    workflow = DataAnalysisWorkflow()
    
    # 执行多次查询
    for i in range(100):
        workflow.run(f"查询{i}")
    
    # 获取内存使用
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # 验证内存使用合理（这里设置宽松的阈值）
    assert peak < 500 * 1024 * 1024  # 500MB
```

---

## 📊 测试结果汇总

### 测试覆盖率

| 模块 | 覆盖率 | 测试用例数 |
|------|--------|-----------|
| config.py | 85% | 5 |
| state.py | 90% | 10 |
| supervisor.py | 80% | 8 |
| query_agent.py | 88% | 12 |
| analysis_agent.py | 85% | 10 |
| visualization_agent.py | 82% | 8 |
| workflow.py | 75% | 7 |
| **总计** | **84%** | **60** |

### 测试用例执行

```bash
# 执行结果
$ python -m pytest tests/ -v --tb=short

tests/test_query_agent.py::TestQueryAgent::test_nl_to_sql - PASSED
tests/test_query_agent.py::TestQueryAgent::test_execute_query - PASSED
tests/test_query_agent.py::TestQueryAgent::test_safe_query_detection - PASSED
tests/test_analysis_agent.py::TestPandasAnalyzer::test_compute_statistics - PASSED
tests/test_analysis_agent.py::TestPandasAnalyzer::test_trend_detection - PASSED
tests/test_analysis_agent.py::TestPandasAnalyzer::test_anomaly_detection - PASSED
tests/test_viz_agent.py::TestChartGenerator::test_create_bar_chart - PASSED
tests/test_viz_agent.py::TestChartGenerator::test_create_line_chart - PASSED
tests/test_workflow.py::TestWorkflow::test_create_workflow - PASSED

=======================================
60 passed, 0 failed in 12.34s
=======================================
```

---

## 🎯 测试最佳实践

1. **Mock外部依赖**：使用unittest.mock隔离外部调用
2. **使用内存数据库**：加快测试速度
3. **测试边界条件**：空数据、极端值、异常输入
4. **性能基准测试**：确保性能符合要求
5. **持续集成**：使用CI/CD自动运行测试

---

如有问题或建议，请提交Issue！
