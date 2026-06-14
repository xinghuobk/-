"""
学术论文工具链 API
基于 FastAPI 的 Web 服务入口
"""
from __future__ import annotations

import sys
import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models.schemas import (
    SearchQuery,
    SearchResult,
    PaperMeta,
    WritingRequest,
    WritingResponse,
    PDFParseResult,
)


# ============================================================
# 本地请求/响应模型
# ============================================================

class PDFParseRequest(BaseModel):
    """PDF 解析请求"""
    pdf_path: str = Field(..., description="PDF 文件路径")


class BibTeXRequest(BaseModel):
    """BibTeX 格式转换请求"""
    bib_path: str = Field(..., description="BibTeX 文件路径")
    format: str = Field(..., pattern="^(apa|gb7714)$", description="目标格式：apa / gb7714")


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="学术论文工具链 API",
    description="学术论文搜索、解析、参考文献管理与写作辅助工具链",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 异常处理
# ============================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "ValueError"},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc: FileNotFoundError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "type": "FileNotFoundError"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


# ============================================================
# 健康检查
# ============================================================

@app.get(
    "/health",
    summary="健康检查",
    description="检查 API 服务是否正常运行",
)
def health_check() -> Dict[str, Any]:
    return {"status": "ok", "service": "academic-paper-toolchain"}


# ============================================================
# 搜索接口
# ============================================================

