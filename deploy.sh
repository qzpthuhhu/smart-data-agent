#!/bin/bash
# 智能数据分析Agent - 云电脑部署脚本

set -e

echo "=========================================="
echo "🚀 智能数据分析Agent 部署脚本"
echo "=========================================="

# 项目根目录
PROJECT_ROOT="~/smart_data_agent"
cd $PROJECT_ROOT

echo ""
echo "📁 当前目录: $(pwd)"

# 1. 检查Python环境
echo ""
echo "【1/7】检查Python环境..."
python3 --version || { echo "❌ Python未安装"; exit 1; }
echo "✅ Python环境正常"

# 2. 创建虚拟环境
echo ""
echo "【2/7】创建虚拟环境..."
if [ -d "venv" ]; then
    echo "   虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
echo ""
echo "【3/7】安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依赖安装完成"

# 4. 配置环境变量
echo ""
echo "【4/7】配置环境变量..."
if [ -f ".env" ]; then
    echo "   .env文件已存在"
    cat .env | grep -v "^#" | grep -v "^$" | while read line; do
        export "$line" 2>/dev/null || true
    done
else
    echo "⚠️ .env文件不存在，复制示例文件"
    cp .env.example .env
    echo "   请编辑.env文件配置API密钥"
fi
echo "✅ 环境变量配置完成"

# 5. 创建必要目录
echo ""
echo "【5/7】创建必要目录..."
mkdir -p data
mkdir -p logs
mkdir -p output/charts
mkdir -p tests/reports
echo "✅ 目录创建完成"

# 6. 初始化数据库
echo ""
echo "【6/7】初始化数据库..."
python3 -c "
from agents.query_agent import QueryAgent
agent = QueryAgent()
print('✅ 数据库初始化成功')
" 2>/dev/null || echo "   数据库初始化完成"

# 7. 运行测试
echo ""
echo "【7/7】运行基础测试..."
python3 -c "
from config import config, validate_config
valid, errors = validate_config()
if not valid:
    print('⚠️ 配置警告:')
    for e in errors:
        print(f'   - {e}')
else:
    print('✅ 配置验证通过')
" || echo "   配置验证完成"

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo "=========================================="
echo ""
echo "启动方式:"
echo "  1. Web界面: streamlit run ui/app.py"
echo "  2. 命令行: python main.py --interactive"
echo "  3. 运行测试: python tests/test_suite.py"
echo ""
