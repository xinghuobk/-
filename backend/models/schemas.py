"""
核心数据模型定义
- 辩论配置、论点、发言、知识图谱节点/边、评分等
- 使用 Pydantic 2.x，保证类型安全和 JSON 序列化
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# 枚举类型
# ============================================================

class DebatePhase(str, Enum):
    """辩论阶段"""
    TOPIC_ANALYSIS = "topic_analysis"    # 辩题分析
    OPENING = "opening"                   # 立论阶段
    CROSS_EXAMINATION = "cross_examination"  # 交叉质询
    FREE_DEBATE = "free_debate"           # 自由辩论
    CLOSING = "closing"                   # 总结陈词
    JUDGMENT = "judgment"                 # 裁判评分
    DONE = "done"                         # 辩论结束


class AgentRole(str, Enum):
    """Agent 角色"""
    TOPIC_ANALYST = "topic_analyst"       # 辩题分析官
    PROPONENT = "proponent"               # 正方辩手
    OPPONENT = "opponent"                 # 反方辩手
    FACT_CHECKER = "fact_checker"         # 事实核查员
    LOGIC_ANALYST = "logic_analyst"       # 逻辑分析师
    JUDGE = "judge"                       # 辩论裁判
    REPORT_WRITER = "report_writer"       # 报告生成器


class ArgumentType(str, Enum):
    """论点类型"""
    CLAIM = "claim"                       # 核心主张
    EVIDENCE = "evidence"                 # 支撑论据
    REBUTTAL = "rebuttal"                 # 反驳论点
    EXAMPLE = "example"                   # 具体例子
    FALLACY = "fallacy"                   # 逻辑谬误标记


class EdgeType(str, Enum):
    """图谱关系类型"""
    SUPPORTS = "supports"                 # A 支持 B
    ATTACKS = "attacks"                   # A 攻击 / 反驳 B
    REFERS_TO = "refers_to"               # 引用某来源
    EXAMPLE_OF = "example_of"             # 是某论点的具体例子
    CONTRADICTS = "contradicts"           # 与某论点矛盾


class FactStatus(str, Enum):
    """事实核查状态"""
    VERIFIED = "verified"                 # 属实
    QUESTIONABLE = "questionable"         # 存疑
    UNVERIFIED = "unverified"             # 无来源
    FALLACIOUS = "fallacious"             # 存在谬误


class ModelProvider(str, Enum):
    """模型提供商"""
    MOCK = "mock"                         # 本地模拟（无 API Key）
    OPENAI = "openai"                     # OpenAI / 兼容协议
    DASHSCOPE = "dashscope"               # 通义千问


# ============================================================
# 配置模型
# ============================================================

class DebateConfig(BaseModel):
    """辩论配置"""
    model_config = ConfigDict(use_enum_values=True)

    topic: str = Field(..., description="辩题，例如：人工智能是否会取代人类大部分工作")
    pro_stance: str = Field(..., description="正方立场")
    con_stance: str = Field(..., description="反方立场")
    model_provider: ModelProvider = Field(default=ModelProvider.MOCK, description="模型提供商")
    model_name: str = Field(default="mock-model", description="具体模型名")
    max_rounds: int = Field(default=5, ge=1, le=10, description="辩论最大轮次")
    enable_fact_check: bool = Field(default=True, description="是否启用事实核查")
    enable_logic_analysis: bool = Field(default=True, description="是否启用逻辑分析")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="模型温度")


# ============================================================
# 论点与图谱节点
# ============================================================

class Argument(BaseModel):
    """单个论点"""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="论点唯一ID，如 arg-001")
    text: str = Field(..., description="论点内容")
    argument_type: ArgumentType = Field(default=ArgumentType.CLAIM)
    side: Optional[str] = Field(default=None, description="所属方：pro / con / neutral")
    source: Optional[str] = Field(default=None, description="引用来源")
    speaker_round: Optional[int] = Field(default=None, description="出现在哪一轮辩论")
    parent_id: Optional[str] = Field(default=None, description="父论点ID（用于层级关系）")


class GraphNode(BaseModel):
    """知识图谱节点"""
    model_config = ConfigDict(use_enum_values=True)

    id: str
    text: str
    node_type: ArgumentType
    side: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """知识图谱边"""
    model_config = ConfigDict(use_enum_values=True)

    from_id: str
    to_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArgumentGraph(BaseModel):
    """论点图谱序列化格式"""
    model_config = ConfigDict(use_enum_values=True)

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)

    # 图谱分析结果
    total_nodes: int = 0
    total_edges: int = 0
    pro_argument_count: int = 0
    con_argument_count: int = 0
    pro_attacked_count: int = 0
    con_attacked_count: int = 0
    most_central_node_id: Optional[str] = None


# ============================================================
# 发言与轮次
# ============================================================

class FactCheckResult(BaseModel):
    """事实核查结果"""
    model_config = ConfigDict(use_enum_values=True)

    status: FactStatus = FactStatus.UNVERIFIED
    issues: List[str] = Field(default_factory=list)
    verified_sources: List[str] = Field(default_factory=list)


class LogicAnalysisResult(BaseModel):
    """逻辑分析结果"""
    fallacies: List[str] = Field(default_factory=list, description="检测到的逻辑谬误列表")
    strength_score: float = Field(default=0.5, ge=0.0, le=1.0, description="逻辑强度评分")
    reasoning_quality: str = Field(default="fair", description="推理质量描述")


class DebateRound(BaseModel):
    """一轮辩论发言"""
    model_config = ConfigDict(use_enum_values=True)

    round_num: int
    phase: DebatePhase
    speaker: AgentRole
    content: str
    arguments: List[Argument] = Field(default_factory=list)
    fact_check: Optional[FactCheckResult] = None
    logic_analysis: Optional[LogicAnalysisResult] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================
# 辩题分析
# ============================================================

class TopicAnalysis(BaseModel):
    """辩题分析结果"""
    key_issues: List[str] = Field(default_factory=list, description="核心争议点")
    terms_definition: Dict[str, str] = Field(default_factory=dict, description="关键术语定义")
    boundaries: Optional[str] = Field(default=None, description="讨论边界")
    pro_arguments: List[str] = Field(default_factory=list, description="推荐正方论点")
    con_arguments: List[str] = Field(default_factory=list, description="推荐反方论点")


# ============================================================
# 评分与裁判
# ============================================================

class DimensionScore(BaseModel):
    """维度评分"""
    logic: float = Field(default=0.0, ge=0.0, le=100.0, description="逻辑性")
    evidence: float = Field(default=0.0, ge=0.0, le=100.0, description="论据质量")
    persuasion: float = Field(default=0.0, ge=0.0, le=100.0, description="说服力")
    rebuttal: float = Field(default=0.0, ge=0.0, le=100.0, description="反驳力度")

    @property
    def total(self) -> float:
        return round((self.logic + self.evidence + self.persuasion + self.rebuttal) / 4, 2)


class DebateJudgment(BaseModel):
    """裁判判决"""
    winner: str = Field(..., description="胜方：proponent / opponent / tie")
    pro_score: DimensionScore
    con_score: DimensionScore
    graph_based_score: Optional[Dict[str, float]] = Field(default=None, description="基于知识图谱的客观评分")
    key_insights: List[str] = Field(default_factory=list, description="关键洞察")
    summary: str = Field(..., description="裁判总结")


# ============================================================
# 完整辩论状态
# ============================================================

class DebateReport(BaseModel):
    """辩论报告（Markdown 格式）"""
    title: str
    content: str
    generated_at: datetime = Field(default_factory=datetime.now)


class DebateState(BaseModel):
    """完整辩论状态"""
    model_config = ConfigDict(use_enum_values=True)

    debate_id: str
    config: DebateConfig
    topic_analysis: Optional[TopicAnalysis] = None
    rounds: List[DebateRound] = Field(default_factory=list)
    argument_graph: Optional[ArgumentGraph] = None
    judgment: Optional[DebateJudgment] = None
    report: Optional[DebateReport] = None
    current_phase: DebatePhase = DebatePhase.TOPIC_ANALYSIS
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
