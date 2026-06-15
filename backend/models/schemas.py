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


class SearchSource(str, Enum):
    """学术搜索来源"""
    ARXIV = "arxiv"                       # arXiv 预印本
    SEMANTIC_SCHOLAR = "semantic_scholar" # Semantic Scholar
    GOOGLE_SCHOLAR = "google_scholar"     # Google Scholar
    CROSSREF = "crossref"                 # Crossref
    OPENALEX = "openalex"                 # OpenAlex


class ReferenceFormat(str, Enum):
    """参考文献格式"""
    BIBTEX = "bibtex"
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    GB7714 = "gb7714"


class WritingTask(str, Enum):
    """写作任务类型"""
    SUMMARY = "summary"                   # 摘要
    TRANSLATE = "translate"               # 翻译
    POLISH = "polish"                     # 润色
    LITERATURE_REVIEW = "literature_review"  # 文献综述
    OUTLINE = "outline"                   # 大纲
    CITATION = "citation"                 # 引用格式化


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
    moderator_config: Optional["ModeratorConfig"] = Field(default=None, description="主持人配置，未设置时使用默认配置")


# ============================================================
# Moderator 主持人模型
# ============================================================

class ModeratorStrictness(str, Enum):
    """主持人严格程度"""
    LOOSE = "loose"           # 宽松，仅记录警告不拒绝
    NORMAL = "normal"         # 默认，轻度质量守门
    STRICT = "strict"         # 严格，主题漂移/重复论点一律拒绝写入


class TimeboxConfig(BaseModel):
    """时间片配置（驱动 Moderator 的节奏管理）"""
    model_config = ConfigDict(use_enum_values=True)

    max_tokens_per_turn: int = Field(default=400, ge=50, le=2000, description="单条发言最大 token 数")
    max_seconds_per_turn: int = Field(default=120, ge=10, le=1800, description="单条发言最大秒数")
    max_total_seconds: int = Field(default=600, ge=60, le=7200, description="Phase 1 总时长上限（秒）")
    poi_max_per_phase: int = Field(default=3, ge=0, le=10, description="每阶段最多 POI 次数")


class ModeratorConfig(BaseModel):
    """主持人配置——驱动辩论状态机的行为"""
    model_config = ConfigDict(use_enum_values=True)

    opening_max_rounds: int = Field(default=1, ge=1, le=3, description="立论阶段每方最多轮数")
    cross_exam_max_rounds: int = Field(default=2, ge=1, le=5, description="交叉质询阶段每方最多轮数")
    free_debate_max_turns: int = Field(default=4, ge=1, le=10, description="自由辩论总轮数")
    closing_max_rounds: int = Field(default=1, ge=1, le=3, description="总结陈词每方最多轮数")
    enable_poi: bool = Field(default=False, description="是否启用 POI（段间质询）")
    timebox_config: TimeboxConfig = Field(default_factory=TimeboxConfig, description="时间片配置")
    strictness: ModeratorStrictness = Field(default=ModeratorStrictness.NORMAL, description="质量守门严格程度")
    duplicate_threshold: float = Field(default=0.85, ge=0.5, le=1.0, description="论点去重相似度阈值")
    off_topic_threshold: float = Field(default=0.4, ge=0.1, le=0.9, description="主题漂移阈值（低于则警告）")


class TurnRequest(BaseModel):
    """Moderator 向单个 Speaker 发出的发言请求"""
    model_config = ConfigDict(use_enum_values=True)

    turn_id: str = Field(..., description="发言请求唯一ID，如 turn-001")
    speaker_id: str = Field(..., description="目标 speaker ID")
    phase: DebatePhase = Field(..., description="当前辩论阶段")
    round_index: int = Field(0, ge=0, description="阶段内轮次索引")
    timebox_max_tokens: int = Field(default=400, ge=50, le=2000, description="本次发言 token 上限")
    timebox_max_seconds: int = Field(default=120, ge=10, le=1800, description="本次发言秒数上限")


class ModeratorWarningType(str, Enum):
    """警告类型"""
    DUPLICATE = "duplicate"   # 论点重复
    OFF_TOPIC = "off_topic"   # 主题漂移
    TIMEOUT = "timeout"       # 超时
    INVALID_CITE = "invalid_cite"  # 引用不合法


class ModeratorWarning(BaseModel):
    """警告记录（可审计）"""
    model_config = ConfigDict(use_enum_values=True)

    speaker_id: str
    warning_type: ModeratorWarningType
    message: str
    argument_excerpt: Optional[str] = Field(default=None, description="被拒绝发言的简短摘要（便于审计）")
    timestamp: datetime = Field(default_factory=datetime.now)


class DebateSummary(BaseModel):
    """Phase 1 产出的结构化辩论总结，供 Phase 2.1 审理消费"""
    model_config = ConfigDict(use_enum_values=True)

    debate_id: str
    phase_durations: Dict[str, float] = Field(default_factory=dict, description="各阶段耗时（秒）")
    total_duration: float = Field(default=0.0, ge=0.0, description="Phase 1 总耗时（秒）")
    total_turns: int = Field(default=0, ge=0, description="有效发言总轮数")
    key_arguments: List[Argument] = Field(default_factory=list, description="核心论点精选（已通过质量守门）")
    warnings: List[ModeratorWarning] = Field(default_factory=list, description="警告记录")
    argument_index_ref: Optional[str] = Field(default=None, description="ArgumentIndex 的存储引用（文件路径/DB Key）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展字段")

    def summary_stats(self) -> Dict[str, int]:
        """返回警告数量的分类统计（供裁决时加权）"""
        stats: Dict[str, int] = {}
        for w in self.warnings:
            key = w.warning_type.value
            stats[key] = stats.get(key, 0) + 1
        return stats


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


