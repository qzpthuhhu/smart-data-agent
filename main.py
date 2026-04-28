"""
主入口模块
提供命令行接口和交互式使用方式
"""

import os
import sys
import argparse
import logging
from typing import Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config, validate_config, load_config_from_env
from graph.workflow import default_workflow, run_query, run_query_full, DataAnalysisWorkflow


# ============ 日志配置 ============

def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# ============ 命令行接口 ============

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能数据分析Agent系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础查询
  python main.py "显示最近一个月的销售额"
  
  # 分析查询
  python main.py "分析最近三个月的销售趋势"
  
  # 可视化查询
  python main.py "生成销售数据的可视化图表"
  
  # 交互模式
  python main.py --interactive
  
  # 指定会话
  python main.py --session my_session "查询销售额"
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="要执行的自然语言查询"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="启动交互模式"
    )
    
    parser.add_argument(
        "-s", "--session",
        default="default",
        help="会话ID (默认: default)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--show-steps",
        action="store_true",
        help="显示执行步骤"
    )
    
    parser.add_argument(
        "--api-key",
        help="设置API密钥"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # 设置API密钥
    if args.api_key:
        os.environ["DEEPSEEK_API_KEY"] = args.api_key
        load_config_from_env()
    
    # 验证配置
    is_valid, errors = validate_config()
    if not is_valid:
        logger.warning("配置验证警告:")
        for error in errors:
            logger.warning(f"  - {error}")
        logger.info("将使用模拟模式或部分功能可能受限")
    
    # 交互模式
    if args.interactive:
        run_interactive(args.session)
        return
    
    # 查询模式
    if args.query:
        execute_query(
            args.query,
            args.session,
            show_steps=args.show_steps
        )
    else:
        parser.print_help()


def execute_query(query: str, session_id: str = "default", show_steps: bool = False):
    """
    执行查询
    
    Args:
        query: 用户查询
        session_id: 会话ID
        show_steps: 是否显示执行步骤
    """
    logger = logging.getLogger(__name__)
    
    print(f"\n{'='*60}")
    print(f"查询: {query}")
    print(f"会话: {session_id}")
    print(f"{'='*60}\n")
    
    try:
        if show_steps:
            # 显示完整结果
            result = run_query_full(query, session_id)
            
            print("【执行步骤】")
            for i, step in enumerate(result.get("intermediate_steps", []), 1):
                agent = step.get("agent", "未知")
                action = step.get("action", "执行操作")
                print(f"  {i}. [{agent}] {action}")
            
            print("\n【查询结果】")
            query_result = result.get("query_result")
            if query_result:
                if query_result.data:
                    print(f"  - SQL: {query_result.sql}")
                    print(f"  - 记录数: {query_result.row_count}")
                else:
                    print(f"  - 错误: {query_result.error or '无数据'}")
            
            print("\n【分析结果】")
            analysis_result = result.get("analysis_result")
            if analysis_result:
                if analysis_result.insights:
                    for insight in analysis_result.insights[:3]:
                        print(f"  - {insight}")
                elif analysis_result.error:
                    print(f"  - 错误: {analysis_result.error}")
            
            print("\n【可视化】")
            viz_result = result.get("visualization_result")
            if viz_result:
                if viz_result.file_path:
                    print(f"  - 图表: {viz_result.file_path}")
                    print(f"  - 描述: {viz_result.description}")
                elif viz_result.error:
                    print(f"  - 错误: {viz_result.error}")
            
            print("\n【最终响应】")
            print("-" * 60)
            print(result.get("response", ""))
            print("-" * 60)
        
        else:
            # 简洁模式
            response = run_query(query, session_id)
            print(response)
        
        print("\n")
        
    except Exception as e:
        logger.error(f"执行查询失败: {e}")
        if "--debug" in sys.argv or "-d" in sys.argv:
            import traceback
            traceback.print_exc()
        print(f"\n错误: {str(e)}")


def run_interactive(session_id: str = "default"):
    """
    交互模式
    
    Args:
        session_id: 会话ID
    """
    print("\n" + "=" * 60)
    print("智能数据分析Agent - 交互模式")
    print("=" * 60)
    print("\n输入您的自然语言查询，按 Enter 执行")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清除会话历史")
    print("输入 'help' 查看帮助")
    print("-" * 60 + "\n")
    
    turn = 0
    
    while True:
        try:
            query = input(f"[{turn + 1}] 请输入查询: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ["quit", "exit", "q"]:
                print("\n感谢使用，再见！\n")
                break
            
            if query.lower() == "clear":
                from memory import memory_manager
                memory_manager.clear_session(session_id)
                print("会话历史已清除\n")
                continue
            
            if query.lower() == "help":
                print("\n【帮助】")
                print("  - 直接输入自然语言查询，如：'显示最近一个月的销售额'")
                print("  - 可以进行复杂分析，如：'分析不同地区的销售趋势'")
                print("  - 可以生成图表，如：'绘制销售数据的可视化图表'")
                print("  - 支持多轮对话，系统会记住上下文\n")
                continue
            
            # 执行查询
            execute_query(query, session_id)
            turn += 1
            
        except KeyboardInterrupt:
            print("\n\n操作已取消\n")
            break
        except Exception as e:
            print(f"\n错误: {str(e)}\n")


# ============ API接口 ============

class DataAnalysisAPI:
    """
    数据分析API封装类
    
    用于在其他Python代码中调用Agent系统
    """
    
    def __init__(self, session_id: str = "api_session"):
        """
        初始化API
        
        Args:
            session_id: 会话ID
        """
        self.session_id = session_id
        self.workflow = DataAnalysisWorkflow(use_checkpointer=True)
    
    def query(self, natural_query: str) -> dict:
        """
        执行查询
        
        Args:
            natural_query: 自然语言查询
            
        Returns:
            结果字典，包含:
            - response: 最终响应文本
            - query_result: 查询结果
            - analysis_result: 分析结果
            - visualization_result: 可视化结果
            - error: 错误信息（如有）
        """
        try:
            result = self.workflow.run(natural_query, self.session_id)
            
            if not result:
                return {"error": "处理失败"}
            
            for state in result.values():
                return {
                    "response": state.get("final_response", ""),
                    "query_result": state.get("query_result"),
                    "analysis_result": state.get("analysis_result"),
                    "visualization_result": state.get("visualization_result"),
                    "tasks": state.get("tasks", []),
                    "error": state.get("error")
                }
            
            return {"error": "未找到结果"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def query_simple(self, natural_query: str) -> str:
        """
        简单查询（只返回响应文本）
        
        Args:
            natural_query: 自然语言查询
            
        Returns:
            响应文本
        """
        result = self.query(natural_query)
        return result.get("response", result.get("error", "处理失败"))
    
    def reset(self):
        """重置会话"""
        from memory import memory_manager
        memory_manager.clear_session(self.session_id)


# ============ 便捷函数 ============

def create_api(session_id: str = "api_session") -> DataAnalysisAPI:
    """
    创建API实例
    
    Args:
        session_id: 会话ID
        
    Returns:
        DataAnalysisAPI实例
    """
    return DataAnalysisAPI(session_id)


# ============ 主程序入口 ============

if __name__ == "__main__":
    main()
