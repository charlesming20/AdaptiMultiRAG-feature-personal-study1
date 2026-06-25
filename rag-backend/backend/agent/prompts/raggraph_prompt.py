"""RAG Graph 相关提示词管理

本模块包含RAG图中各个节点使用的提示词模板。
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from typing import List


class RetrievalNeedDecision(BaseModel):
    """检索需求判断结果"""
    need_retrieval: bool = Field(description="是否需要进行检索")
    extracted_question: str = Field(description="提取的核心问题")
    reasoning: str = Field(description="判断是否需要检索的理由")


class SubquestionExpansion(BaseModel):
    """子问题扩展结果"""
    subquestions: List[str] = Field(description="扩展出的子问题列表")


class RetrievalTypeDecision(BaseModel):
    """检索类型判断结果"""
    retrieval_type: str = Field(description="推荐的检索类型：vector_only或graph_only")
    reasoning: str = Field(description="选择该检索类型的理由")


class RAGGraphPrompts:
    """RAG Graph 提示词集合"""

    @staticmethod
    def get_direct_answer_prompt() -> str:
        """获取直接回答节点的提示词（简化版，不使用记忆功能）
        
        Returns:
            直接回答的提示词模板
        """
        return """你是一个专业且友好的AI助手。请根据用户的问题提供准确、清晰的回答。

用户问题：
{question}

请直接回答用户的问题，保持回答的准确性和实用性。如果问题不清楚，可以要求用户提供更多信息。
"""

    @staticmethod
    def get_direct_answer_memory_prompt() -> str:
        """获取直接回答节点的记忆管理提示词（已弃用）
        """
        return f"""你是一个智能助手，拥有长期记忆功能。
    回答任何问题前一定要先对记忆进行回忆。
在回答用户问题前，请先调用 search_memory 工具，检查是否有相关记忆。
然后再决定是否需要调用 manage_memory 更新记忆。"""

    @staticmethod
    def get_retrieval_need_judgment_prompt() -> str:
        """获取判断是否需要检索的提示词
        
        Returns:
            判断检索需求的提示词模板
        """
        return """
你是一个智能的检索需求判断助手。你的任务是分析用户的问题，判断是否需要进行外部知识检索来回答这个问题。

请根据以下标准进行判断：

**需要检索的情况：**
1. 问题涉及具体的事实信息、数据、统计数字
2. 问题询问特定的人物、事件、地点、组织等
3. 问题需要最新的信息或时事
4. 问题涉及专业领域的具体知识
5. 问题询问具体的产品、服务、技术细节
6. 问题需要引用权威资料或文档

**不需要检索的情况：**
1. 纯粹的数学计算或逻辑推理
2. 一般性的概念解释或常识问题
3. 创意性问题（如写作、头脑风暴）
4. 个人观点或主观判断
5. 简单的定义或解释
6. 程序代码编写或调试（基础层面）

**用户问题：**
{question}

请分析这个问题，判断是否需要进行检索，并提取出核心问题。

**请按照以下格式输出你的判断结果：**

need_retrieval: [true/false] - 是否需要进行检索
extracted_question: [提取的核心问题] - 从用户问题中提取出的关键问题
reasoning: [判断理由] - 详细说明为什么需要或不需要检索的原因

确保你的回答准确反映问题的性质，并提供清晰的判断依据。

"""
    
    @staticmethod
    def get_retrieval_type_judgment_prompt() -> str:
        """获取判断检索类型的提示词
        
        Returns:
            判断检索类型的提示词模板
        """
        return """
你是一个智能的检索类型判断助手。你的任务是分析用户的问题，判断应该使用向量检索还是图检索来获取最相关的信息。

**向量检索 (vector_only) 适用场景：**
1. 语义相似性查询：寻找意思相近的内容
2. 模糊匹配：关键词不完全匹配但语义相关
3. 概念性问题：需要理解概念含义的查询
4. 文本内容检索：主要基于文档内容进行匹配
5. 跨语言查询：不同语言但相同含义的查询
6. 长文本查询：复杂的自然语言描述

**图检索 (graph_only) 适用场景：**
1. 关系查询：询问实体之间的关系
2. 路径查询：需要通过多个节点找到答案
3. 结构化查询：基于明确的实体和属性
4. 精确匹配：需要准确的实体或属性值
5. 层次查询：涉及分类、层级关系的问题
6. 连接查询：需要连接多个相关实体的信息

**用户问题：**
{question}

请分析这个问题的特点，判断应该使用哪种检索方式，并说明理由。

请按照以下JSON格式返回结果：
{{
    "retrieval_type": "vector_only" 或 "graph_only",
    "reasoning": "选择该检索类型的详细理由"
}}
"""
    
    @staticmethod
    def get_subquestion_expansion_prompt() -> str:
        """获取子问题扩展提示词"""
        return """
你是一个专业的问题分析助手。请根据用户的原始问题，将其分解为多个具体的子问题，以便更好地进行信息检索和回答。

分解原则：
1. 子问题应该涵盖原始问题的各个方面
2. 每个子问题应该具体明确，便于检索
3. 子问题之间应该相互补充，避免重复
4. 子问题数量通常在2-5个之间
5. 如果原始问题已经足够具体，可以只生成1个子问题（即原问题本身）

原始问题：{question}

请将上述问题分解为具体的子问题列表。
"""
    

    
    @staticmethod
    def get_answer_generation_prompt() -> str:
        """获取答案生成的提示词
        
        Returns:
            答案生成的提示词模板
        """
        return """
你是一个专业的知识整合助手。请基于检索到的相关文档，为用户问题提供准确、全面的答案。

**回答要求：**
1. 答案应该准确、客观、有条理
2. 优先使用检索到的权威信息
3. 如果信息不足，请明确指出
4. 提供信息来源和参考依据
5. 保持回答的简洁性和可读性

**用户问题：**
{question}

**检索到的相关文档（共{doc_count}个）：**
{documents}

"""