@app.post(
    "/api/v1/search",
    summary="学术论文搜索",
    description="根据关键词、年份范围、期刊等条件在多源平台上搜索论文",
    response_model=SearchResult,
)
def search_papers(query: SearchQuery) -> SearchResult:
    from src.search.engine import unified_search

    try:
        return unified_search(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# PDF 解析接口
# ============================================================

@app.post(
    "/api/v1/parse/pdf",
    summary="PDF 论文解析",
    description="解析本地 PDF 文件，提取文本、章节、参考文献、元数据等",
    response_model=PDFParseResult,
)
def parse_pdf_endpoint(request: PDFParseRequest) -> PDFParseResult:
    from src.parse.pdf_parser import parse_pdf

    try:
        return parse_pdf(request.pdf_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 参考文献接口
# ============================================================

@app.post(
    "/api/v1/reference/generate-bibtex",
    summary="从论文元数据生成 BibTeX",
    description="根据 PaperMeta 生成标准的 BibTeX 引用条目字符串",
)
def generate_bibtex(paper: PaperMeta) -> Dict[str, str]:
    from src.reference.bibtex_manager import generate_bibtex_from_paper

    try:
        bibtex = generate_bibtex_from_paper(paper)
        return {"bibtex": bibtex}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _bibtex_to_apa(entry_key: str, fields: Dict[str, str]) -> str:
    authors = fields.get("author", "Unknown")
    title = fields.get("title", "")
    journal = fields.get("journal", fields.get("booktitle", ""))
    year = fields.get("year", "")
    volume = fields.get("volume", "")
    pages = fields.get("pages", "")
    doi = fields.get("doi", "")

    parts = [f"{authors} ({year}). {title}."]
    if journal:
        journal_part = journal
        if volume:
            journal_part += f", {volume}"
        if pages:
            journal_part += f", {pages}"
        parts[-1] = parts[-1] + " " + journal_part + "."
    if doi:
        parts.append(f"https://doi.org/{doi}")
    return " ".join(parts)


def _bibtex_to_gb7714(entry_key: str, fields: Dict[str, str]) -> str:
    authors = fields.get("author", "Unknown")
    title = fields.get("title", "")
    journal = fields.get("journal", fields.get("booktitle", ""))
    year = fields.get("year", "")
    volume = fields.get("volume", "")
    pages = fields.get("pages", "")
    doi = fields.get("doi", "")

    authors_cn = authors.replace(" and ", ", ")
    parts = [f"{authors_cn}. {title}[J]. {journal}"]
    if year:
        parts[-1] += f", {year}"
    if volume:
        parts[-1] += f", {volume}"
    if pages:
        parts[-1] += f": {pages}"
    parts[-1] += "."
    if doi:
        parts.append(f"DOI: {doi}.")
    return " ".join(parts)


def _parse_simple_bibtex(text: str):
    entries = []
    import re

    pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)
    pos = 0
    while pos < len(text):
        m = pattern.search(text, pos)
        if not m:
            break
        entry_type = m.group(1).lower()
        key = m.group(2)
        brace_depth = 0
        i = m.end()
        started = False
        while i < len(text):
            ch = text[i]
            if ch == "{":
                brace_depth += 1
                started = True
            elif ch == "}":
                brace_depth -= 1
                if started and brace_depth == 0:
                    break
            i += 1
        body = text[m.end():i]
        fields: Dict[str, str] = {}
        field_pattern = re.compile(r"(\w+)\s*=\s*(?:\{([^{}]*)\}|\"([^\"]*)\"|([^,\n}]+))", re.DOTALL)
        for fm in field_pattern.finditer(body):
            fname = fm.group(1).strip().lower()
            fval = fm.group(2) or fm.group(3) or fm.group(4) or ""
            fields[fname] = fval.strip()
        entries.append((key, entry_type, fields))
        pos = i + 1
    return entries


@app.post(
    "/api/v1/reference/to-format",
    summary="将 BibTeX 转换为指定引用格式",
    description="加载 BibTeX 文件并转换为 APA 或 GB7714 格式",
)
def convert_bibtex_to_format(request: BibTeXRequest) -> Dict[str, str]:
    try:
        if not os.path.exists(request.bib_path):
            raise FileNotFoundError(f"BibTeX 文件不存在: {request.bib_path}")

        with open(request.bib_path, "r", encoding="utf-8") as f:
            bib_text = f.read()

        entries = _parse_simple_bibtex(bib_text)
        formatted_lines = []
        for key, etype, fields in entries:
            if request.format == "apa":
                formatted_lines.append(_bibtex_to_apa(key, fields))
            elif request.format == "gb7714":
                formatted_lines.append(_bibtex_to_gb7714(key, fields))

        return {"result": "\n\n".join(formatted_lines)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 写作接口
# ============================================================

def _get_writer():
    from src.writer.llm_helper import AcademicWriter
    return AcademicWriter()


@app.post(
    "/api/v1/write/summary",
    summary="学术文本摘要",
    description="对输入的学术文本进行摘要总结",
    response_model=WritingResponse,
)
def write_summary(request: WritingRequest) -> WritingResponse:
    try:
        writer = _get_writer()
        return writer.summarize_text(request.input_text, context=request.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/write/translate",
    summary="学术文本翻译",
    description="对输入的学术文本进行翻译（支持中英互译）",
    response_model=WritingResponse,
)
def write_translate(request: WritingRequest) -> WritingResponse:
    try:
        writer = _get_writer()
        return writer.translate_academic(
            request.input_text,
            target_language=request.target_language,
            context=request.context,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/write/polish",
    summary="学术文本润色",
    description="对输入的学术文本进行润色和风格优化",
    response_model=WritingResponse,
)
def write_polish(request: WritingRequest) -> WritingResponse:
    try:
        writer = _get_writer()
        return writer.polish_paragraph(request.input_text, context=request.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/write/review",
    summary="文献综述生成",
    description="基于输入的多篇文献内容生成文献综述",
    response_model=WritingResponse,
)
def write_review(request: WritingRequest) -> WritingResponse:
    try:
        writer = _get_writer()
        return writer.generate_literature_review(request.input_text, context=request.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/write/outline",
    summary="生成论文大纲",
    description="根据主题或摘要生成结构化的论文大纲",
    response_model=WritingResponse,
)
def write_outline(request: WritingRequest) -> WritingResponse:
    try:
        writer = _get_writer()
        return writer.generate_outline(request.input_text, context=request.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
