"""
Query Agent模块
负责自然语言转SQL、执行查询、返回结构化数据
"""

import sqlite3
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from pathlib import Path

from config import config, create_llm_call
from graph.state import QueryResult


# ============ 提示词模板 ============

QUERY_AGENT_SYSTEM_PROMPT = """你是一个数据分析专家，精通SQL查询。你的任务是将自然语言查询转换为SQL语句。

## 数据库信息：
- 数据库类型：SQLite
- 示例表结构：

### sales表（销售数据）
- id: INTEGER PRIMARY KEY - 记录ID
- product_id: INTEGER - 产品ID
- amount: REAL - 销售金额
- quantity: INTEGER - 销售数量
- sale_date: TEXT - 销售日期（格式：YYYY-MM-DD）
- region: TEXT - 销售地区

### products表（产品信息）
- id: INTEGER PRIMARY KEY - 产品ID
- name: TEXT - 产品名称
- category: TEXT - 产品类别
- price: REAL - 产品价格
- cost: REAL - 产品成本

## SQL转换规则：
1. 始终使用清晰的表别名
2. 使用参数化查询防止SQL注入（如果需要动态值）
3. 注意日期格式转换
4. 使用合适的聚合函数
5. 添加必要的WHERE条件
6. 结果按需要的维度排序

## 输出格式：
请严格按照以下JSON格式输出：
```json
{
    "sql": "SELECT ... FROM ... WHERE ...",
    "reasoning": "转换逻辑说明"
}
```

注意：只输出JSON，不要包含其他文字。"""


QUERY_EXECUTION_PROMPT = """你是一个数据分析专家。请评估以下SQL查询是否可以安全执行。

SQL: {sql}

请判断：
1. 是否是SELECT语句（只读查询）
2. 是否有潜在的危险操作（DROP, DELETE, UPDATE, INSERT等）
3. 是否语法正确

输出JSON格式：
```json
{
    "safe": true/false,
    "can_execute": true/false,
    "reason": "判断理由"
}
```"""


