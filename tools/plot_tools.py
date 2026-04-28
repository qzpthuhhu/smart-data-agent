"""
可视化工具
基于Matplotlib的图表生成工具
"""

import os
import random
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np


# 设置中文字体
def setup_chinese_font():
    """设置中文字体"""
    # 尝试多种中文字体
    fonts = [
        'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei',
        'PingFang SC', 'STHeiti', 'Arial Unicode MS', 'DejaVu Sans'
    ]
    
    for font in fonts:
        try:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            break
        except:
            continue


setup_chinese_font()


class ChartConfig:
    """图表配置"""
    
    # 样式
    STYLES = ['default', 'seaborn-v0_8-darkgrid', 'bmh', 'ggplot', 'classic']
    
    # 颜色方案
    COLOR_SCHEMES = {
        'default': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'],
        'warm': ['#e74c3c', '#e67e22', '#f39c12', '#f1c40f', '#f5b041'],
        'cool': ['#3498db', '#2980b9', '#1abc9c', '#16a085', '#00bcd4'],
        'pastel': ['#a8e6cf', '#dcedc1', '#ffd3b6', '#ffaaa5', '#ff8b94'],
        'vibrant': ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7']
    }
    
    @classmethod
    def get_config(cls, style: str = 'default', **kwargs):
        """获取配置"""
        return {
            'style': kwargs.get('style', 'default'),
            'colors': kwargs.get('colors', cls.COLOR_SCHEMES['default']),
            'figure_size': kwargs.get('figure_size', (10, 6)),
            'dpi': kwargs.get('dpi', 100),
            'title_size': kwargs.get('title_size', 14),
            'label_size': kwargs.get('label_size', 11),
            'tick_size': kwargs.get('tick_size', 10),
        }


class ChartFactory:
    """
    图表工厂
    
    根据数据类型自动选择合适的图表类型
    """
    
    @staticmethod
    def recommend_chart_type(
        data: List[Dict],
        x_col: Optional[str] = None,
        y_col: Optional[str] = None
    ) -> str:
        """
        推荐图表类型
        
        Args:
            data: 数据
            x_col: X轴列
            y_col: Y轴列
            
        Returns:
            推荐的图表类型
        """
        if not data:
            return 'bar'
        
        df = pd.DataFrame(data)
        
        # 检测是否为时间序列
        if x_col:
            x_lower = x_col.lower()
            if any(kw in x_lower for kw in ['date', 'time', 'day', 'month', 'year']):
                return 'line'
        
        # 检测分类数据
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # 类别数量
        if len(categorical_cols) > 0:
            unique_counts = [df[col].nunique() for col in categorical_cols]
            if max(unique_counts) <= 10 and len(numeric_cols) > 0:
                return 'bar'  # 适合柱状图
        
        # 时间序列
        if x_col and y_col and x_col in df.columns:
            try:
                pd.to_datetime(df[x_col])
                return 'line'
            except:
                pass
        
        return 'bar'
    
    @staticmethod
    def prepare_plot_data(
        data: List[Dict],
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        group_col: Optional[str] = None
    ) -> Tuple[List, List, Optional[str]]:
        """
        准备绘图数据
        
        Args:
            data: 数据
            x_col: X轴列
            y_col: Y轴列
            group_col: 分组列
            
        Returns:
            (x值, y值, x轴标签)
        """
        if not data:
            return [], [], None
        
        df = pd.DataFrame(data)
        
        # 自动选择列
        if not y_col:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                y_col = numeric_cols[0]
        
        if not x_col:
            str_cols = df.select_dtypes(include=['object']).columns
            time_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
            
            if time_cols:
                x_col = time_cols[0]
            elif len(str_cols) > 0:
                x_col = str_cols[0]
        
        # 提取数据
        x_values = []
        y_values = []
        x_label = x_col
        
        for row in data:
            if x_col and x_col in row:
                val = row[x_col]
                if isinstance(val, (int, float)):
                    x_values.append(val)
                else:
                    x_values.append(str(val))
            else:
                x_values.append(len(x_values))
            
            if y_col and y_col in row:
                try:
                    y_values.append(float(row[y_col]))
                except (ValueError, TypeError):
                    y_values.append(0)
            else:
                y_values.append(0)
        
        return x_values, y_values, x_label


