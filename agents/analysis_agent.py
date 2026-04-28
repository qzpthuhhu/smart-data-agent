"""
Analysis Agent模块
负责统计分析、趋势检测、异常发现
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from datetime import datetime
import re

from config import config, create_llm_call
from graph.state import AnalysisResult


# ============ 提示词模板 ============

ANALYSIS_SYSTEM_PROMPT = """你是一个数据分析专家，擅长从数据中发现洞察和趋势。你的任务是：

1. **统计分析**：计算均值、方差、总和、计数等
2. **趋势检测**：识别数据的变化趋势
3. **异常发现**：找出数据中的异常点
4. **洞察生成**：从数据中提炼有价值的见解

## 分析方法：
- 描述性统计：均值、中位数、众数、标准差等
- 时间序列分析：趋势线、增长率、季节性模式
- 异常检测：基于统计方法（3σ原则）或业务规则
- 对比分析：与目标值、历史值、竞品对比

## 输出格式：
请严格按照以下JSON格式输出：
```json
{
    "statistics": {
        "key_metric": value,
        ...
    },
    "trends": [
        {
            "type": "趋势类型",
            "description": "趋势描述",
            "data_points": []
        }
    ],
    "anomalies": [
        {
            "point": "异常点描述",
            "reason": "原因分析",
            "severity": "high/medium/low"
        }
    ],
    "insights": [
        "洞察点1",
        "洞察点2"
    ]
}
```
"""


ANALYSIS_PROMPT = """请分析以下数据，生成洞察和报告。

## 用户查询：
{query}

## 数据：
{data}

## 上下文摘要：
{context_summary}

