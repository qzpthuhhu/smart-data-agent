"""
workflow.py的补丁修复
修复checkpointer需要thread_id的问题
"""

# 读取原文件
with open('graph/workflow.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复run方法 - 添加config参数
old_run = '''    def run(self, query: str, session_id: str = "default", **kwargs):
        """
        运行工作流
        
        Args:
            query: 用户查询
            session_id: 会话ID
            **kwargs: 其他参数
            
        Returns:
            最终状态
        """
        # 创建初始状态
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id,
            turn=kwargs.get("turn", 0)
        )
        
        # 运行工作流
        final_state = None
        for state in self.app.stream(initial_state):
            final_state = state
        
        return final_state'''

new_run = '''    def run(self, query: str, session_id: str = "default", **kwargs):
        """
        运行工作流
        
        Args:
            query: 用户查询
            session_id: 会话ID
            **kwargs: 其他参数
            
        Returns:
            最终状态
        """
        # 创建初始状态
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id,
            turn=kwargs.get("turn", 0)
        )
        
        # 配置checkpointer所需的thread_id
        config = {"configurable": {"thread_id": session_id}}
        
        # 运行工作流
        final_state = None
        for state in self.app.stream(initial_state, config):
            final_state = state
        
        return final_state'''

content = content.replace(old_run, new_run)

# 写回文件
with open('graph/workflow.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成!")
