"""
配置管理模块
支持MiniMax、DeepSeek等多种LLM API
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class LLMConfig:
    """LLM配置"""
    # MiniMax API配置 (优先使用)
    minimax_api_key: str = field(default_factory=lambda: os.getenv("MINIMAX_API_KEY", ""))
    minimax_base_url: str = "https://api.minimax.chat/v1"
    minimax_model: str = "MiniMax-M2.7"
    
    # DeepSeek API配置 (备选)
    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    
    # 通用配置
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # 备选LLM配置
    backup_api_key: str = field(default_factory=lambda: os.getenv("BACKUP_API_KEY", ""))
    backup_base_url: str = field(default_factory=lambda: os.getenv("BACKUP_BASE_URL", ""))
    backup_model: str = "gpt-4"
    
    @property
    def is_configured(self) -> bool:
        """检查是否已配置API密钥"""
        return bool(self.minimax_api_key or self.api_key)
    
    @property
    def active_provider(self) -> str:
        """获取当前激活的API提供商"""
        if self.minimax_api_key:
            return "minimax"
        elif self.api_key:
            return "deepseek"
        elif self.backup_api_key:
            return "backup"
        return "none"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_path: str = "data/sample.db"
    
    tables: dict = field(default_factory=lambda: {
        "sales": {
            "columns": ["id", "product_id", "amount", "quantity", "sale_date", "region"],
            "primary_key": "id"
        },
        "products": {
            "columns": ["id", "name", "category", "price", "cost"],
            "primary_key": "id"
        }
    })


@dataclass
class MemoryConfig:
    """记忆模块配置"""
    chroma_persist_directory: str = "data/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    short_term_max_turns: int = 10
    long_term_threshold: float = 0.7


@dataclass
class VisualizationConfig:
    """可视化配置"""
    default_style: str = "seaborn-v0_8-darkgrid"
    figure_size: tuple = (10, 6)
    dpi: int = 100
    color_palette: str = "Set2"
    output_dir: str = "output/charts"


@dataclass
class AgentConfig:
    """Agent配置"""
    supervisor_model: str = "deepseek-chat"
    query_agent_model: str = "deepseek-chat"
    analysis_agent_model: str = "deepseek-chat"
    viz_agent_model: str = "deepseek-chat"
    query_max_retries: int = 3
    agent_timeout: int = 120


@dataclass
class AppConfig:
    """应用总配置"""
    debug: bool = True
    log_level: str = "INFO"
    project_root: Path = field(default_factory=Path)
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    def __post_init__(self):
        if self.project_root == Path:
            self.project_root = Path(__file__).parent
        self.database.db_path = str(self.project_root / self.database.db_path)
        self.memory.chroma_persist_directory = str(
            self.project_root / self.memory.chroma_persist_directory
        )
        self.visualization.output_dir = str(
            self.project_root / self.visualization.output_dir
        )


# 全局配置实例
config = AppConfig()


def load_config_from_env(prefix: str = "AGENT_") -> AppConfig:
    """从环境变量加载配置"""
    # MiniMax配置
    if os.getenv(f"{prefix}MINIMAX_API_KEY"):
        config.llm.minimax_api_key = os.getenv(f"{prefix}MINIMAX_API_KEY")
    if os.getenv(f"{prefix}MINIMAX_BASE_URL"):
        config.llm.minimax_base_url = os.getenv(f"{prefix}MINIMAX_BASE_URL")
    if os.getenv(f"{prefix}MINIMAX_MODEL"):
        config.llm.minimax_model = os.getenv(f"{prefix}MINIMAX_MODEL")
    
    # DeepSeek配置
    if os.getenv(f"{prefix}API_KEY"):
        config.llm.api_key = os.getenv(f"{prefix}API_KEY")
    if os.getenv(f"{prefix}BASE_URL"):
        config.llm.base_url = os.getenv(f"{prefix}BASE_URL")
    if os.getenv(f"{prefix}MODEL"):
        config.llm.model = os.getenv(f"{prefix}MODEL")
    
    # 数据库配置
    if os.getenv(f"{prefix}DB_PATH"):
        config.database.db_path = os.getenv(f"{prefix}DB_PATH")
        
    return config


def validate_config() -> tuple[bool, list]:
    """验证配置是否完整"""
    errors = []
    
    if not config.llm.is_configured:
        errors.append("未配置LLM API密钥，请设置MINIMAX_API_KEY或DEEPSEEK_API_KEY环境变量")
    
    db_path = Path(config.database.db_path)
    if not db_path.parent.exists():
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"无法创建数据库目录: {e}")
    
    return len(errors) == 0, errors


def get_llm_client():
    """获取LLM客户端（支持MiniMax和DeepSeek）"""
    try:
        from openai import OpenAI
        
        # 优先使用MiniMax
        if config.llm.minimax_api_key:
            client = OpenAI(
                api_key=config.llm.minimax_api_key,
                base_url=config.llm.minimax_base_url
            )
        elif config.llm.api_key:
            client = OpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
        else:
            raise ValueError("未配置任何LLM API密钥")
        
        return client
    except ImportError:
        raise ImportError("请安装openai库: pip install openai")


def get_current_model() -> str:
    """获取当前使用的模型名称"""
    if config.llm.minimax_api_key:
        return config.llm.minimax_model
    elif config.llm.api_key:
        return config.llm.model
    return "unknown"


def create_llm_call(system_prompt: str, user_prompt: str, **kwargs) -> str:
    """创建LLM调用"""
    try:
        client = get_llm_client()
        
        # 根据不同API设置模型
        if config.llm.minimax_api_key:
            model = config.llm.minimax_model
        else:
            model = config.llm.model
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get("temperature", config.llm.temperature),
            max_tokens=kwargs.get("max_tokens", config.llm.max_tokens)
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"LLM调用失败: {str(e)}")
