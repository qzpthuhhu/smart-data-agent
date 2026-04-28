#!/usr/bin/env python3
"""
MiniMax API测试和调用工具
"""

import os
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

import json
import time
from datetime import datetime

class MiniMaxAPITester:
    """MiniMax API测试器"""
    
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY", "")
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
        self.model = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
        self.client = None
        
    def test_connection(self) -> dict:
        """测试API连接"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "api_key_configured": bool(self.api_key),
            "api_key_preview": self.api_key[:20] + "..." if self.api_key else "未配置",
            "base_url": self.base_url,
            "model": self.model,
            "connection_status": "unknown",
            "error": None
        }
        
        if not self.api_key:
            result["connection_status"] = "failed"
            result["error"] = "API密钥未配置"
            return result
        
        try:
            from openai import OpenAI
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # 发送测试请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个助手"},
                    {"role": "user", "content": "请回复'连接成功'"}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            result["connection_status"] = "success"
            result["response"] = response.choices[0].message.content
            
        except Exception as e:
            result["connection_status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def test_multiple_calls(self, count: int = 5) -> dict:
        """测试多次调用稳定性"""
        results = {
            "total_calls": count,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_time": 0,
            "avg_time": 0,
            "calls": []
        }
        
        if not self.client:
            self.test_connection()
            if not self.client:
                results["error"] = "无法建立连接"
                return results
        
        for i in range(count):
            call_result = {
                "call_number": i + 1,
                "status": "unknown",
                "time": 0,
                "response": None,
                "error": None
            }
            
            start_time = time.time()
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": f"这是第{i+1}次测试，请回复'测试成功{i+1}'"}
                    ],
                    max_tokens=50
                )
                
                elapsed = time.time() - start_time
                
                call_result["status"] = "success"
                call_result["time"] = elapsed
                call_result["response"] = response.choices[0].message.content
                
                results["successful_calls"] += 1
                
            except Exception as e:
                elapsed = time.time() - start_time
                call_result["status"] = "failed"
                call_result["time"] = elapsed
                call_result["error"] = str(e)
                
                results["failed_calls"] += 1
            
            results["total_time"] += elapsed
            results["calls"].append(call_result)
            
            print(f"  第{i+1}次调用: {'✅' if call_result['status'] == 'success' else '❌'} ({call_result['time']:.3f}秒)")
            
            # 短暂休息
            if i < count - 1:
                time.sleep(0.5)
        
        results["avg_time"] = results["total_time"] / count if count > 0 else 0
        
        return results
    
    def test_data_analysis(self) -> dict:
        """测试数据分析场景"""
        test_queries = [
            "将'显示销售总额'转换为SQL语句",
            "分析以下数据的趋势：[100, 120, 150, 140, 180]",
            "用中文简要解释什么是数据分析"
        ]
        
        results = {
            "query_count": len(test_queries),
            "results": []
        }
        
        for query in test_queries:
            result = {
                "query": query,
                "status": "unknown",
                "response": None,
                "error": None
            }
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个数据分析专家，请简洁回答。"},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                result["status"] = "success"
                result["response"] = response.choices[0].message.content
                
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
            
            results["results"].append(result)
        
        return results


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔬 MiniMax API 测试工具")
    print("="*60)
    
    tester = MiniMaxAPITester()
    
    # 1. 测试连接
    print("\n【1】测试API连接...")
    print("-" * 40)
    connection_result = tester.test_connection()
    
    print(f"API密钥: {connection_result['api_key_preview']}")
    print(f"Base URL: {connection_result['base_url']}")
    print(f"模型: {connection_result['model']}")
    print(f"连接状态: {connection_result['connection_status']}")
    
    if connection_result.get("response"):
        print(f"测试响应: {connection_result['response']}")
    
    if connection_result.get("error"):
        print(f"错误信息: {connection_result['error']}")
    
    if connection_result["connection_status"] != "success":
        print("\n❌ 连接失败，请检查API密钥配置")
        print("\n配置方法:")
        print("1. 编辑 .env 文件")
        print("2. 设置 MINIMAX_API_KEY=你的密钥")
        print("3. 重启程序")
        return
    
    print("\n✅ API连接成功!")
    
    # 2. 测试多次调用
    print("\n【2】测试API调用稳定性 (5次)...")
    print("-" * 40)
    stability_result = tester.test_multiple_calls(5)
    
    print(f"\n成功: {stability_result['successful_calls']}/{stability_result['total_calls']}")
    print(f"失败: {stability_result['failed_calls']}/{stability_result['total_calls']}")
    print(f"总耗时: {stability_result['total_time']:.3f}秒")
    print(f"平均耗时: {stability_result['avg_time']:.3f}秒")
    
    # 3. 测试数据分析场景
    print("\n【3】测试数据分析场景...")
    print("-" * 40)
    analysis_result = tester.test_data_analysis()
    
    for i, res in enumerate(analysis_result["results"], 1):
        print(f"\n查询{i}: {res['query'][:30]}...")
        if res["status"] == "success":
            print(f"  响应: {res['response'][:100]}...")
        else:
            print(f"  错误: {res['error']}")
    
    # 保存测试报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "connection": connection_result,
        "stability": stability_result,
        "analysis": analysis_result
    }
    
    report_dir = project_root / "tests" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("✅ API测试完成")
    print("="*60)
    print(f"\n📄 测试报告已保存: {report_file}")
    
    return report


if __name__ == "__main__":
    main()
