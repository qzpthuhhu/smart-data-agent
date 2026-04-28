"""
Memory Module - 记忆管理模块
提供短期记忆和长期记忆功能
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config import config


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    query: str = ""  # 原始查询
    response: str = ""  # 响应摘要
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """
    短期记忆管理
    
    功能：
    - 存储当前会话的对话历史
    - 提供上下文检索
    - 自动摘要和压缩
    """
    
    def __init__(self, max_turns: int = None):
        """
        初始化短期记忆
        
        Args:
            max_turns: 最大保留轮数
        """
        self.max_turns = max_turns or config.memory.short_term_max_turns
        self.entries: List[MemoryEntry] = []
        self.session_history: List[Dict[str, str]] = []
    
    def add(
        self,
        query: str,
        response: str,
        session_id: str = "default",
        metadata: Dict = None
    ) -> MemoryEntry:
        """
        添加记忆条目
        
        Args:
            query: 用户查询
            response: 系统响应
            session_id: 会话ID
            metadata: 元数据
            
        Returns:
            创建的记忆条目
        """
        entry = MemoryEntry(
            id=f"stm_{len(self.entries)}_{int(time.time())}",
            content=f"Q: {query}\nA: {response}",
            query=query,
            response=response,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        
        # 更新会话历史
        self.session_history.append({
            "query": query,
            "response": response,
            "timestamp": entry.timestamp
        })
        
        # 自动裁剪
        self._trim()
        
        return entry
    
    def get_recent(self, n: int = 5) -> List[MemoryEntry]:
        """
        获取最近的记忆
        
        Args:
            n: 获取数量
            
        Returns:
            记忆条目列表
        """
        return self.entries[-n:] if n > 0 else self.entries
    
    def get_context(self, max_entries: int = None) -> str:
        """
        获取上下文摘要
        
        Args:
            max_entries: 最大条目数
            
        Returns:
            上下文字符串
        """
        if not self.entries:
            return ""
        
        entries = self.get_recent(max_entries or self.max_turns)
        
        context_parts = ["## 最近的对话历史\n"]
        
        for i, entry in enumerate(entries, 1):
            context_parts.append(f"### 对话 {i}")
            context_parts.append(f"**时间**: {datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            context_parts.append(f"**查询**: {entry.query}")
            context_parts.append(f"**响应**: {entry.response[:200]}..." if len(entry.response) > 200 else f"**响应**: {entry.response}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def search(self, keyword: str) -> List[MemoryEntry]:
        """
        搜索包含关键词的记忆
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的条目
        """
        keyword_lower = keyword.lower()
        return [
            entry for entry in self.entries
            if keyword_lower in entry.content.lower()
        ]
    
    def clear(self, session_id: str = None):
        """
        清除记忆
        
        Args:
            session_id: 如果指定，只清除该会话的记忆；否则清除所有
        """
        if session_id:
            self.entries = [
                e for e in self.entries
                if e.session_id != session_id
            ]
            self.session_history = [
                h for h in self.session_history
                if h.get("session_id") != session_id
            ]
        else:
            self.entries.clear()
            self.session_history.clear()
    
    def _trim(self):
        """裁剪过长的记忆"""
        if len(self.entries) > self.max_turns:
            # 保留最近的条目
            self.entries = self.entries[-self.max_turns:]


class LongTermMemory:
    """
    长期记忆管理
    
    功能：
    - 基于Chroma向量库存储
    - 语义相似度检索
    - 用户偏好学习
    """
    
    def __init__(self, persist_directory: str = None):
        """
        初始化长期记忆
        
        Args:
            persist_directory: 向量库持久化目录
        """
        self.persist_directory = persist_directory or config.memory.chroma_persist_directory
        self.embedding_threshold = config.memory.long_term_threshold
        
        # 延迟初始化Chroma（可能未安装）
        self._client = None
        self._collection = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保Chroma已初始化"""
        if self._initialized:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings
            import sentence_transformers
            
            # 创建持久化目录
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # 初始化Chroma客户端
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 获取或创建集合
            self._collection = self._client.get_or_create_collection(
                name="agent_memory",
                metadata={"description": "Agent长期记忆存储"}
            )
            
            self._initialized = True
            
        except ImportError as e:
            print(f"警告: Chroma未安装，长期记忆功能不可用: {e}")
            self._initialized = False
        except Exception as e:
            print(f"警告: 初始化Chroma失败: {e}")
            self._initialized = False
    
    def add(
        self,
        content: str,
        query: str = "",
        response: str = "",
        metadata: Dict = None
    ) -> Optional[str]:
        """
        添加长期记忆
        
        Args:
            content: 记忆内容
            query: 原始查询
            response: 响应摘要
            metadata: 元数据
            
        Returns:
            记忆ID，失败返回None
        """
        self._ensure_initialized()
        
        if not self._initialized:
            return None
        
        try:
            memory_id = f"ltm_{int(time.time() * 1000)}"
            
            meta = {
                "query": query,
                "response": response,
                "timestamp": time.time(),
                **(metadata or {})
            }
            
            self._collection.add(
                documents=[content],
                ids=[memory_id],
                metadatas=[meta]
            )
            
            return memory_id
            
        except Exception as e:
            print(f"添加长期记忆失败: {e}")
            return None
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        threshold: float = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        搜索长期记忆
        
        Args:
            query: 搜索查询
            n_results: 返回数量
            threshold: 相似度阈值
            
        Returns:
            [(内容, 相似度, 元数据), ...]
        """
        self._ensure_initialized()
        
        if not self._initialized:
            return []
        
        threshold = threshold or self.embedding_threshold
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            memories = []
            
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if "distances" in results else 1.0
                    similarity = 1 - distance  # 转换为相似度
                    
                    if similarity >= threshold:
                        metadata = results["metadatas"][0][i] if "metadatas" in results else {}
                        memories.append((doc, similarity, metadata))
            
            return memories
            
        except Exception as e:
            print(f"搜索长期记忆失败: {e}")
            return []
    
    def get_recent(self, n: int = 10) -> List[Dict]:
        """
        获取最近的记忆
        
        Args:
            n: 返回数量
            
        Returns:
            记忆列表
        """
        self._ensure_initialized()
        
        if not self._initialized:
            return []
        
        try:
            # 获取所有记忆并按时间排序
            all_data = self._collection.get()
            
            if not all_data or not all_data.get("metadatas"):
                return []
            
            memories = []
            for i, metadata in enumerate(all_data["metadatas"]):
                memories.append({
                    "id": all_data["ids"][i],
                    "content": all_data["documents"][i] if "documents" in all_data else "",
                    **metadata
                })
            
            # 按时间排序
            memories.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            
            return memories[:n]
            
        except Exception as e:
            print(f"获取最近记忆失败: {e}")
            return []
    
    def delete(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        self._ensure_initialized()
        
        if not self._initialized:
            return False
        
        try:
            self._collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"删除记忆失败: {e}")
            return False
    
    def clear_all(self):
        """清除所有长期记忆"""
        self._ensure_initialized()
        
        if not self._initialized:
            return
        
        try:
            self._client.delete_collection(name="agent_memory")
            self._collection = self._client.get_or_create_collection(
                name="agent_memory"
            )
        except Exception as e:
            print(f"清除记忆失败: {e}")


class MemoryManager:
    """
    记忆管理器
    
    整合短期记忆和长期记忆，提供统一的接口
    """
    
    def __init__(self):
        """初始化记忆管理器"""
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
    
    def save_interaction(
        self,
        query: str,
        response: str,
        session_id: str = "default",
        metadata: Dict = None
    ):
        """
        保存交互到记忆
        
        Args:
            query: 用户查询
            response: 系统响应
            session_id: 会话ID
            metadata: 元数据
        """
        # 保存到短期记忆
        entry = self.short_term.add(query, response, session_id, metadata)
        
        # 如果交互重要，保存到长期记忆
        if self._should_save_long_term(query, response):
            self.long_term.add(
                content=f"查询: {query}\n响应: {response[:500]}",
                query=query,
                response=response[:200],
                metadata=metadata
            )
    
    def get_context(self, max_turns: int = None) -> str:
        """
        获取上下文
        
        Args:
            max_turns: 最大保留轮数
            
        Returns:
            上下文字符串
        """
        return self.short_term.get_context(max_turns)
    
    def search_memory(self, query: str) -> List[str]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            
        Returns:
            相关的记忆内容列表
        """
        # 先搜索长期记忆
        long_term_results = self.long_term.search(query)
        
        # 合并短期记忆搜索结果
        short_term_results = self.short_term.search(query)
        
        results = []
        
        for content, similarity, metadata in long_term_results:
            results.append(f"[长期记忆 - 相似度{similarity:.2f}]\n{content}")
        
        for entry in short_term_results:
            results.append(f"[短期记忆]\n{entry.content}")
        
        return results
    
    def get_context_with_memory(self, query: str) -> str:
        """
        获取包含记忆的上下文
        
        Args:
            query: 当前查询
            
        Returns:
            上下文字符串
        """
        context_parts = []
        
        # 添加短期记忆上下文
        short_context = self.short_term.get_context()
        if short_context:
            context_parts.append(short_context)
        
        # 搜索相关长期记忆
        related_memories = self.search_memory(query)
        if related_memories:
            context_parts.append("\n## 相关记忆\n")
            for memory in related_memories[:3]:  # 最多3条
                context_parts.append(memory)
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str = None):
        """
        清除会话记忆
        
        Args:
            session_id: 会话ID
        """
        self.short_term.clear(session_id)
    
    def _should_save_long_term(self, query: str, response: str) -> bool:
        """
        判断是否应该保存到长期记忆
        
        Args:
            query: 查询
            response: 响应
            
        Returns:
            是否保存
        """
        # 简单的启发式判断
        # 1. 响应较长（说明信息量大）
        if len(response) > 300:
            return True
        
        # 2. 包含关键分析或洞察
        keywords = ["分析", "发现", "趋势", "洞察", "建议", "结论"]
        if any(kw in response for kw in keywords):
            return True
        
        # 3. 用户明确表示重要
        important_keywords = ["记住", "保存", "重要", "下次"]
        if any(kw in query for kw in important_keywords):
            return True
        
        return False


# 创建全局实例
memory_manager = MemoryManager()


# 导出
__all__ = [
    "MemoryEntry",
    "ShortTermMemory",
    "LongTermMemory", 
    "MemoryManager",
    "memory_manager"
]