请生成JSON格式的分析结果。"""


class PandasAnalyzer:
    """
    Pandas分析工具
    提供基础的数据分析功能
    """
    
    def __init__(self):
        """初始化分析器"""
        import pandas as pd
        self.pd = pd
    
    def compute_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """
        计算统计指标
        
        Args:
            data: 数据列表
            
        Returns:
            统计指标字典
        """
        if not data:
            return {}
        
        df = self.pd.DataFrame(data)
        stats = {}
        
        # 数值型列的统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            stats[col] = {
                "count": int(df[col].count()),
                "mean": round(df[col].mean(), 2),
                "median": round(df[col].median(), 2),
                "std": round(df[col].std(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "sum": round(df[col].sum(), 2)
            }
        
        # 分类型列的统计
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            value_counts = df[col].value_counts().head(10)
            stats[col] = {
                "unique_count": int(df[col].nunique()),
                "top_values": {
                    str(k): int(v) for k, v in value_counts.items()
                }
            }
        
        return stats
    
    def detect_trends(self, data: List[Dict], time_col: str, value_col: str) -> List[Dict]:
        """
        检测趋势
        
        Args:
            data: 数据列表
            time_col: 时间列名
            value_col: 数值列名
            
        Returns:
            趋势列表
        """
        if not data or time_col not in data[0] or value_col not in data[0]:
            return []
        
        df = self.pd.DataFrame(data)
        
        try:
            # 转换时间列
            df[time_col] = self.pd.to_datetime(df[time_col])
            df = df.sort_values(time_col)
            
            # 计算移动平均
            df['ma_7'] = df[value_col].rolling(window=7, min_periods=1).mean()
            df['ma_30'] = df[value_col].rolling(window=30, min_periods=1).mean()
            
            # 计算增长率
            df['growth_rate'] = df[value_col].pct_change() * 100
            
            # 简单趋势判断
            first_half_mean = df[value_col].iloc[:len(df)//2].mean()
            second_half_mean = df[value_col].iloc[len(df)//2:].mean()
            
            trends = []
            
            if second_half_mean > first_half_mean * 1.1:
                trends.append({
                    "type": "上升趋势",
                    "description": f"后半段均值({second_half_mean:.2f})相比前半段({first_half_mean:.2f})有明显上升",
                    "growth_percentage": round((second_half_mean - first_half_mean) / first_half_mean * 100, 2)
                })
            elif second_half_mean < first_half_mean * 0.9:
                trends.append({
                    "type": "下降趋势",
                    "description": f"后半段均值({second_half_mean:.2f})相比前半段({first_half_mean:.2f})有明显下降",
                    "decline_percentage": round((first_half_mean - second_half_mean) / first_half_mean * 100, 2)
                })
            else:
                trends.append({
                    "type": "平稳趋势",
                    "description": "数据整体较为平稳，无明显趋势变化"
                })
            
            # 计算总趋势
            if len(df) >= 2:
                first_value = df[value_col].iloc[0]
                last_value = df[value_col].iloc[-1]
                if last_value > first_value:
                    overall_trend = "上升"
                    change_pct = round((last_value - first_value) / first_value * 100, 2)
                elif last_value < first_value:
                    overall_trend = "下降"
                    change_pct = round((first_value - last_value) / first_value * 100, 2)
                else:
                    overall_trend = "持平"
                    change_pct = 0
                
                trends.append({
                    "type": "总体趋势",
                    "description": f"从期初到期末，{value_col}整体{overall_trend}",
                    "change_percentage": change_pct
                })
            
            return trends
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def detect_anomalies(self, data: List[Dict], value_col: str) -> List[Dict]:
        """
        检测异常点（基于3σ原则）
        
        Args:
            data: 数据列表
            value_col: 数值列名
            
        Returns:
            异常点列表
        """
        if not data or value_col not in data[0]:
            return []
        
        df = self.pd.DataFrame(data)
        
        try:
            mean = df[value_col].mean()
            std = df[value_col].std()
            
            # 标记异常点
            anomalies = []
            
            for idx, row in df.iterrows():
                value = row[value_col]
                z_score = abs((value - mean) / std) if std > 0 else 0
                
                if z_score > 3:
                    anomalies.append({
                        "point": f"索引{idx}: {value_col}={value}",
                        "reason": f"偏离均值{mean:.2f}超过3个标准差(std={std:.2f})",
                        "severity": "high",
                        "z_score": round(z_score, 2)
                    })
                elif z_score > 2:
                    anomalies.append({
                        "point": f"索引{idx}: {value_col}={value}",
                        "reason": f"偏离均值{mean:.2f}超过2个标准差",
                        "severity": "medium",
                        "z_score": round(z_score, 2)
                    })
            
            return anomalies
            
        except Exception as e:
            return [{"error": str(e)}]


class AnalysisAgent:
    """
    Analysis Agent
    
    核心职责：
    - 统计分析：计算各种统计指标
    - 趋势检测：识别数据趋势
    - 异常发现：发现数据中的异常点
    - 洞察生成：提炼有价值的见解
    """
    
    def __init__(self):
        """初始化Analysis Agent"""
        self.system_prompt = ANALYSIS_SYSTEM_PROMPT
        self.pandas_analyzer = PandasAnalyzer()
        self.max_retries = 3
    
    def analyze(
        self,
        query: str,
        data: List[Dict],
        context_summary: str = ""
    ) -> AnalysisResult:
        """
        执行数据分析
        
        Args:
            query: 用户查询
            data: 查询到的数据
            context_summary: 上下文摘要
            
        Returns:
            AnalysisResult对象
        """
        result = AnalysisResult()
        
        if not data:
            result.error = "没有数据可供分析"
            return result
        
        try:
            # 自动统计分析
            result.statistics = self.pandas_analyzer.compute_statistics(data)
            
            # 检测趋势（如果有时间列和数值列）
            time_col = self._find_time_column(data)
            value_col = self._find_value_column(data)
            
            if time_col and value_col:
                result.trends = self.pandas_analyzer.detect_trends(data, time_col, value_col)
            
            # 检测异常
            if value_col:
                result.anomalies = self.pandas_analyzer.detect_anomalies(data, value_col)
            
            # LLM生成洞察
            insights = self._generate_insights(query, data, context_summary)
            result.insights = insights
            
        except Exception as e:
            result.error = f"分析过程出错: {str(e)}"
        
        return result
    
    def _find_time_column(self, data: List[Dict]) -> Optional[str]:
        """查找时间列"""
        time_keywords = ["date", "time", "day", "month", "year", "period"]
        
        if not data:
            return None
        
        first_row = data[0]
        for key in first_row.keys():
            key_lower = key.lower()
            if any(kw in key_lower for kw in time_keywords):
                return key
        
        return None
    
    def _find_value_column(self, data: List[Dict]) -> Optional[str]:
        """查找数值列"""
        if not data:
            return None
        
        first_row = data[0]
        for key, value in first_row.items():
            if isinstance(value, (int, float)):
                return key
        
        return None
    
    def _generate_insights(
        self,
        query: str,
        data: List[Dict],
        context_summary: str
    ) -> List[str]:
        """
        使用LLM生成洞察
        
        Args:
            query: 用户查询
            data: 数据
            context_summary: 上下文摘要
            
        Returns:
            洞察列表
        """
        prompt = ANALYSIS_PROMPT.format(
            query=query,
            data=json.dumps(data[:50], ensure_ascii=False, indent=2),  # 限制数据量
            context_summary=context_summary or "无"
        )
        
        for attempt in range(self.max_retries):
            try:
                response = create_llm_call(
                    system_prompt=self.system_prompt,
                    user_prompt=prompt,
                    temperature=0.7
                )
                
                # 解析JSON响应
                result = self._parse_json_response(response)
                if result and result.get("insights"):
                    return result["insights"]
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # 返回自动生成的简单洞察
                    return self._generate_fallback_insights(data)
                continue
        
        return self._generate_fallback_insights(data)
    
    def _generate_fallback_insights(self, data: List[Dict]) -> List[str]:
        """生成降级洞察"""
        insights = []
        
        if not data:
            return ["数据为空，无法生成洞察"]
        
        # 简单的洞察生成
        insights.append(f"共分析了 {len(data)} 条数据记录")
        
        # 数值列洞察
        value_col = self._find_value_column(data)
        if value_col:
            values = [row.get(value_col, 0) for row in data if isinstance(row.get(value_col), (int, float))]
            if values:
                insights.append(f"{value_col} 均值为 {sum(values)/len(values):.2f}")
                insights.append(f"{value_col} 范围为 {min(values):.2f} 到 {max(values):.2f}")
        
        # 分类型洞察
        for key in data[0].keys():
            if isinstance(data[0][key], str) and key not in [value_col, self._find_time_column(data)]:
                unique_values = set(row.get(key) for row in data)
                if len(unique_values) <= 10:
                    insights.append(f"{key} 共有 {len(unique_values)} 种不同值")
        
        return insights[:5]  # 限制洞察数量
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析JSON响应"""
        try:
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            return eval(json_str)
            
        except Exception:
            return None