# ============================================================
# 学术论文元数据与搜索
# ============================================================

class PaperMeta(BaseModel):
    """论文元数据"""
    model_config = ConfigDict(use_enum_values=True)

    title: str = Field(..., description="论文标题")
    authors: List[str] = Field(default_factory=list, description="作者列表")
    abstract: Optional[str] = Field(default=None, description="摘要")
    year: Optional[int] = Field(default=None, description="发表年份")
    venue: Optional[str] = Field(default=None, description="期刊/会议名称")
    pdf_url: Optional[str] = Field(default=None, description="PDF 下载链接")
    doi: Optional[str] = Field(default=None, description="DOI 编号")
    arxiv_id: Optional[str] = Field(default=None, description="arXiv 编号")
    url: List[str] = Field(default_factory=list, description="相关链接")
    tags: List[str] = Field(default_factory=list, description="标签/关键词")
    citation_count: Optional[int] = Field(default=None, description="被引用次数")
    source: Optional[SearchSource] = Field(default=None, description="搜索来源")
    id: Optional[str] = Field(default=None, description="来源平台内部 ID")

    def model_dump_bibtex(self) -> str:
        """导出为 BibTeX 字符串"""
        key = self.doi or self.arxiv_id or f"paper{self.year or ''}"
        authors_str = " and ".join(self.authors) if self.authors else ""
        lines = [f"@article{{{key},"]
        if self.title:
            lines.append(f"  title = {{{self.title}}},")
        if authors_str:
            lines.append(f"  author = {{{authors_str}}},")
        if self.year:
            lines.append(f"  year = {{{self.year}}},")
        if self.venue:
            lines.append(f"  journal = {{{self.venue}}},")
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        if self.arxiv_id:
            lines.append(f"  eprint = {{{self.arxiv_id}}},")
        if self.pdf_url:
            lines.append(f"  url = {{{self.pdf_url}}},")
        lines.append("}")
        return "\n".join(lines)


class SearchQuery(BaseModel):
    """学术搜索查询"""
    model_config = ConfigDict(use_enum_values=True)

    keyword: str = Field(..., description="关键词")
    year_min: Optional[int] = Field(default=None, description="起始年份")
    year_max: Optional[int] = Field(default=None, description="结束年份")
    venue: Optional[str] = Field(default=None, description="目标期刊/会议")
    max_results: int = Field(default=10, ge=1, le=200, description="最大返回条数")
    sources: List[SearchSource] = Field(default_factory=list, description="搜索来源列表")


class SearchResult(BaseModel):
    """学术搜索结果"""
    total_count: int = Field(..., description="命中总数")
    papers: List[PaperMeta] = Field(default_factory=list, description="论文列表")
    query: SearchQuery = Field(..., description="原始查询")
    used_time: float = Field(default=0.0, ge=0.0, description="耗时（秒）")


# ============================================================
# PDF 解析
# ============================================================

class PDFPage(BaseModel):
    """PDF 单页内容"""
    page_num: int = Field(..., ge=1, description="页码")
    text: str = Field(default="", description="页面文本")
    images_count: int = Field(default=0, ge=0, description="页面图像数量")


class PDFParseResult(BaseModel):
    """PDF 解析结果"""
    pages: List[PDFPage] = Field(default_factory=list, description="各页内容")
    full_text: Optional[str] = Field(default=None, description="全文")
    summary: Optional[str] = Field(default=None, description="论文摘要")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    sections: Dict[str, str] = Field(default_factory=dict, description="章节 -> 章节内容")
    tables: List[str] = Field(default_factory=list, description="表格文本")
    figures: List[str] = Field(default_factory=list, description="图注文本")
    references: List[str] = Field(default_factory=list, description="参考文献列表")
    metadata: Optional[PaperMeta] = Field(default=None, description="论文元数据")
    parse_time: float = Field(default=0.0, ge=0.0, description="解析耗时（秒）")


# ============================================================
# 参考文献管理
# ============================================================

class BibEntry(BaseModel):
    """BibTeX 条目"""
    key: str = Field(..., description="引用键（cite key）")
    entry_type: str = Field(default="article", description="条目类型，如 article/book")
    fields: Dict[str, str] = Field(default_factory=dict, description="字段键值对")
    raw: str = Field(default="", description="原始 BibTeX 字符串")


class ReferenceManager(BaseModel):
    """参考文献管理器"""
    entries: List[BibEntry] = Field(default_factory=list, description="BibTeX 条目列表")
    source_path: Optional[str] = Field(default=None, description="来源文件路径")


# ============================================================
# 写作任务
# ============================================================

class WritingRequest(BaseModel):
    """写作任务请求"""
    model_config = ConfigDict(use_enum_values=True)

    task_type: WritingTask = Field(..., description="任务类型")
    input_text: str = Field(..., description="待处理文本")
    context: Optional[str] = Field(default=None, description="背景信息/上下文")
    target_language: str = Field(default="zh-CN", description="目标语言")
    model_name: Optional[str] = Field(default=None, description="使用的模型名")
    extra_args: Dict[str, Any] = Field(default_factory=dict, description="额外参数")


class WritingResponse(BaseModel):
    """写作任务响应"""
    task_type: WritingTask = Field(..., description="任务类型")
    original: str = Field(..., description="原始输入文本")
    output: str = Field(..., description="生成输出文本")
    model_name: Optional[str] = Field(default=None, description="使用的模型名")
    used_time: float = Field(default=0.0, ge=0.0, description="耗时（秒）")
    citations: List[str] = Field(default_factory=list, description="相关引用")
