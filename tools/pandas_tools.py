"""
Pandas数据分析工具
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StatisticsResult:
    """统计结果"""
    count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    sum: float
    q25: float
    q75: float


class DataAnalyzer:
    """
    数据分析工具类
    
    提供常用的数据分析功能
    """
    
    def __init__(self, data: List[Dict]):
        """
        初始化分析器
        
        Args:
            data: 数据列表
        """
        self.df = pd.DataFrame(data)
    
    def get_statistics(self, column: str) -> StatisticsResult:
        """
        获取列的统计信息
        
        Args:
            column: 列名
            
        Returns:
            统计结果
        """
        if column not in self.df.columns:
            raise ValueError(f"列 '{column}' 不存在")
        
        col_data = self.df[column].dropna()
        
        return StatisticsResult(
            count=len(col_data),
            mean=col_data.mean(),
            median=col_data.median(),
            std=col_data.std() if len(col_data) > 1 else 0,
            min=col_data.min(),
            max=col_data.max(),
            sum=col_data.sum(),
            q25=col_data.quantile(0.25),
            q75=col_data.quantile(0.75)
        )
    
    def group_statistics(
        self,
        group_by: str,
        value_col: str,
        agg_func: str = "sum"
    ) -> pd.DataFrame:
        """
        分组统计
        
        Args:
            group_by: 分组列
            value_col: 数值列
            agg_func: 聚合函数
            
        Returns:
            分组统计结果
        """
        if group_by not in self.df.columns:
            raise ValueError(f"分组列 '{group_by}' 不存在")
        if value_col not in self.df.columns:
            raise ValueError(f"数值列 '{value_col}' 不存在")
        
        result = self.df.groupby(group_by)[value_col].agg(agg_func)
        return result.reset_index()
    
    def time_series_analysis(
        self,
        date_col: str,
        value_col: str,
        freq: str = "D"
    ) -> pd.DataFrame:
        """
        时间序列分析
        
        Args:
            date_col: 日期列
            value_col: 数值列
            freq: 频率 (D=天, W=周, M=月)
            
        Returns:
            时间序列数据
        """
        if date_col not in self.df.columns:
            raise ValueError(f"日期列 '{date_col}' 不存在")
        
        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # 设置日期索引
        df.set_index(date_col, inplace=True)
        
        # 重采样
        resampled = df[value_col].resample(freq).sum().reset_index()
        
        # 计算移动平均
        resampled[f"{value_col}_ma7"] = resampled[value_col].rolling(7).mean()
        resampled[f"{value_col}_ma30"] = resampled[value_col].rolling(30).mean()
        
        return resampled
    
    def correlation_analysis(self, columns: List[str]) -> pd.DataFrame:
        """
        相关性分析
        
        Args:
            columns: 要分析的列
            
        Returns:
            相关性矩阵
        """
        valid_cols = [c for c in columns if c in self.df.columns]
        
        if len(valid_cols) < 2:
            raise ValueError("需要至少2列进行相关性分析")
        
        return self.df[valid_cols].corr()
    
    def detect_outliers(
        self,
        column: str,
        method: str = "iqr"
    ) -> Tuple[List[int], List[Dict]]:
        """
        异常值检测
        
        Args:
            column: 列名
            method: 方法 (iqr=四分位距, zscore=Z分数)
            
        Returns:
            (异常值索引列表, 异常值详情列表)
        """
        if column not in self.df.columns:
            raise ValueError(f"列 '{column}' 不存在")
        
        outliers_idx = []
        outliers_info = []
        
        if method == "iqr":
            q1 = self.df[column].quantile(0.25)
            q3 = self.df[column].quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for idx, value in self.df[column].items():
                if value < lower_bound or value > upper_bound:
                    outliers_idx.append(idx)
                    outliers_info.append({
                        "index": idx,
                        "value": value,
                        "bound": "lower" if value < lower_bound else "upper",
                        "threshold": lower_bound if value < lower_bound else upper_bound
                    })
        
        elif method == "zscore":
            mean = self.df[column].mean()
            std = self.df[column].std()
            
            for idx, value in self.df[column].items():
                z_score = abs((value - mean) / std) if std > 0 else 0
                if z_score > 3:
                    outliers_idx.append(idx)
                    outliers_info.append({
                        "index": idx,
                        "value": value,
                        "z_score": z_score
                    })
        
        return outliers_idx, outliers_info
    
    def trend_detection(
        self,
        x_col: str,
        y_col: str
    ) -> Dict[str, Any]:
        """
        趋势检测
        
        Args:
            x_col: X轴列
            y_col: Y轴列
            
        Returns:
            趋势信息
        """
        if x_col not in self.df.columns or y_col not in self.df.columns:
            raise ValueError("指定的列不存在")
        
        df = self.df[[x_col, y_col]].dropna()
        
        if len(df) < 2:
            return {"error": "数据点不足"}
        
        # 简单线性回归
        x = np.arange(len(df))
        y = df[y_col].values
        
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # 计算趋势
        if abs(slope) < 0.01:
            trend = "平稳"
        elif slope > 0:
            trend = "上升"
        else:
            trend = "下降"
        
        # 计算变化率
        first_half = y[:len(y)//2].mean()
        second_half = y[len(y)//2:].mean()
        change_rate = (second_half - first_half) / first_half * 100 if first_half != 0 else 0
        
        return {
            "trend": trend,
            "slope": slope,
            "change_rate": change_rate,
            "direction": "up" if slope > 0 else "down" if slope < 0 else "flat"
        }


def analyze_data(
    data: List[Dict],
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """
    数据分析便捷函数
    
    Args:
        data: 数据列表
        analysis_type: 分析类型 (full, statistics, outliers, trend)
        
    Returns:
        分析结果
    """
    if not data:
        return {"error": "没有数据"}
    
    analyzer = DataAnalyzer(data)
    
    if analysis_type == "full":
        # 完整分析
        result = {
            "row_count": len(data),
            "columns": list(data[0].keys()) if data else [],
            "column_types": {
                col: str(type(data[0][col]).__name__)
                for col in (data[0].keys() if data else [])
            }
        }
        
        # 数值列统计
        numeric_cols = analyzer.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            result["statistics"] = {}
            for col in numeric_cols:
                stats = analyzer.get_statistics(col)
                result["statistics"][col] = {
                    "count": stats.count,
                    "mean": round(stats.mean, 2),
                    "std": round(stats.std, 2),
                    "min": round(stats.min, 2),
                    "max": round(stats.max, 2)
                }
        
        return result
    
    elif analysis_type == "statistics":
        # 简单统计
        numeric_cols = analyzer.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {"error": "没有数值列"}
        
        col = numeric_cols[0]
        stats = analyzer.get_statistics(col)
        return {
            "column": col,
            "count": stats.count,
            "mean": round(stats.mean, 2),
            "median": round(stats.median, 2),
            "std": round(stats.std, 2)
        }
    
    elif analysis_type == "outliers":
        numeric_cols = analyzer.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {"error": "没有数值列"}
        
        col = numeric_cols[0]
        outliers_idx, outliers_info = analyzer.detect_outliers(col)
        return {
            "column": col,
            "outlier_count": len(outliers_idx),
            "outliers": outliers_info[:10]  # 最多返回10个
        }
    
    elif analysis_type == "trend":
        numeric_cols = analyzer.df.select_dtypes(include=[np.number]).columns
        str_cols = analyzer.df.select_dtypes(include=["object"]).columns
        
        if len(numeric_cols) == 0:
            return {"error": "没有数值列"}
        
        col = numeric_cols[0]
        date_col = None
        
        # 尝试找日期列
        for c in str_cols:
            if "date" in c.lower() or "time" in c.lower():
                date_col = c
                break
        
        if date_col:
            return analyzer.trend_detection(date_col, col)
        else:
            # 使用索引作为x轴
            return analyzer.trend_detection("index", col)
    
    return {"error": f"未知的分析类型: {analysis_type}"}