# 创建全局实例
analysis_agent = AnalysisAgent()


def analysis_agent_node(state) -> Dict[str, Any]:
    """
    Analysis Agent的LangGraph节点函数
    
    Args:
        state: 当前状态
        
    Returns:
        要更新的状态字典
    """
    # 获取查询结果
    query_result = state.get("query_result")
    
    if not query_result or not query_result.data:
        state["analysis_result"] = AnalysisResult(error="没有数据可供分析")
        state["next_agent"] = AgentName.TERMINATE
        return state
    
    # 记录开始
    state["intermediate_steps"].append({
        "agent": "analysis_agent",
        "action": "开始数据分析",
        "data_rows": len(query_result.data)
    })
    
    # 执行分析
    result = analysis_agent.analyze(
        query=state["user_query"],
        data=query_result.data,
        context_summary=state.get("context_summary", "")
    )
    
    # 记录完成
    state["intermediate_steps"].append({
        "agent": "analysis_agent",
        "action": "完成数据分析",
        "statistics_keys": list(result.statistics.keys()) if result.statistics else [],
        "insights_count": len(result.insights)
    })
    
    # 更新状态
    state["analysis_result"] = result
    
    # 确定下一个Agent
    tasks = state.get("tasks", [])
    current_task_id = state.get("current_task_id", "")
    
    current_idx = -1
    for i, task in enumerate(tasks):
        if task.task_id == current_task_id:
            current_idx = i
            break
    
    if current_idx >= 0 and current_idx < len(tasks) - 1:
        next_task = tasks[current_idx + 1]
        tasks[current_idx].status = "completed"
        state["tasks"] = tasks
        state["current_task_id"] = next_task.task_id
        
        if next_task.task_type == TaskType.VISUALIZATION:
            state["next_agent"] = AgentName.VISUALIZATION
        else:
            state["next_agent"] = AgentName.TERMINATE
    else:
        state["next_agent"] = AgentName.TERMINATE
    
    return state


# 导入AgentName和TaskType
from graph.state import AgentName, TaskType
