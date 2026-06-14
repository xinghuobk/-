import sys
sys.path.insert(0, '.')

import json
import os
from datetime import datetime

from backend.models.schemas import SearchQuery, SearchSource, PaperMeta
from src.search.engine import unified_search
from src.search.arxiv_client import search_arxiv
from src.search.crossref_client import search_crossref
from src.search.semantic_scholar_client import search_semantic_scholar

# ====== 6 大领域关键词定义 ======
QUERIES = {
    "数学推理": [
        "multi-agent debate mathematics reasoning",
        "LLM debate math problem solving",
        "multi-agent mathematical theorem proving",
        "debate-style math verification",
    ],
    "物理科学": [
        "multi-agent physics reasoning",
        "LLM debate physics problem solving",
        "multi-agent scientific discovery physics",
        "debate-style scientific reasoning",
    ],
    "工程设计": [
        "multi-agent engineering design",
        "LLM collaborative engineering optimization",
        "multi-agent debate design optimization",
        "agent-based engineering decision making",
    ],
    "医疗诊断": [
        "multi-agent debate medical diagnosis",
        "LLM debate clinical decision making",
        "multi-agent medical reasoning benchmark",
        "doctor-agent debate healthcare",
    ],
    "法律推理": [
        "multi-agent debate legal reasoning",
        "LLM legal argument multi-agent",
        "multi-agent legal case analysis",
        "debate-style legal judgment",
    ],
    "热点信息研判": [
        "multi-agent fact-checking debate",
        "LLM debate information verification",
        "multi-agent rumor detection misinformation",
        "debate-style fake news detection",
    ],
}

# ====== 类似项目检索（用 Crossref 找项目名 + GitHub 类项目） ======
RELATED_PROJECTS = [
    "multi-agent debate system",
    "DebateGPT AI debate",
    "generative agents debate",
    "self-consistency debate LLM",
    "multi-agent reflection debate",
    "adversarial debate LLM safety",
]

# ====== 执行搜索 ======
def run_search(keyword, year_min=2022):
    """对单个关键词执行统一搜索（arXiv + Crossref + Semantic Scholar）"""
    try:
        result = unified_search(SearchQuery(
            keyword=keyword,
            year_min=year_min,
            max_results=10,
            sources=[SearchSource.ARXIV, SearchSource.CROSSREF, SearchSource.SEMANTIC_SCHOLAR],
        ))
        papers = []
        for p in result.papers:
            if hasattr(p, 'model_dump'):
                papers.append(p.model_dump())
            else:
                papers.append({
                    'title': getattr(p, 'title', ''),
                    'authors': getattr(p, 'authors', []),
                    'abstract': getattr(p, 'abstract', '')[:500],
                    'year': getattr(p, 'year', None),
                    'venue': getattr(p, 'venue', ''),
                    'citation_count': getattr(p, 'citation_count', 0),
                    'doi': getattr(p, 'doi', ''),
                    'source': str(getattr(p, 'source', '')),
                })
        return {
            'keyword': keyword,
            'total_count': result.total_count,
            'used_time': round(result.used_time, 3),
            'papers': papers,
        }
    except Exception as exc:
        return {'keyword': keyword, 'error': str(exc), 'total_count': 0, 'papers': []}

def main():
    output_dir = "/workspace/data/research"
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = {}
    
    # 每个领域执行 2~3 个关键词
    for domain, keywords in QUERIES.items():
        print(f"\n=== 正在检索领域: {domain} ===")
        domain_results = []
        for kw in keywords:
            print(f"  - {kw} ...")
            r = run_search(kw, year_min=2022)
            domain_results.append(r)
            print(f"    -> {r.get('total_count', '?')} 篇, 耗时 {r.get('used_time', '?')}s")
        all_results[domain] = domain_results
    
    # 类似项目检索
    print("\n=== 正在检索类似项目/系统 ===")
    project_results = []
    for kw in RELATED_PROJECTS:
        print(f"  - {kw} ...")
        r = run_search(kw, year_min=2021)
        project_results.append(r)
        print(f"    -> {r.get('total_count', '?')} 篇")
    all_results["类似项目"] = project_results
    
    # 汇总保存
    summary = {
        'generated_at': datetime.now().isoformat(),
        'domains': list(QUERIES.keys()),
        'results': all_results,
    }
    
    out_path = os.path.join(output_dir, "multi_agent_debate_research.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # 简单统计
    total_papers = 0
    for dom, items in all_results.items():
        for it in items:
            total_papers += len(it.get('papers', []))
    
    print(f"\n✓ 检索完成，共 {total_papers} 篇论文/条目")
    print(f"✓ 原始数据已保存到: {out_path}")
    
    # 同时保存为便于浏览的 txt
    out_txt = os.path.join(output_dir, "multi_agent_debate_research_summary.txt")
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(f"# 多智能体辩论系统 - 学术调研\n")
        f.write(f"# 生成时间: {summary['generated_at']}\n\n")
        for dom, items in all_results.items():
            f.write(f"\n## {dom}\n")
            f.write("=" * 60 + "\n\n")
            all_papers_in_domain = []
            for r in items:
                all_papers_in_domain.extend(r.get('papers', []))
            # 按 citation_count 排序去重
            seen = set()
            unique = []
            for p in all_papers_in_domain:
                key = (p.get('title') or '')[:80]
                if key and key not in seen:
                    seen.add(key)
                    unique.append(p)
            unique.sort(key=lambda p: -(p.get('citation_count') or 0))
            for idx, p in enumerate(unique[:15], 1):
                f.write(f"[{idx}] {p.get('title', '')}\n")
                if p.get('authors'):
                    f.write(f"    作者: {', '.join(p['authors'][:3])}\n")
                f.write(f"    年份: {p.get('year', '?')} | 引用: {p.get('citation_count', '?')} | 来源: {p.get('source', '')}\n")
                if p.get('venue'):
                    f.write(f"    期刊/会议: {p['venue']}\n")
                if p.get('doi'):
                    f.write(f"    DOI: {p['doi']}\n")
                if p.get('abstract'):
                    abs_text = str(p['abstract'])[:300].replace('\n', ' ')
                    f.write(f"    摘要: {abs_text}...\n")
                f.write("\n")
    print(f"✓ 摘要已保存到: {out_txt}")

if __name__ == "__main__":
    main()
