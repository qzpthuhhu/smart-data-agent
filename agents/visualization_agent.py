"""
Visualization Agent模块
负责图表类型选择、图表生成、样式定制
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import random

from config import config, create_llm_call
from graph.state import VisualizationResult


# ============ 提示词模板 ============

VIZ_SYSTEM_PROMPT = """你是一个数据可视化专家，擅长选择最合适的图表类型来展示数据。

## 支持的图表类型：
1. **折线图 (line)**: 展示数据随时间变化的趋势
2. **柱状图 (bar)**: 对比不同类别的数值
3. **饼图 (pie)**: 展示各部分占整体的比例
4. **散点图 (scatter)**: 展示两个变量之间的关系
5. **面积图 (area)**: 展示累积数据的变化趋势
6. **热力图 (heatmap)**: 展示数据的分布密度

## 图表选择规则：
- 时间序列数据 -> 折线图或面积图
- 类别对比 -> 柱状图
- 比例分布 -> 饼图
- 关联关系 -> 散点图
- 多维度对比 -> 热力图或分组柱状图

## 输出格式：
请严格按照以下JSON格式输出：
```json
{
    "chart_type": "推荐的图表类型",
    "x_axis": "x轴字段名",
    "y_axis": "y轴字段名",
    "group_by": "分组字段（可选）",
    "title": "图表标题",
    "reasoning": "选择理由"
}
```
"""


VIZ_PROMPT = """根据以下信息，推荐合适的可视化方案。

## 用户查询：
{query}

## 数据样本：
{data}

## 数据特征：
{data_features}

