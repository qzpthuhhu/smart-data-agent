#!/bin/bash
# 智能数据分析Agent启动脚本

echo "=================================================="
echo "  智能数据分析Agent"
echo "=================================================="
echo ""

# 设置环境变量
export MINIMAX_API_KEY='sk-cp-i2fR6CGvVPegIgOK6yjZSZ0LENb3WkBoGP3fJrQgb2yaeQvgurY8ToY6AePD-mrIgg6bm0XOiBk48Y0xYnGzKS2fVzS485dQaILPnaKWIwtRbH4hVdqjwyc'

# 进入项目目录
cd ~/smart_data_agent

# 检查是否有参数
if [ "$1" == "--test" ]; then
    echo "运行测试..."
    python quick_test.py
elif [ "$1" == "--query" ]; then
    # 命令行查询模式
    shift
    if [ -z "$1" ]; then
        echo "用法: ./run.sh --query '你的查询'"
        exit 1
    fi
    echo "执行查询: $1"
    python -c "
import os
os.environ['MINIMAX_API_KEY'] = 'sk-cp-i2fR6CGvVPegIgOK6yjZSZ0LENb3WkBoGP3fJrQgb2yaeQvgurY8ToY6AePD-mrIgg6bm0XOiBk48Y0xYnGzKS2fVzS485dQaILPnaKWIwtRbH4hVdqjwyc'
from agents.query_agent import QueryAgent
agent = QueryAgent('./data/sample.db')
sql, explanation = agent.nl_to_sql('$1')
print(f'SQL: {sql}')
print(f'说明: {explanation}')
"
elif [ "$1" == "--ui" ]; then
    # 检查Streamlit是否安装
    if command -v streamlit &> /dev/null; then
        echo "启动Web界面..."
        streamlit run ui/app.py
    else
        echo "Streamlit未安装"
        echo "正在尝试安装Streamlit..."
        pip install streamlit -q
        if [ $? -eq 0 ]; then
            echo "安装成功，启动Web界面..."
            streamlit run ui/app.py
        else
            echo "安装失败，请手动安装: pip install streamlit"
            exit 1
        fi
    fi
else
    # 交互模式
    echo "启动交互模式..."
    echo "可用命令："
    echo "  --test    运行测试"
    echo "  --query   执行查询（如：./run.sh --query '显示销售额'）"
    echo "  --ui      启动Web界面"
    echo ""
    python main.py --interactive
fi