class QueryAgent:
    """
    Query Agent
    
    核心职责：
    - 自然语言转SQL
    - SQL安全性检查
    - 执行数据库查询
    - 返回结构化数据
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化Query Agent
        
        Args:
            db_path: 数据库路径，默认使用配置中的路径
        """
        self.db_path = db_path or config.database.db_path
        self.system_prompt = QUERY_AGENT_SYSTEM_PROMPT
        self.max_retries = config.agent.query_max_retries
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库存在"""
        db_file = Path(self.db_path)
        if not db_file.exists():
            # 如果数据库不存在，创建一个示例数据库
            self._create_sample_database()
    
    def _create_sample_database(self):
        """创建示例数据库"""
        from datetime import datetime, timedelta
        import random
        
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建products表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                cost REAL NOT NULL
            )
        """)
        
        # 创建sales表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                quantity INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                region TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # 插入示例产品数据
        products = [
            (1, "iPhone 15", "电子产品", 6999, 5500),
            (2, "MacBook Pro", "电子产品", 12999, 10000),
            (3, "AirPods Pro", "电子产品", 1899, 1400),
            (4, "iPad Air", "电子产品", 4799, 3600),
            (5, "运动T恤", "服装", 199, 80),
            (6, "运动裤", "服装", 299, 120),
            (7, "运动鞋", "服装", 799, 400),
            (8, "瑜伽垫", "健身", 99, 40),
            (9, "蛋白粉", "营养品", 299, 150),
            (10, "咖啡机", "家电", 599, 350),
        ]
        cursor.executemany(
            "INSERT OR REPLACE INTO products (id, name, category, price, cost) VALUES (?, ?, ?, ?, ?)",
            products
        )
        
        # 生成最近6个月的销售数据
        base_date = datetime.now()
        regions = ["华东", "华南", "华北", "华西", "华中"]
        
        sales_data = []
        for i in range(500):  # 500条销售记录
            product_id = random.randint(1, 10)
            days_ago = random.randint(0, 180)  # 最近6个月内
            sale_date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            region = random.choice(regions)
            
            # 根据产品ID获取价格
            cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            quantity = random.randint(1, 10)
            # 销售金额可以有一定折扣波动
            discount = random.uniform(0.7, 1.0)
            amount = price * quantity * discount
            
            sales_data.append((product_id, amount, quantity, sale_date, region))
        
        cursor.executemany(
            "INSERT INTO sales (product_id, amount, quantity, sale_date, region) VALUES (?, ?, ?, ?, ?)",
            sales_data
        )
        
        conn.commit()
        conn.close()
    
    def nl_to_sql(self, query: str, context: Optional[Dict] = None) -> Tuple[str, str]:
        """
        自然语言转SQL
        
        Args:
            query: 自然语言查询
            context: 上下文信息（如之前的查询结果）
            
        Returns:
            (SQL语句, 推理过程)
        """
        # 构建提示
        prompt_parts = [f"请将以下自然语言查询转换为SQL：\n{query}\n"]
        
        if context:
            # 添加上下文信息
            if context.get("available_tables"):
                prompt_parts.append(f"\n可用表: {context['available_tables']}")
            if context.get("current_data"):
                prompt_parts.append(f"\n当前数据样本:\n{context['current_data']}")
        
        user_prompt = "\n".join(prompt_parts)
        
        for attempt in range(self.max_retries):
            try:
                response = create_llm_call(
                    system_prompt=self.system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.3  # 较低的随机性
                )
                
                # 解析JSON响应
                result = self._parse_json_response(response)
                if result and result.get("sql"):
                    return result["sql"], result.get("reasoning", "")
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"NL转SQL失败: {str(e)}")
                continue
        
        return "", "转换失败"
    
    def execute_query(self, sql: str) -> QueryResult:
        """
        执行SQL查询
        
        Args:
            sql: SQL语句
            
        Returns:
            QueryResult对象
        """
        result = QueryResult()
        start_time = time.time()
        
        # 安全性检查
        if not self._is_safe_query(sql):
            result.error = "SQL语句存在安全风险，已拒绝执行"
            return result
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 支持列名访问
            cursor = conn.cursor()
            
            # 执行查询
            cursor.execute(sql)
            
            # 获取结果
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 转换为字典列表
            data = [dict(zip(columns, row)) for row in rows]
            
            result.sql = sql
            result.executed = True
            result.data = data
            result.row_count = len(data)
            
            conn.close()
            
        except sqlite3.Error as e:
            result.error = f"数据库错误: {str(e)}"
            result.sql = sql
        except Exception as e:
            result.error = f"执行错误: {str(e)}"
            result.sql = sql
        finally:
            result.execution_time = time.time() - start_time
        
        return result
    
    def query(self, natural_query: str, context: Optional[Dict] = None) -> QueryResult:
        """
        执行完整查询流程
        
        Args:
            natural_query: 自然语言查询
            context: 上下文信息
            
        Returns:
            QueryResult对象
        """
        # NL转SQL
        sql, reasoning = self.nl_to_sql(natural_query, context)
        
        if not sql:
            return QueryResult(error=f"无法将查询转换为SQL: {reasoning}")
        
        # 执行查询
        result = self.execute_query(sql)
        result.sql = sql  # 确保SQL被记录
        
        return result
    
    def get_schema(self) -> str:
        """
        获取数据库Schema
        
        Returns:
            Schema描述字符串
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = cursor.fetchall()
            
            schema_parts = []
            for (table_name,) in tables:
                schema_parts.append(f"\n### {table_name}表")
                
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_id, name, col_type, notnull, default, pk = col
                    pk_str = " PRIMARY KEY" if pk else ""
                    schema_parts.append(f"- {name}: {col_type}{pk_str}")
                
                # 获取记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                schema_parts.append(f"- 记录数: {count}")
            
            conn.close()
            return "\n".join(schema_parts)
            
        except Exception as e:
            return f"获取Schema失败: {str(e)}"
    
    def get_sample_data(self, table: str, limit: int = 5) -> str:
        """
        获取示例数据
        
        Args:
            table: 表名
            limit: 返回行数
            
        Returns:
            示例数据字符串
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
            rows = cursor.fetchall()
            
            # 获取列名
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            conn.close()
            
            lines = [f"表: {table}"]
            lines.append("列: " + ", ".join(columns))
            lines.append("样本数据:")
            
            for row in rows:
                lines.append(str(row))
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"获取样本数据失败: {str(e)}"
    
    def _is_safe_query(self, sql: str) -> bool:
        """
        检查SQL安全性
        
        Args:
            sql: SQL语句
            
        Returns:
            是否安全
        """
        # 转换为小写进行匹配
        sql_lower = sql.lower().strip()
        
        # 检查是否以SELECT开头
        if not sql_lower.startswith("select"):
            return False
        
        # 检查危险关键词
        dangerous_keywords = [
            "drop ", "delete ", "update ", "insert ", "truncate ",
            "alter ", "create ", "grant ", "revoke ", "exec ",
            "execute ", "xp_", "sp_"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False
        
        return True
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析JSON响应
        
        Args:
            response: LLM响应文本
            
        Returns:
            解析后的字典
        """
        try:
            # 优先尝试提取```json块
            json_match = re.search(
                r'```json\s*([\s\S]*?)\s*```',
                response
            )
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有```json，尝试提取最后一个```块（通常是JSON）
                all_blocks = re.findall(r'```\w*\s*([\s\S]*?)\s*```', response)
                if all_blocks:
                    json_str = all_blocks[-1]  # 取最后一个块
                else:
                    json_str = response.strip()
            
            # 清理可能的注释和多余空格
            json_str = json_str.strip()
            
            # 尝试解析JSON
            import json
            try:
                return json.loads(json_str)
            except:
                # 如果JSON解析失败，尝试eval（更宽松）
                return eval(json_str)
            
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return None


# 创建全局实例
query_agent = QueryAgent()


def query_agent_node(state) -> Dict[str, Any]:
    """
    Query Agent的LangGraph节点函数
    
    Args:
        state: 当前状态
        
    Returns:
        要更新的状态字典
    """
    user_query = state["user_query"]
    
    # 记录开始
    state["intermediate_steps"].append({
        "agent": "query_agent",
        "action": "开始NL转SQL",
        "query": user_query
    })
    
    # 构建上下文
    context = {
        "available_tables": query_agent.get_schema()
    }
    
    # 执行查询
    result = query_agent.query(user_query, context)
    
    # 记录完成
    state["intermediate_steps"].append({
        "agent": "query_agent",
        "action": "完成查询",
        "executed": result.executed,
        "row_count": result.row_count,
        "sql": result.sql if result.executed else None,
        "error": result.error
    })
    
    # 更新状态
    state["query_result"] = result
    
    # 确定下一个Agent
    tasks = state.get("tasks", [])
    current_task_id = state.get("current_task_id", "")
    
    # 找到当前任务的索引
    current_idx = -1
    for i, task in enumerate(tasks):
        if task.task_id == current_task_id:
            current_idx = i
            break
    
    # 检查是否需要继续下一个任务
    if current_idx >= 0 and current_idx < len(tasks) - 1:
        next_task = tasks[current_idx + 1]
        
        # 更新当前任务状态
        tasks[current_idx].status = "completed"
        tasks[current_idx].result = asdict(result)
        state["tasks"] = tasks
        state["current_task_id"] = next_task.task_id
        
        # 根据下一个任务类型设置Agent
        if next_task.task_type == TaskType.ANALYSIS:
            state["next_agent"] = AgentName.ANALYSIS
        elif next_task.task_type == TaskType.VISUALIZATION:
            state["next_agent"] = AgentName.VISUALIZATION
        else:
            state["next_agent"] = AgentName.TERMINATE
    else:
        # 没有更多任务，整合结果
        state["next_agent"] = AgentName.TERMINATE
    
    return state


# 导入TaskType和AgentName
from graph.state import TaskType, AgentName