class MatplotlibPlotter:
    """
    Matplotlib绘图器
    
    提供各种图表的绑制功能
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化绘图器
        
        Args:
            config: 图表配置
        """
        self.config = config or ChartConfig.get_config()
        self._apply_style()
    
    def _apply_style(self):
        """应用样式"""
        style = self.config.get('style', 'default')
        try:
            plt.style.use(style)
        except:
            pass
        
        plt.rcParams['figure.figsize'] = self.config.get('figure_size', (10, 6))
        plt.rcParams['figure.dpi'] = self.config.get('dpi', 100)
    
    def create_line_chart(
        self,
        x: List,
        y: List,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        save_path: Optional[str] = None,
        show_trend: bool = True
    ) -> str:
        """
        创建折线图
        
        Args:
            x: X轴数据
            y: Y轴数据
            title: 标题
            xlabel: X轴标签
            ylabel: Y轴标签
            save_path: 保存路径
            show_trend: 是否显示趋势线
            
        Returns:
            保存的文件路径
        """
        fig, ax = plt.subplots(figsize=self.config['figure_size'])
        
        ax.plot(x, y, marker='o', linewidth=2, markersize=4,
                color=self.config['colors'][0])
        
        # 添加趋势线
        if show_trend and len(y) > 2:
            z = np.polyfit(range(len(y)), y, 1)
            p = np.poly1d(z)
            trend_line = [p(i) for i in range(len(y))]
            ax.plot(x, trend_line, '--', alpha=0.5, color='red', label='趋势')
            ax.legend()
        
        ax.set_title(title or '趋势图', fontsize=self.config['title_size'], fontweight='bold')
        ax.set_xlabel(xlabel or 'X', fontsize=self.config['label_size'])
        ax.set_ylabel(ylabel or 'Y', fontsize=self.config['label_size'])
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'])
        
        plt.close()
        return save_path or ""
    
    def create_bar_chart(
        self,
        categories: List,
        values: List,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        save_path: Optional[str] = None,
        horizontal: bool = False
    ) -> str:
        """
        创建柱状图
        
        Args:
            categories: 类别
            values: 数值
            title: 标题
            xlabel: X轴标签
            ylabel: Y轴标签
            save_path: 保存路径
            horizontal: 是否水平柱状图
            
        Returns:
            保存的文件路径
        """
        fig, ax = plt.subplots(figsize=self.config['figure_size'])
        
        colors = self.config['colors']
        
        if horizontal:
            bars = ax.barh(range(len(categories)), values, color=colors[:len(categories)])
            ax.set_yticks(range(len(categories)))
            ax.set_yticklabels(categories)
            ax.set_xlabel(ylabel or '数值', fontsize=self.config['label_size'])
            ax.set_ylabel(xlabel or '类别', fontsize=self.config['label_size'])
        else:
            bars = ax.bar(range(len(categories)), values, color=colors[:len(categories)])
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.set_xlabel(xlabel or '类别', fontsize=self.config['label_size'])
            ax.set_ylabel(ylabel or '数值', fontsize=self.config['label_size'])
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=9)
        
        ax.set_title(title or '对比图', fontsize=self.config['title_size'], fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'])
        
        plt.close()
        return save_path or ""
    
    def create_pie_chart(
        self,
        labels: List,
        values: List,
        title: str = "",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建饼图
        
        Args:
            labels: 标签
            values: 数值
            title: 标题
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        fig, ax = plt.subplots(figsize=self.config['figure_size'])
        
        colors = self.config['colors']
        
        def autopct_format(pct):
            return f'{pct:.1f}%' if pct > 3 else ''
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=autopct_format,
            colors=colors[:len(labels)],
            startangle=90
        )
        
        for autotext in autotexts:
            autotext.set_fontsize(9)
        
        ax.set_title(title or '占比图', fontsize=self.config['title_size'], fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'])
        
        plt.close()
        return save_path or ""
    
    def create_scatter_chart(
        self,
        x: List,
        y: List,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建散点图
        
        Args:
            x: X轴数据
            y: Y轴数据
            title: 标题
            xlabel: X轴标签
            ylabel: Y轴标签
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        fig, ax = plt.subplots(figsize=self.config['figure_size'])
        
        ax.scatter(x, y, alpha=0.6, s=50, color=self.config['colors'][0])
        
        # 添加趋势线
        if len(x) > 2:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            x_line = [min(x), max(x)]
            ax.plot(x_line, p(x_line), '--', alpha=0.5, color='red', label='趋势')
            ax.legend()
        
        ax.set_title(title or '散点图', fontsize=self.config['title_size'], fontweight='bold')
        ax.set_xlabel(xlabel or 'X', fontsize=self.config['label_size'])
        ax.set_ylabel(ylabel or 'Y', fontsize=self.config['label_size'])
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'])
        
        plt.close()
        return save_path or ""
    
    def create_multi_line_chart(
        self,
        data: Dict[str, List],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        save_path: Optional[str] = None
    ) -> str:
        """
        创建多线图
        
        Args:
            data: 数据字典 {系列名: [值]}
            title: 标题
            xlabel: X轴标签
            ylabel: Y轴标签
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        fig, ax = plt.subplots(figsize=self.config['figure_size'])
        
        colors = self.config['colors']
        
        for i, (series_name, values) in enumerate(data.items()):
            x = range(len(values))
            ax.plot(x, values, marker='o', linewidth=2, 
                   color=colors[i % len(colors)], label=series_name)
        
        ax.set_title(title or '多系列图', fontsize=self.config['title_size'], fontweight='bold')
        ax.set_xlabel(xlabel or 'X', fontsize=self.config['label_size'])
        ax.set_ylabel(ylabel or 'Y', fontsize=self.config['label_size'])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['dpi'])
        
        plt.close()
        return save_path or ""


# 便捷函数
def quick_plot(
    data: List[Dict],
    chart_type: str = "auto",
    title: str = "",
    save_dir: str = "output/charts",
    **kwargs
) -> str:
    """
    快速绑图
    
    Args:
        data: 数据
        chart_type: 图表类型
        title: 标题
        save_dir: 保存目录
        **kwargs: 其他参数
        
    Returns:
        保存的文件路径
    """
    # 确保目录存在
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 自动选择图表类型
    if chart_type == "auto":
        chart_type = ChartFactory.recommend_chart_type(
            data,
            kwargs.get('x_col'),
            kwargs.get('y_col')
        )
    
    # 准备数据
    x, y, xlabel = ChartFactory.prepare_plot_data(
        data,
        kwargs.get('x_col'),
        kwargs.get('y_col')
    )
    
    # 生成文件名
    timestamp = random.randint(10000, 99999)
    filename = f"chart_{chart_type}_{timestamp}.png"
    save_path = os.path.join(save_dir, filename)
    
    # 创建图表
    plotter = MatplotlibPlotter()
    
    if chart_type == "line":
        return plotter.create_line_chart(
            x, y, title, xlabel, kwargs.get('ylabel', ''),
            save_path, kwargs.get('show_trend', True)
        )
    elif chart_type == "bar":
        return plotter.create_bar_chart(
            x, y, title, xlabel, kwargs.get('ylabel', ''),
            save_path, kwargs.get('horizontal', False)
        )
    elif chart_type == "pie":
        return plotter.create_pie_chart(
            x, y, title, save_path
        )
    elif chart_type == "scatter":
        return plotter.create_scatter_chart(
            x, y, title, xlabel, kwargs.get('ylabel', ''),
            save_path
        )
    else:
        return plotter.create_bar_chart(
            x, y, title, xlabel, kwargs.get('ylabel', ''),
            save_path
        )
