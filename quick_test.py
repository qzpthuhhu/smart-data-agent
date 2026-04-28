#!/usr/bin/env python3
"""
快速测试脚本
验证智能数据分析Agent的核心功能
"""

import os
import sys

# 设置环境变量
os.environ['MINIMAX_API_KEY'] = 'sk-cp-i2fR6CGvVPegIgOK6yjZSZ0LENb3WkBoGP3fJrQgb2yaeQvgurY8ToY6AePD-mrIgg6bm0XOiBk48Y0xYnGzKS2fVzS485dQaILPnaKWIwtRbH4hVdqjwyc'

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 50)
    print("测试1: 模块导入")
    print("=" * 50)
    
    try:
        from config import config
        print("✓ config.py 导入成功")
        print(f"  提供商: {config.llm.active_provider}")
        print(f"  模型: {config.llm.minimax_model}")
    except Exception as e:
        print(f"✗ config.py 导入失败: {e}")
        return False
    
    try:
        from graph.state import AgentState
        print("✓ state.py 导入成功")
    except Exception as e:
        print(f"✗ state.py 导入失败: {e}")
        return False
    
    try:
        from agents.query_agent import QueryAgent
        print("✓ query_agent.py 导入成功")
    except Exception as e:
        print(f"✗ query_agent.py 导入失败: {e}")
        return False
    
    try:
        from graph.supervisor import SupervisorAgent
        print("✓ supervisor.py 导入成功")
    except Exception as e:
        print(f"✗ supervisor.py 导入失败: {e}")
        return False
    
    return True


def test_database():
    """测试数据库"""
    print("\n" + "=" * 50)
    print("测试2: 数据库")
    print("=" * 50)
    
    import sqlite3
    
    db_path = './data/sample.db'
    if not os.path.exists(db_path):
        print(f"✗ 数据库不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"✓ 数据库连接成功")
        print(f"  表: {tables}")
        
        # 获取记录数
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}表记录数: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False


def test_api():
    """测试API调用"""
    print("\n" + "=" * 50)
    print("测试3: API调用")
    print("=" * 50)
    
    try:
        from config import create_llm_call
        
        response = create_llm_call(
            system_prompt="你是一个友好的助手",
            user_prompt="请回复：测试成功",
            max_tokens=50
        )
        
        print("✓ API调用成功")
        print(f"  响应: {response[:50]}...")
        return True
    except Exception as e:
        print(f"✗ API调用失败: {e}")
        return False


def test_sql_generation():
    """测试SQL生成"""
    print("\n" + "=" * 50)
    print("测试4: SQL生成")
    print("=" * 50)
    
    try:
        from agents.query_agent import QueryAgent
        
        agent = QueryAgent('./data/sample.db')
        sql, explanation = agent.nl_to_sql('显示最近一个月的销售额')
        
        if sql:
            print("✓ SQL生成成功")
            print(f"  SQL: {sql}")
            return True
        else:
            print("✗ SQL为空")
            return False
    except Exception as e:
        print(f"✗ SQL生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  智能数据分析Agent - 快速测试")
    print("=" * 60 + "\n")
    
    results = {
        "模块导入": test_imports(),
        "数据库": test_database(),
        "API调用": test_api(),
        "SQL生成": test_sql_generation(),
    }
    
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！项目可以正常运行。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
