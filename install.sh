#!/bin/bash
# 安装脚本

echo "========================================"
echo "智能数据分析Agent系统 - 安装脚本"
echo "========================================"

# 检查Python版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "检测到Python版本: $python_version"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    python -m venv venv
    source venv/bin/activate
    echo "已激活虚拟环境"
fi

# 安装核心依赖
echo ""
echo "安装核心依赖..."

pip install --upgrade pip

# 安装LangGraph相关
pip install langgraph>=0.0.20
pip install langchain-core>=0.1.0

# 安装数据处理
pip install pandas>=1.5.0
pip install numpy>=1.21.0

# 安装可视化
pip install matplotlib>=3.5.0

# 安装可选依赖（向量数据库）
read -p "是否安装可选依赖（向量数据库）? (y/n): " install_optional
if [ "$install_optional" = "y" ]; then
    pip install chromadb>=0.4.0
    pip install sentence-transformers>=2.2.0
fi

# 复制环境变量示例
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "已创建.env文件，请编辑并填入您的API密钥"
fi

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，填入您的 DeepSeek API密钥"
echo "2. 运行: python main.py --interactive"
echo ""
