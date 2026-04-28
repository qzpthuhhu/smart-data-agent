# 智能数据分析Agent - 部署文档

## 📋 目录

1. [系统要求](#系统要求)
2. [快速部署](#快速部署)
3. [详细部署步骤](#详细部署步骤)
4. [配置说明](#配置说明)
5. [Docker部署](#docker部署)
6. [验证部署](#验证部署)
7. [常见问题](#常见问题)

---

## 系统要求

### 硬件要求
- CPU: 2核心以上
- 内存: 4GB以上
- 硬盘: 10GB以上可用空间

### 软件要求
- Python: 3.10+
- pip: 最新版本
- Git: 用于代码管理

---

## 快速部署

### 方式一：一键部署（推荐）

```bash
# 克隆项目
git clone <项目地址>
cd 智能数据分析Agent

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 方式二：手动部署

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入API密钥

# 4. 运行应用
streamlit run ui/app.py
```

---

## 详细部署步骤

### 第一步：克隆或复制项目

```bash
# 从云端文件系统复制
cp -r ./美团面试准备/智能数据分析Agent ~/smart_data_agent
cd ~/smart_data_agent
```

### 第二步：创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 第三步：安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 第四步：配置API密钥

```bash
# 编辑.env文件
nano .env

# 添加以下内容：
MINIMAX_API_KEY=你的MiniMax密钥
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=MiniMax-Text-01

# 或者使用DeepSeek：
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

### 第五步：创建必要目录

```bash
mkdir -p data logs output/charts tests/reports
```

### 第六步：初始化数据库

```bash
python3 -c "
from agents.query_agent import QueryAgent
agent = QueryAgent()
print('数据库初始化成功')
"
```

### 第七步：启动应用

```bash
# Web界面
streamlit run ui/app.py

# 或命令行模式
python main.py --interactive
```

---

## 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MINIMAX_API_KEY | MiniMax API密钥 | - |
| MINIMAX_BASE_URL | MiniMax API地址 | https://api.minimax.chat/v1 |
| MINIMAX_MODEL | MiniMax模型 | MiniMax-Text-01 |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | - |
| DEEPSEEK_BASE_URL | DeepSeek API地址 | https://api.deepseek.com/v1 |
| LOG_LEVEL | 日志级别 | INFO |
| DEBUG | 调试模式 | false |

### 配置文件

配置文件位于 `config.py`，包含以下模块：

- `LLMConfig`: LLM模型配置
- `DatabaseConfig`: 数据库配置
- `MemoryConfig`: 记忆系统配置
- `VisualizationConfig`: 可视化配置
- `AgentConfig`: Agent配置

---

## Docker部署

### 构建Docker镜像

```bash
# 构建镜像
docker build -t smart-data-agent .

# 或使用docker-compose
docker-compose up -d
```

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 访问应用

打开浏览器访问: http://localhost:8501

---

## 验证部署

### 1. 检查服务状态

```bash
# 检查进程
ps aux | grep streamlit

# 检查端口
netstat -tlnp | grep 8501
```

### 2. 运行测试

```bash
# 运行单次测试
python tests/test_suite.py

# 运行连续测试（10次）
python tests/test_suite.py --count 10

# 生成详细报告
python tests/test_suite.py --report
```

### 3. 检查日志

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

---

## 常见问题

### Q1: 启动失败，提示"API密钥未配置"

**解决**：
1. 检查 `.env` 文件是否存在
2. 确认API密钥是否正确填写
3. 验证API密钥是否有效

### Q2: 数据库初始化失败

**解决**：
```bash
# 删除旧数据库
rm -f data/sample.db

# 重新初始化
python3 -c "
from agents.query_agent import QueryAgent
agent = QueryAgent()
"
```

### Q3: 依赖安装失败

**解决**：
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q4: 端口被占用

**解决**：
```bash
# 修改端口
streamlit run ui/app.py --server.port 8502

# 或在.env中设置
STREAMLIT_SERVER_PORT=8502
```

### Q5: 内存不足

**解决**：
- 增加虚拟内存
- 减少测试并发数
- 清理不必要的进程

---

## 后续维护

### 更新代码

```bash
git pull
pip install -r requirements.txt --upgrade
```

### 备份数据

```bash
# 备份数据库
cp data/sample.db data/sample.db.bak

# 备份配置
cp .env .env.bak
```

### 恢复数据

```bash
# 恢复数据库
cp data/sample.db.bak data/sample.db

# 恢复配置
cp .env.bak .env
```

---

## 联系方式

如有问题，请查看：
- README.md - 项目说明
- docs/ - 详细文档
- logs/ - 运行日志
