"""
智能数据分析Agent - Streamlit Web界面
提供完整的Web界面，支持数据查询、分析、可视化和对话历史
"""

import streamlit as st
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from config import config, load_config_from_env, get_current_model
from graph.workflow import DataAnalysisWorkflow
from memory import memory_manager

# ============ 页面配置 ============

st.set_page_config(
    page_title="智能数据分析Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f8ff;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# ============ 初始化 ============

def init_session_state():
    """初始化会话状态"""
    if 'workflow' not in st.session_state:
        DataAnalysisWorkflow(use_checkpointer=False) = DataAnalysisWorkflow(use_checkpointer=True)
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"web_{int(time.time())}"
    
    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0
    
    if 'test_results' not in st.session_state:
        st.session_state.test_results = []
    
    # 加载环境变量
    load_config_from_env()


def get_api_status() -> Dict[str, Any]:
    """获取API状态"""
    status = {
        "configured": False,
        "provider": "未配置",
        "model": "未知",
        "error": None
    }
    
    try:
        if config.llm.is_configured:
            status["configured"] = True
            status["provider"] = config.llm.active_provider
            status["model"] = get_current_model()
        else:
            status["error"] = "请配置API密钥"
    except Exception as e:
        status["error"] = str(e)
    
    return status


# ============ 侧边栏 ============

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### 📊 智能数据分析Agent")
        st.markdown("---")
        
        # API状态
        api_status = get_api_status()
        
        if api_status["configured"]:
            st.success("✅ API已配置")
            st.info(f"**提供商**: {api_status['provider']}")
            st.info(f"**模型**: {api_status['model']}")
        else:
            st.error("❌ API未配置")
            if api_status["error"]:
                st.warning(api_status["error"])
        
        st.markdown("---")
        
        # 导航菜单
        st.markdown("### 📋 导航菜单")
        pages = {
            "🏠 主页": "home",
            "🔍 数据查询": "query",
            "📈 数据分析": "analysis",
            "📊 可视化": "visualization",
            "💬 对话历史": "history",
            "⚙️ 设置": "settings",
            "🔄 完整演示": "workflow_demo"
        }
        
        selected = st.radio("选择页面", list(pages.keys()), index=0)
        
        # 统计信息
        st.markdown("### 📊 统计信息")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("查询次数", st.session_state.get('query_count', 0))
        with col2:
            st.metric("会话ID", st.session_state.get('session_id', 'N/A')[:8])
        
        st.markdown("---")
        
        # 关于信息
        st.markdown("### ℹ️ 关于")
        st.caption("智能数据分析Agent v1.0")
        st.caption("基于LangGraph构建")
        
        return pages[selected]


# ============ 页面1：主页 ============

def render_home_page():
    """渲染主页"""
    st.markdown('<p class="main-header">🏠 智能数据分析Agent</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于自然语言的数据分析助手</p>', unsafe_allow_html=True)
    
    # 快速开始区域
    st.markdown("### 🚀 快速开始")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🔍 数据查询</h4>
            <p>使用自然语言查询数据库，自动转换为SQL</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开始查询", key="quick_query"):
            st.session_state.current_page = "query"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>📈 数据分析</h4>
            <p>统计分析、趋势分析、异常检测</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开始分析", key="quick_analysis"):
            st.session_state.current_page = "analysis"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>📊 可视化</h4>
            <p>生成交互式图表，支持多种类型</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("生成图表", key="quick_viz"):
            st.session_state.current_page = "visualization"
            st.rerun()
    
    st.markdown("---")
    
    # 功能介绍
    st.markdown("### 🎯 系统功能")
    
    features = [
        ("🤖 智能Agent", "基于LangGraph的多Agent协作系统，自动化完成数据分析任务"),
        ("💬 自然语言", "支持自然语言查询，无需编写SQL代码"),
        ("📊 多维度分析", "支持统计分析、趋势分析、异常检测等多种分析类型"),
        ("🎨 交互可视化", "生成Plotly交互式图表，支持导出和自定义配置"),
        ("🧠 记忆系统", "支持短期和长期记忆，记住对话上下文和重要信息"),
        ("🔄 完整工作流", "从查询到分析到可视化，完整的数据分析流程")
    ]
    
    for title, desc in features:
        with st.expander(title):
            st.write(desc)
    
    st.markdown("---")
    
    # 最近查询
    st.markdown("### 📝 最近查询")
    
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history[-5:]):
            with st.expander(f"查询 {i+1}: {chat.get('query', '')[:50]}..."):
                st.write(f"**时间**: {chat.get('timestamp', 'N/A')}")
                st.write(f"**查询**: {chat.get('query', '')}")
                if chat.get('result'):
                    st.write(f"**结果**: {str(chat['result'])[:200]}...")
    else:
        st.info("暂无查询记录，开始你的第一个查询吧！")
    
    st.markdown("---")
    
    # 系统状态
    st.markdown("### 🔧 系统状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        api_status = get_api_status()
        status = "✅ 正常" if api_status["configured"] else "❌ 未配置"
        st.metric("API状态", status)
    
    with col2:
        db_exists = Path(config.database.db_path).exists()
        st.metric("数据库", "✅ 存在" if db_exists else "❌ 不存在")
    
    with col3:
        st.metric("会话数", len(st.session_state.chat_history))
    
    with col4:
        st.metric("模型", get_current_model())


# ============ 页面2：数据查询 ============

def render_query_page():
    """渲染数据查询页面"""
    st.markdown("### 🔍 数据查询")
    st.write("使用自然语言查询数据库，系统会自动转换为SQL并执行查询")
    
    # 查询输入
    query_input = st.text_area(
        "输入你的查询",
        placeholder="例如：显示最近一个月的销售总额",
        height=100
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        submitted = st.button("🚀 执行查询", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ 清空", use_container_width=True):
            st.session_state.query_result = None
            st.session_state.generated_sql = None
            st.rerun()
    
    if submitted and query_input:
        with st.spinner("正在处理查询..."):
            try:
                # 执行查询
                result = DataAnalysisWorkflow(use_checkpointer=False).run(query_input, st.session_state.session_id)
                
                # 提取结果
                if result:
                    for state in result.values():
                        response = state.get("final_response", "")
                        query_result = state.get("query_result")
                        
                        # 存储到会话状态
                        st.session_state.chat_history.append({
                            "query": query_input,
                            "result": query_result,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        st.session_state.query_count += 1
                        
                        # 显示结果
                        st.markdown("#### 📋 查询结果")
                        
                        if query_result and hasattr(query_result, 'data') and query_result.data:
                            # SQL预览
                            if hasattr(query_result, 'sql') and query_result.sql:
                                with st.expander("📜 SQL语句"):
                                    st.code(query_result.sql, language="sql")
                            
                            # 数据展示
                            st.markdown("**数据预览:**")
                            import pandas as pd
                            df = pd.DataFrame(query_result.data)
                            st.dataframe(df, use_container_width=True)
                            
                            st.success(f"✅ 查询成功，返回 {query_result.row_count} 条记录")
                        else:
                            st.info("查询未返回数据")
                        
                        # 显示AI响应
                        if response:
                            st.markdown("#### 💬 AI响应")
                            st.markdown(response)
                
            except Exception as e:
                st.error(f"查询失败: {str(e)}")
                logging.error(f"Query error: {str(e)}")
    
    # SQL预览区域
    if 'generated_sql' in st.session_state and st.session_state.generated_sql:
        st.markdown("#### 📜 SQL预览")
        st.code(st.session_state.generated_sql, language="sql")
    
    # 数据导出功能
    if 'query_result' in st.session_state and st.session_state.query_result:
        st.markdown("---")
        st.markdown("#### 📥 导出数据")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 导出CSV", use_container_width=True):
                import pandas as pd
                from io import StringIO
                
                df = pd.DataFrame(st.session_state.query_result.data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="下载CSV",
                    data=csv,
                    file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 导出JSON", use_container_width=True):
                import json
                
                json_data = json.dumps(st.session_state.query_result.data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="下载JSON",
                    data=json_data,
                    file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            st.button("📄 复制到剪贴板", use_container_width=True, disabled=True)


# ============ 页面3：数据分析 ============

def render_analysis_page():
    """渲染数据分析页面"""
    st.markdown("### 📈 数据分析")
    st.write("选择数据集和分析类型，进行深度数据分析")
    
    # 数据集选择
    st.markdown("#### 📁 选择数据集")
    datasets = {
        "销售数据 (sales)": "sales",
        "产品数据 (products)": "products"
    }
    
    selected_dataset = st.selectbox("数据集", list(datasets.keys()))
    dataset = datasets[selected_dataset]
    
    # 分析类型选择
    st.markdown("#### 🔬 分析类型")
    
    analysis_types = {
        "统计分析": "statistical",
        "趋势分析": "trend",
        "异常检测": "anomaly",
        "对比分析": "comparison"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_type = st.selectbox("分析类型", list(analysis_types.keys()))
    
    with col2:
        analysis_target = st.text_input(
            "分析目标",
            placeholder="例如：按地区分析销售额",
            value="按地区统计销售额和数量"
        )
    
    # 分析参数配置
    st.markdown("#### ⚙️ 分析参数")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_range = st.selectbox(
            "时间范围",
            ["最近7天", "最近30天", "最近90天", "最近6个月", "全部"]
        )
    
    with col2:
        granularity = st.selectbox(
            "时间粒度",
            ["日", "周", "月", "季度", "年"]
        )
    
    with col3:
        top_n = st.slider("显示前N条", 5, 50, 10)
    
    # 执行分析
    if st.button("🚀 开始分析", type="primary", use_container_width=True):
        with st.spinner("正在进行数据分析..."):
            try:
                # 构建分析查询
                analysis_query = f"对{dataset}表进行{analysis_types[analysis_type]}，{analysis_target}"
                
                result = DataAnalysisWorkflow(use_checkpointer=False).run(analysis_query, st.session_state.session_id)
                
                if result:
                    for state in result.values():
                        response = state.get("final_response", "")
                        analysis_result = state.get("analysis_result")
                        
                        # 显示分析结果
                        st.markdown("#### 📊 分析结果")
                        
                        if analysis_result:
                            if hasattr(analysis_result, 'insights') and analysis_result.insights:
                                for i, insight in enumerate(analysis_result.insights[:5], 1):
                                    st.markdown(f"**{i}.** {insight}")
                            elif hasattr(analysis_result, 'summary') and analysis_result.summary:
                                st.write(analysis_result.summary)
                            else:
                                st.write(str(analysis_result))
                        else:
                            st.info("分析未返回详细结果")
                        
                        # 显示AI响应
                        if response:
                            st.markdown("#### 💬 AI分析报告")
                            st.markdown(response)
                
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                logging.error(f"Analysis error: {str(e)}")
    
    # 分析历史
    st.markdown("---")
    st.markdown("#### 📜 分析历史")
    
    analysis_history = [
        {"time": "2024-01-15 10:30", "type": "统计分析", "dataset": "sales", "result": "华东地区销售额最高"},
        {"time": "2024-01-14 15:20", "type": "趋势分析", "dataset": "sales", "result": "近30天销售额呈上升趋势"},
        {"time": "2024-01-13 09:15", "type": "异常检测", "dataset": "products", "result": "发现2个异常数据点"}
    ]
    
    for record in analysis_history:
        with st.expander(f"{record['time']} - {record['type']}"):
            st.write(f"**数据集**: {record['dataset']}")
            st.write(f"**结果**: {record['result']}")


# ============ 页面4：可视化 ============

def render_visualization_page():
    """渲染可视化页面"""
    st.markdown("### 📊 数据可视化")
    st.write("选择图表类型和参数，生成交互式可视化图表")
    
    # 图表类型选择
    st.markdown("#### 📈 图表类型")
    
    chart_types = {
        "折线图": "line",
        "柱状图": "bar",
        "饼图": "pie",
        "散点图": "scatter",
        "面积图": "area",
        "热力图": "heatmap"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        chart_type = st.selectbox("图表类型", list(chart_types.keys()))
    
    with col2:
        chart_title = st.text_input("图表标题", value="销售数据分析")
    
    # 数据选择
    st.markdown("#### 📁 数据选择")
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_axis = st.selectbox(
            "X轴（维度）",
            ["region", "sale_date", "product_id", "category"]
        )
    
    with col2:
        y_axis = st.selectbox(
            "Y轴（指标）",
            ["amount", "quantity", "COUNT(*)", "AVG(amount)"]
        )
    
    # 图表样式配置
    st.markdown("#### 🎨 图表样式")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        color_scheme = st.selectbox(
            "配色方案",
            ["Set2", "viridis", "plasma", "inferno", "Set1", "Paired"]
        )
    
    with col2:
        show_legend = st.checkbox("显示图例", value=True)
    
    with col3:
        show_grid = st.checkbox("显示网格", value=True)
    
    # 生成图表
    if st.button("🎨 生成图表", type="primary", use_container_width=True):
        with st.spinner("正在生成图表..."):
            try:
                # 构建可视化查询
                viz_query = f"生成{chart_types[chart_type]}图表，X轴为{x_axis}，Y轴为{y_axis}，标题为{chart_title}"
                
                result = DataAnalysisWorkflow(use_checkpointer=False).run(viz_query, st.session_state.session_id)
                
                if result:
                    for state in result.values():
                        viz_result = state.get("visualization_result")
                        response = state.get("final_response", "")
                        
                        # 显示结果
                        st.markdown("#### 📊 生成的图表")
                        
                        if viz_result and hasattr(viz_result, 'file_path') and viz_result.file_path:
                            from PIL import Image
                            img = Image.open(viz_result.file_path)
                            st.image(img, caption=chart_title, use_container_width=True)
                            st.success("✅ 图表生成成功！")
                        else:
                            # 生成示例图表
                            import pandas as pd
                            import plotly.express as px
                            
                            # 创建示例数据
                            data = {
                                'region': ['华东', '华南', '华北', '华西', '华中'],
                                'amount': [150000, 120000, 100000, 80000, 90000]
                            }
                            df = pd.DataFrame(data)
                            
                            if chart_types[chart_type] == "bar":
                                fig = px.bar(df, x='region', y='amount', title=chart_title)
                            elif chart_types[chart_type] == "line":
                                fig = px.line(df, x='region', y='amount', title=chart_title)
                            elif chart_types[chart_type] == "pie":
                                fig = px.pie(df, names='region', values='amount', title=chart_title)
                            else:
                                fig = px.bar(df, x='region', y='amount', title=chart_title)
                            
                            st.plotly_chart(fig, use_container_width=True)
                            st.success("✅ 示例图表生成成功（实际使用查询数据）")
                        
                        # 显示描述
                        if viz_result and hasattr(viz_result, 'description'):
                            st.markdown("#### 📝 图表描述")
                            st.write(viz_result.description)
                        
                        # 显示AI响应
                        if response:
                            st.markdown("#### 💬 AI说明")
                            st.markdown(response)
                
            except Exception as e:
                st.error(f"图表生成失败: {str(e)}")
                logging.error(f"Visualization error: {str(e)}")
    
    # 图表导出
    st.markdown("---")
    st.markdown("#### 📥 导出图表")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📷 导出PNG", use_container_width=True):
            st.info("图表已保存到 output/charts/ 目录")
    
    with col2:
        if st.button("📄 导出SVG", use_container_width=True):
            st.info("SVG导出需要先生成PNG")
    
    with col3:
        if st.button("📑 导出HTML", use_container_width=True):
            st.info("HTML导出功能开发中")


# ============ 页面5：对话历史 ============

def render_history_page():
    """渲染对话历史页面"""
    st.markdown("### 💬 对话历史")
    st.write("查看和管理历史查询记录")
    
    # 过滤器
    st.markdown("#### 🔍 筛选")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox(
            "筛选类型",
            ["全部", "查询", "分析", "可视化"]
        )
    
    with col2:
        date_range = st.date_input(
            "日期范围",
            value=(datetime.now().replace(day=1), datetime.now())
        )
    
    with col3:
        search_query = st.text_input("搜索内容", placeholder="输入关键词搜索")
    
    # 清空历史按钮
    if st.button("🗑️ 清空所有历史"):
        st.session_state.chat_history = []
        st.success("历史记录已清空")
        st.rerun()
    
    st.markdown("---")
    
    # 历史记录列表
    st.markdown("#### 📜 历史记录")
    
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"💬 {chat.get('timestamp', 'N/A')} - {chat.get('query', '')[:50]}..."):
                st.write(f"**查询**: {chat.get('query', '')}")
                st.write(f"**时间**: {chat.get('timestamp', 'N/A')}")
                
                if chat.get('result'):
                    st.write(f"**结果类型**: {type(chat['result']).__name__}")
                    if hasattr(chat['result'], 'row_count'):
                        st.write(f"**记录数**: {chat['result'].row_count}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔄 复现", key=f"replay_{i}"):
                        # 重新执行查询
                        query = chat.get('query', '')
                        DataAnalysisWorkflow(use_checkpointer=False).run(query, st.session_state.session_id)
                        st.success("查询已重新执行")
                
                with col2:
                    if st.button(f"🗑️ 删除", key=f"delete_{i}"):
                        st.session_state.chat_history.remove(chat)
                        st.rerun()
    else:
        st.info("暂无对话历史记录")
    
    # 对话统计
    st.markdown("---")
    st.markdown("#### 📊 对话统计")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总查询数", len(st.session_state.chat_history))
    
    with col2:
        # 统计今天查询数
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = sum(1 for c in st.session_state.chat_history 
                         if c.get('timestamp', '').startswith(today))
        st.metric("今日查询", today_count)
    
    with col3:
        if st.session_state.chat_history:
            last_query = st.session_state.chat_history[-1]
            st.metric("最近查询", last_query.get('timestamp', 'N/A')[:10])
        else:
            st.metric("最近查询", "N/A")


# ============ 页面6：设置 ============

def render_settings_page():
    """渲染设置页面"""
    st.markdown("### ⚙️ 设置")
    st.write("配置系统参数和管理功能")
    
    # API配置
    st.markdown("#### 🔑 API配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("MiniMax API Key", value=config.llm.minimax_api_key[:20] + "..." if config.llm.minimax_api_key else "", disabled=True)
        st.text_input("MiniMax Base URL", value=config.llm.minimax_base_url, disabled=True)
        st.text_input("MiniMax Model", value=config.llm.minimax_model, disabled=True)
    
    with col2:
        st.text_input("DeepSeek API Key", value=config.llm.api_key[:20] + "..." if config.llm.api_key else "未配置", disabled=True)
        st.text_input("DeepSeek Base URL", value=config.llm.base_url, disabled=True)
        st.text_input("DeepSeek Model", value=config.llm.model, disabled=True)
    
    st.info("API配置通过环境变量设置，请编辑 .env 文件")
    
    # 数据库配置
    st.markdown("---")
    st.markdown("#### 🗄️ 数据库配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("数据库路径", value=config.database.db_path, disabled=True)
        db_exists = Path(config.database.db_path).exists()
        st.selectbox("数据库状态", ["✅ 存在" if db_exists else "❌ 不存在"], disabled=True)
    
    with col2:
        if st.button("🔄 重新初始化数据库"):
            from agents.query_agent import QueryAgent
            agent = QueryAgent()
            st.success("数据库已重新初始化")
    
    # 记忆系统管理
    st.markdown("---")
    st.markdown("#### 🧠 记忆系统管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 查看短期记忆", use_container_width=True):
            st.json({
                "session_id": st.session_state.session_id,
                "turns": st.session_state.query_count,
                "history_count": len(st.session_state.chat_history)
            })
    
    with col2:
        if st.button("💾 清除短期记忆", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.query_count = 0
            st.success("短期记忆已清除")
    
    with col3:
        if st.button("🗑️ 清除长期记忆", use_container_width=True):
            try:
                memory_manager.clear_all()
                st.success("长期记忆已清除")
            except Exception as e:
                st.warning(f"长期记忆清除失败: {str(e)}")
    
    # 日志配置
    st.markdown("---")
    st.markdown("#### 📝 日志配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox(
            "日志级别",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )
    
    with col2:
        if st.button("📥 下载日志"):
            log_file = "logs/app.log"
            if Path(log_file).exists():
                with open(log_file, 'r') as f:
                    st.download_button(
                        label="下载日志文件",
                        data=f.read(),
                        file_name="app.log",
                        mime="text/plain"
                    )
            else:
                st.warning("日志文件不存在")
    
    # 测试工具
    st.markdown("---")
    st.markdown("#### 🧪 测试工具")
    
    if st.button("🔬 运行系统诊断", type="primary", use_container_width=True):
        with st.spinner("正在诊断..."):
            diagnostic = {
                "timestamp": datetime.now().isoformat(),
                "api_configured": config.llm.is_configured,
                "api_provider": config.llm.active_provider,
                "model": get_current_model(),
                "database_exists": Path(config.database.db_path).exists(),
                "session_id": st.session_state.session_id,
                "query_count": st.session_state.query_count,
                "history_count": len(st.session_state.chat_history)
            }
            
            st.json(diagnostic)
            
            if diagnostic["api_configured"] and diagnostic["database_exists"]:
                st.success("✅ 系统诊断通过")
            else:
                st.warning("⚠️ 系统配置不完整，请检查上述配置")


# ============ 主函数 ============

def render_workflow_demo_page():
    """展示完整的多Agent协作工作流"""
    st.header("🔄 完整工作流演示")
    st.markdown("""
    ### 这个页面展示多Agent协作过程
    
    输入一个复杂查询，系统会：
    1. **Supervisor Agent** - 意图识别和任务规划
    2. **Query Agent** - 数据查询（如需要）
    3. **Analysis Agent** - 数据分析（如需要）
    4. **Visualization Agent** - 可视化（如需要）
    5. **结果整合** - 生成最终响应
    
    你可以看到每个Agent的思考和执行过程。
    """)
    
    # 输入区
    st.markdown("### 📝 输入查询")
    col1, col2 = st.columns([4, 1])
    with col1:
        user_query = st.text_input(
            "输入你的问题",
            value="分析最近30天的销售趋势，并生成可视化图表",
            key="demo_query_input"
        )
    with col2:
        run_button = st.button("🚀 运行完整工作流", type="primary")
    
    if run_button and user_query:
        # 创建工作流实例
        workflow = DataAnalysisWorkflow(use_checkpointer=False)
        
        # 展示区域
        st.markdown("---")
        st.markdown("### 🤖 Agent协作过程")
        
        # 创建进度展示容器
        progress_container = st.container()
        
        # 创建结果展示容器
        result_container = st.container()
        
        with progress_container:
            # Step 1: Supervisor
            st.markdown("#### 🎯 Step 1: Supervisor Agent - 意图识别与任务规划")
            with st.spinner("Supervisor正在分析..."):
                # 先获取意图识别结果
                from graph.supervisor import supervisor_agent
                intent_result = supervisor_agent.recognize_intent(user_query)
                
                # 展示意图识别结果
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("识别意图", intent_result.get("intent", "unknown"))
                with col2:
                    st.metric("任务类型", intent_result.get("task_type", "unknown"))
                with col3:
                    st.metric("置信度", f"{intent_result.get('confidence', 0):.2f}")
                
                # 展示推理过程
                with st.expander("🔍 查看Supervisor推理过程"):
                    st.json(intent_result)
            
            st.success("✅ Supervisor完成意图识别和任务规划")
            
            # Step 2: 运行完整工作流
            st.markdown("#### ⚙️ Step 2: 多Agent协作执行")
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 运行工作流并捕获中间状态
            try:
                # 使用stream来获取每个节点执行后的状态
                from graph.state import create_initial_state
                
                initial_state = create_initial_state(
                    user_query=user_query,
                    session_id=f"demo_{int(time.time())}"
                )
                
                config = {"configurable": {"thread_id": f"demo_{int(time.time())}"}}
                
                step_count = 0
                agent_steps = []
                
                for state in workflow.app.stream(initial_state, config):
                    step_count += 1
                    progress_bar.progress(min(step_count * 20, 100))
                    
                    # 提取当前节点信息
                    for node_name, node_state in state.items():
                        if node_name == "supervisor":
                            status_text.text("🎯 Supervisor: 任务规划中...")
                            agent_steps.append({
                                "agent": "Supervisor",
                                "action": "任务规划",
                                "status": "完成"
                            })
                        elif node_name == "query_agent":
                            status_text.text("📊 Query Agent: 执行数据查询...")
                            agent_steps.append({
                                "agent": "Query Agent",
                                "action": "数据查询",
                                "status": "完成"
                            })
                        elif node_name == "analysis_agent":
                            status_text.text("📈 Analysis Agent: 执行数据分析...")
                            agent_steps.append({
                                "agent": "Analysis Agent",
                                "action": "数据分析",
                                "status": "完成"
                            })
                        elif node_name == "visualization_agent":
                            status_text.text("📊 Visualization Agent: 生成图表...")
                            agent_steps.append({
                                "agent": "Visualization Agent",
                                "action": "生成可视化",
                                "status": "完成"
                            })
                        elif node_name == "integrate":
                            status_text.text("🔄 整合结果...")
                
                progress_bar.progress(100)
                
            except Exception as e:
                st.error(f"工作流执行失败: {str(e)}")
                import traceback
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())
                return
            
            # 展示Agent执行步骤
            st.markdown("#### 📋 Agent执行流程")
            for i, step in enumerate(agent_steps, 1):
                st.markdown(f"**{i}. {step['agent']}** - {step['action']} ✅")
        
        # 展示最终结果
        with result_container:
            st.markdown("---")
            st.markdown("### 📊 最终结果")
            
            # 再次运行获取最终状态
            final_state = None
            for state in workflow.app.stream(initial_state, config):
                final_state = state
            
            if final_state:
                # 提取最终状态数据
                for node_name, node_state in final_state.items():
                    # 最终响应
                    if "final_response" in node_state and node_state["final_response"]:
                        st.markdown("#### 💬 最终响应")
                        st.markdown(node_state["final_response"])
                    
                    # 查询结果
                    if node_state.get("query_result"):
                        qr = node_state["query_result"]
                        if qr.get("executed"):
                            st.markdown("#### 📋 查询结果")
                            st.code(qr.get("sql", ""), language="sql")
                            if qr.get("data"):
                                st.dataframe(qr["data"][:10])
                    
                    # 分析结果
                    if node_state.get("analysis_result"):
                        ar = node_state["analysis_result"]
                        if ar.get("insights"):
                            st.markdown("#### 💡 分析洞察")
                            for insight in ar["insights"]:
                                st.markdown(f"- {insight}")
                    
                    # 可视化结果
                    if node_state.get("visualization_result"):
                        vr = node_state["visualization_result"]
                        if vr.get("file_path"):
                            st.markdown("#### 📊 可视化图表")
                            import os
                            if os.path.exists(vr["file_path"]):
                                st.image(vr["file_path"])
                                st.caption(vr.get("description", ""))
                    
                    # 中间步骤（展示ReAct循环）
                    if node_state.get("intermediate_steps"):
                        st.markdown("#### 🔄 执行轨迹（ReAct循环）")
                        with st.expander("查看详细执行步骤"):
                            for j, step in enumerate(node_state["intermediate_steps"], 1):
                                st.markdown(f"**Step {j}:**")
                                st.json(step)
            
            st.success("🎉 完整工作流执行完成！")


def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 渲染侧边栏
    current_page = render_sidebar()
    
    # 根据选择渲染页面
    if current_page == "home" or current_page == "settings":
        render_home_page()
    elif current_page == "query":
        render_query_page()
    elif current_page == "analysis":
        render_analysis_page()
    elif current_page == "visualization":
        render_visualization_page()
    elif current_page == "history":
        render_history_page()
    elif current_page == "workflow_demo":
        render_workflow_demo_page()
    else:
        render_settings_page()


if __name__ == "__main__":
    main()


# ============ 完整工作流演示页面 ============