请生成JSON格式的建议。"""


class ChartGenerator:
    """
    图表生成器
    使用Matplotlib生成各种图表
    """
    
    def __init__(self, style: str = None, figure_size: Tuple = None, dpi: int = None):
        """
        初始化图表生成器
        
        Args:
            style: 图表样式
            figure_size: 图形大小
            dpi: 分辨率
        """
        import matplotlib
        matplotlib.use('Agg')  # 使用非交互式后端
        import matplotlib.pyplot as plt
        
        self.plt = plt
        self.style = style or config.visualization.default_style
        self.figure_size = figure_size or config.visualization.figure_size
        self.dpi = dpi or config.visualization.dpi
        
        # 设置样式
        try:
            self.plt.style.use(self.style)
        except:
            self.plt.style.use('default')
    
    def _prepare_data(self, data: List[Dict]) -> Tuple[List, List, Optional[str]]:
        """
        准备图表数据
        
        Args:
            data: 原始数据
            
        Returns:
            (x值列表, y值列表, 分组字段)
        """
        if not data:
            return [], [], None
        
        first_row = data[0]
        x_col = None
        y_col = None
        group_col = None
        
        # 查找时间/类别列作为x轴
        time_keywords = ["date", "time", "day", "month", "year"]
        for key in first_row.keys():
            if any(kw in key.lower() for kw in time_keywords):
                x_col = key
                break
        
        # 查找数值列作为y轴
        for key, value in first_row.items():
            if isinstance(value, (int, float)) and key != x_col:
                y_col = key
                break
        
        # 如果没找到x列，使用索引
        if not x_col:
            x_col = "index"
        
        # 提取数据
        x_values = []
        y_values = []
        
        for i, row in enumerate(data):
            if x_col == "index":
                x_values.append(i)
            else:
                x_values.append(str(row.get(x_col, i)))
            
            if y_col:
                y_values.append(float(row.get(y_col, 0)))
            else:
                # 如果没有数值列，计数
                y_values.append(1)
        
        return x_values, y_values, x_col if x_col != "index" else None
    
    def _prepare_aggregate_data(
        self,
        data: List[Dict],
        group_col: str,
        value_col: str
    ) -> Tuple[List, List]:
        """
        准备聚合数据（用于柱状图、饼图）
        
        Args:
            data: 原始数据
            group_col: 分组列
            value_col: 数值列
            
        Returns:
            (类别列表, 数值列表)
        """
        if not data or not group_col or not value_col:
            return [], []
        
        # 聚合计算
        groups = {}
        for row in data:
            key = str(row.get(group_col, "未知"))
            value = float(row.get(value_col, 0))
            groups[key] = groups.get(key, 0) + value
        
        # 排序并限制数量
        sorted_groups = sorted(groups.items(), key=lambda x: x[1], reverse=True)
        
        # 限制显示数量
        max_items = 8
        if len(sorted_groups) > max_items:
            other_sum = sum(v for _, v in sorted_groups[max_items:])
            sorted_groups = sorted_groups[:max_items]
            if other_sum > 0:
                sorted_groups.append(("其他", other_sum))
        
        return [k for k, v in sorted_groups], [v for k, v in sorted_groups]
    
    def create_line_chart(
        self,
        data: List[Dict],
        title: str = "趋势图",
        x_label: str = "",
        y_label: str = "",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建折线图
        
        Args:
            data: 数据
            title: 标题
            x_label: x轴标签
            y_label: y轴标签
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        x_values, y_values, x_col = self._prepare_data(data)
        
        if not y_values:
            raise ValueError("没有有效数据")
        
        fig, ax = self.plt.subplots(figsize=self.figure_size)
        
        ax.plot(x_values, y_values, marker='o', linewidth=2, markersize=4)
        
        # 添加趋势线
        if len(y_values) > 2:
            z = self.plt.polyfit(range(len(y_values)), y_values, 1)
            p = self.plt.poly1d(z)
            ax.plot(x_values, p(range(len(y_values))), "--", alpha=0.5, label="趋势线")
            ax.legend()
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label or x_col or "X", fontsize=12)
        ax.set_ylabel(y_label or "数值", fontsize=12)
        ax.grid(True, alpha=0.3)
        
        self.plt.tight_layout()
        
        if save_path:
            self.plt.savefig(save_path, dpi=self.dpi)
        
        self.plt.close()
        
        return save_path or ""
    
    def create_bar_chart(
        self,
        data: List[Dict],
        group_col: str,
        value_col: str,
        title: str = "对比图",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建柱状图
        
        Args:
            data: 数据
            group_col: 分组列
            value_col: 数值列
            title: 标题
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        labels, values = self._prepare_aggregate_data(data, group_col, value_col)
        
        if not values:
            raise ValueError("没有有效数据")
        
        fig, ax = self.plt.subplots(figsize=self.figure_size)
        
        colors = self._generate_colors(len(labels))
        bars = ax.bar(range(len(labels)), values, color=colors)
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(value_col, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}',
                    ha='center', va='bottom', fontsize=9)
        
        self.plt.tight_layout()
        
        if save_path:
            self.plt.savefig(save_path, dpi=self.dpi)
        
        self.plt.close()
        
        return save_path or ""
    
    def create_pie_chart(
        self,
        data: List[Dict],
        group_col: str,
        value_col: str,
        title: str = "占比图",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建饼图
        
        Args:
            data: 数据
            group_col: 分组列
            value_col: 数值列
            title: 标题
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        labels, values = self._prepare_aggregate_data(data, group_col, value_col)
        
        if not values:
            raise ValueError("没有有效数据")
        
        fig, ax = self.plt.subplots(figsize=self.figure_size)
        
        colors = self._generate_colors(len(labels))
        
        def autopct_format(pct):
            return f'{pct:.1f}%' if pct > 3 else ''
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=autopct_format,
            colors=colors,
            startangle=90
        )
        
        # 设置百分比文字样式
        for autotext in autotexts:
            autotext.set_fontsize(9)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        self.plt.tight_layout()
        
        if save_path:
            self.plt.savefig(save_path, dpi=self.dpi)
        
        self.plt.close()
        
        return save_path or ""
    
    def create_scatter_chart(
        self,
        data: List[Dict],
        x_col: str,
        y_col: str,
        title: str = "散点图",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建散点图
        
        Args:
            data: 数据
            x_col: x轴列
            y_col: y轴列
            title: 标题
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        x_values = []
        y_values = []
        
        for row in data:
            try:
                x_values.append(float(row.get(x_col, 0)))
                y_values.append(float(row.get(y_col, 0)))
            except (ValueError, TypeError):
                continue
        
        if not x_values:
            raise ValueError("没有有效数据")
        
        fig, ax = self.plt.subplots(figsize=self.figure_size)
        
        ax.scatter(x_values, y_values, alpha=0.6, s=50)
        
        # 添加趋势线
        if len(x_values) > 2:
            z = self.plt.polyfit(x_values, y_values, 1)
            p = self.plt.poly1d(z)
            x_line = [min(x_values), max(x_values)]
            ax.plot(x_line, p(x_line), "--", alpha=0.5, label="趋势线")
            ax.legend()
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        self.plt.tight_layout()
        
        if save_path:
            self.plt.savefig(save_path, dpi=self.dpi)
        
        self.plt.close()
        
        return save_path or ""
    
    def create_heatmap(
        self,
        data: List[Dict],
        rows_col: str,
        cols_col: str,
        values_col: str,
        title: str = "热力图",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建热力图
        
        Args:
            data: 数据
            rows_col: 行分组列
            cols_col: 列分组列
            values_col: 数值列
            title: 标题
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        import pandas as pd
        
        if not data:
            raise ValueError("没有有效数据")
        
        df = pd.DataFrame(data)
        
        # 创建透视表
        try:
            pivot = df.pivot_table(
                values=values_col,
                index=rows_col,
                columns=cols_col,
                aggfunc='sum',
                fill_value=0
            )
        except Exception:
            raise ValueError("无法创建热力图数据")
        
        fig, ax = self.plt.subplots(figsize=(12, 8))
        
        im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
        
        # 设置刻度
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_yticks(range(len(pivot.index)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
        ax.set_yticklabels(pivot.index)
        
        # 添加数值标签
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                text = ax.text(j, i, f'{pivot.values[i, j]:.0f}',
                              ha="center", va="center", color="black", fontsize=8)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        self.plt.colorbar(im, ax=ax, label=values_col)
        self.plt.tight_layout()
        
        if save_path:
            self.plt.savefig(save_path, dpi=self.dpi)
        
        self.plt.close()
        
        return save_path or ""
    
    def _generate_colors(self, n: int) -> List[str]:
        """生成颜色列表"""
        base_colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
            '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
        ]
        
        if n <= len(base_colors):
            return base_colors[:n]
        
        # 如果颜色不够，重复使用
        return [base_colors[i % len(base_colors)] for i in range(n)]


class VisualizationAgent:
    """
    Visualization Agent
    
    核心职责：
    - 图表类型选择：根据数据特点选择合适的图表
    - 图表生成：使用Matplotlib生成图表
    - 样式定制：设置标题、标签、颜色等
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化Visualization Agent
        
        Args:
            output_dir: 图表输出目录
        """
        self.system_prompt = VIZ_SYSTEM_PROMPT
        self.output_dir = output_dir or config.visualization.output_dir
        self.chart_generator = ChartGenerator()
        self.max_retries = 3
        
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def recommend_chart(
        self,
        query: str,
        data: List[Dict]
    ) -> Dict[str, Any]:
        """
        推荐图表类型
        
        Args:
            query: 用户查询
            data: 数据
            
        Returns:
            推荐配置
        """
        # 分析数据特征
        data_features = self._analyze_data_features(data)
        
        prompt = VIZ_PROMPT.format(
            query=query,
            data=json.dumps(data[:10], ensure_ascii=False),
            data_features=json.dumps(data_features, ensure_ascii=False)
        )
        
        for attempt in range(self.max_retries):
            try:
                response = create_llm_call(
                    system_prompt=self.system_prompt,
                    user_prompt=prompt,
                    temperature=0.5
                )
                
                result = self._parse_json_response(response)
                if result:
                    return result
                
            except Exception:
                if attempt == self.max_retries - 1:
                    return self._get_default_recommendation(data_features)
                continue
        
        return self._get_default_recommendation(data_features)
    
    def generate_chart(
        self,
        data: List[Dict],
        chart_type: str,
        title: str = "",
        **kwargs
    ) -> VisualizationResult:
        """
        生成图表
        
        Args:
            data: 数据
            chart_type: 图表类型
            title: 标题
            **kwargs: 其他参数
            
        Returns:
            VisualizationResult对象
        """
        result = VisualizationResult()
        result.chart_type = chart_type
        
        # 生成文件名
        timestamp = random.randint(10000, 99999)
        filename = f"chart_{chart_type}_{timestamp}.png"
        save_path = os.path.join(self.output_dir, filename)
        
        try:
            if chart_type == "line":
                save_path = self.chart_generator.create_line_chart(
                    data, title, save_path=save_path
                )
            elif chart_type == "bar":
                save_path = self.chart_generator.create_bar_chart(
                    data,
                    kwargs.get("x_axis", "region"),
                    kwargs.get("y_axis", "amount"),
                    title,
                    save_path=save_path
                )
            elif chart_type == "pie":
                save_path = self.chart_generator.create_pie_chart(
                    data,
                    kwargs.get("x_axis", "category"),
                    kwargs.get("y_axis", "amount"),
                    title,
                    save_path=save_path
                )
            elif chart_type == "scatter":
                save_path = self.chart_generator.create_scatter_chart(
                    data,
                    kwargs.get("x_axis", "quantity"),
                    kwargs.get("y_axis", "amount"),
                    title,
                    save_path=save_path
                )
            else:
                # 默认使用柱状图
                save_path = self.chart_generator.create_bar_chart(
                    data,
                    kwargs.get("x_axis", "region"),
                    kwargs.get("y_axis", "amount"),
                    title,
                    save_path=save_path
                )
            
            result.file_path = save_path
            result.saved = True
            result.description = f"已生成{chart_type}类型图表: {filename}"
            
        except Exception as e:
            result.error = f"生成图表失败: {str(e)}"
        
        return result
    
    def visualize(
        self,
        query: str,
        data: List[Dict],
        chart_type: str = None,
        title: str = ""
    ) -> VisualizationResult:
        """
        执行完整可视化流程
        
        Args:
            query: 用户查询
            data: 数据
            chart_type: 指定图表类型（可选）
            title: 图表标题
            
        Returns:
            VisualizationResult对象
        """
        # 如果没有指定图表类型，自动推荐
        if not chart_type:
            recommendation = self.recommend_chart(query, data)
            chart_type = recommendation.get("chart_type", "bar")
            title = title or recommendation.get("title", "数据可视化")
        else:
            title = title or "数据可视化"
        
        # 准备参数
        data_features = self._analyze_data_features(data)
        
        kwargs = {}
        if "x_axis" in data_features:
            kwargs["x_axis"] = data_features["x_axis"]
        if "y_axis" in data_features:
            kwargs["y_axis"] = data_features["y_axis"]
        
        # 生成图表
        return self.generate_chart(data, chart_type, title, **kwargs)
    
    def _analyze_data_features(self, data: List[Dict]) -> Dict[str, Any]:
        """分析数据特征"""
        if not data:
            return {}
        
        features = {}
        first_row = data[0]
        
        # 查找数值列
        numeric_cols = []
        for key, value in first_row.items():
            if isinstance(value, (int, float)):
                numeric_cols.append(key)
        
        if numeric_cols:
            features["numeric_columns"] = numeric_cols
            features["y_axis"] = numeric_cols[0]
        
        # 查找类别列
        categorical_cols = []
        for key, value in first_row.items():
            if isinstance(value, str):
                categorical_cols.append(key)
        
        if categorical_cols:
            features["categorical_columns"] = categorical_cols
            features["x_axis"] = categorical_cols[0]
        
        # 查找时间列
        time_keywords = ["date", "time", "day", "month", "year"]
        for key in first_row.keys():
            if any(kw in key.lower() for kw in time_keywords):
                features["time_column"] = key
                features["x_axis"] = key
                break
        
        return features
    
    def _get_default_recommendation(self, data_features: Dict) -> Dict[str, Any]:
        """获取默认推荐"""
        if data_features.get("time_column"):
            return {
                "chart_type": "line",
                "title": "趋势分析图",
                "reasoning": "检测到时间序列数据，使用折线图展示趋势"
            }
        elif data_features.get("categorical_columns"):
            return {
                "chart_type": "bar",
                "title": "分类对比图",
                "x_axis": data_features.get("x_axis", "category"),
                "y_axis": data_features.get("y_axis", "amount"),
                "reasoning": "检测到分类数据，使用柱状图进行对比"
            }
        else:
            return {
                "chart_type": "bar",
                "title": "数据分布图",
                "reasoning": "使用柱状图展示数据分布"
            }
    
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
viz_agent = VisualizationAgent()


def visualization_agent_node(state) -> Dict[str, Any]:
    """
    Visualization Agent的LangGraph节点函数
    
    Args:
        state: 当前状态
        
    Returns:
        要更新的状态字典
    """
    # 获取查询和分析结果
    query_result = state.get("query_result")
    
    if not query_result or not query_result.data:
        state["visualization_result"] = VisualizationResult(
            error="没有数据可供可视化"
        )
        state["next_agent"] = AgentName.TERMINATE
        return state
    
    # 记录开始
    state["intermediate_steps"].append({
        "agent": "visualization_agent",
        "action": "开始生成可视化",
        "data_rows": len(query_result.data)
    })
    
    # 生成可视化
    result = viz_agent.visualize(
        query=state["user_query"],
        data=query_result.data
    )
    
    # 记录完成
    state["intermediate_steps"].append({
        "agent": "visualization_agent",
        "action": "完成可视化",
        "chart_type": result.chart_type,
        "file_path": result.file_path
    })
    
    # 更新状态
    state["visualization_result"] = result
    state["next_agent"] = AgentName.TERMINATE
    
    return state


# 导入AgentName
from graph.state import AgentName
