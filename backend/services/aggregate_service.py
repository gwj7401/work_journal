# -*- coding: utf-8 -*-
"""
聚合AI摘要服务 - 季度总结 & 年度总结
数据来源优先级：已有月度总结 → 原始日志条目
"""
import httpx
from config import get_settings

settings = get_settings()

QUARTER_MONTHS = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
QUARTER_NAMES = {1: "第一季度", 2: "第二季度", 3: "第三季度", 4: "第四季度"}

QUARTERLY_PROMPT = """你是一名政府机关文秘，精通公文写作。请根据以下{quarter_name}月度工作总结，按照公文写作规范，生成一份正式的季度工作总结报告。

【格式要求】
- 标题：{dept_name}{year}年{quarter_name}工作总结
- 一、主要工作完成情况（综合本季度成果，重点突出，分项列述）
- 二、存在的主要问题（客观分析，1-3条）
- 三、下季度工作计划（具体可行，承上启下）
- 文风：严谨、简洁，符合党政机关公文规范
- 字数：1000字至1500字之间
- 不要出现"根据您提供的"等表述，直接以第一人称写总结

【本季度月度工作总结资料】
{content}

请直接输出标题和正文，无需其他说明。"""

ANNUAL_PROMPT = """你是一名政府机关文秘，精通公文写作。请根据以下全年各季度/月度工作总结，按照公文写作规范，生成一份正式的年度工作总结报告。

【格式要求】
- 标题：{dept_name}{year}年度工作总结
- 一、年度主要工作完成情况（综合全年重点工作成果，系统归纳）
- 二、存在的主要问题和不足
- 三、下一年度工作思路与计划
- 文风：高度凝练、严谨正式，符合党政机关年度公文规范
- 字数：1500字至2500字之间
- 不要出现"根据您提供的"等表述，直接以第一人称写总结

【本年度工作总结资料】
{content}

请直接输出标题和正文，无需其他说明。"""


async def _call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()


async def generate_quarterly_summary(
    year: int,
    quarter: int,
    monthly_summaries: list[dict],   # [{month, content}]
    journal_entries: list[dict],      # 兜底：原始日志 [{date, content, tags}]
    dept_name: str = None,
) -> str:
    dept = dept_name or settings.dept_name
    quarter_name = QUARTER_NAMES[quarter]
    months = QUARTER_MONTHS[quarter]

    # 优先使用月度总结，否则降级到原始日志
    sections = []
    covered = set()
    for ms in monthly_summaries:
        if ms["month"] in months:
            sections.append(f"## {ms['month']}月工作总结\n{ms['content']}")
            covered.add(ms["month"])

    # 对没有月度总结的月份，整理原始日志
    for m in months:
        if m in covered:
            continue
        m_entries = [e for e in journal_entries if int(e["date"][5:7]) == m]
        if m_entries:
            lines = [f"- 【{e['date']}】{e['content']}" for e in sorted(m_entries, key=lambda x: x["date"])]
            sections.append(f"## {m}月工作日志\n" + "\n".join(lines))

    if not sections:
        return f"{dept}{year}年{quarter_name}暂无工作记录。"

    content = "\n\n".join(sections)
    prompt = QUARTERLY_PROMPT.format(
        dept_name=dept, year=year, quarter_name=quarter_name, content=content
    )
    try:
        return await _call_ollama(prompt)
    except httpx.ConnectError:
        raise RuntimeError("无法连接Ollama服务，请确认服务已启动（端口11434）")
    except httpx.TimeoutException:
        raise RuntimeError("Ollama生成超时，请稍后重试")
    except Exception as e:
        raise RuntimeError(f"AI生成失败：{str(e)}")


async def generate_annual_summary(
    year: int,
    quarterly_summaries: list[dict],  # [{quarter, content}]
    monthly_summaries: list[dict],     # 兜底1：月度总结
    journal_entries: list[dict],       # 兜底2：原始日志
    dept_name: str = None,
) -> str:
    dept = dept_name or settings.dept_name

    sections = []

    if quarterly_summaries:
        # 最优：用季度总结
        for qs in sorted(quarterly_summaries, key=lambda x: x["quarter"]):
            sections.append(f"## {QUARTER_NAMES[qs['quarter']]}总结\n{qs['content']}")
    elif monthly_summaries:
        # 次优：用月度总结
        for ms in sorted(monthly_summaries, key=lambda x: x["month"]):
            sections.append(f"## {ms['month']}月工作总结\n{ms['content']}")
    else:
        # 兜底：原始日志
        for e in sorted(journal_entries, key=lambda x: x["date"]):
            sections.append(f"- 【{e['date']}】{e['content']}")

    if not sections:
        return f"{dept}{year}年暂无工作记录。"

    content = "\n\n".join(sections)
    prompt = ANNUAL_PROMPT.format(dept_name=dept, year=year, content=content)
    try:
        return await _call_ollama(prompt)
    except httpx.ConnectError:
        raise RuntimeError("无法连接Ollama服务，请确认服务已启动（端口11434）")
    except httpx.TimeoutException:
        raise RuntimeError("Ollama生成超时，请稍后重试")
    except Exception as e:
        raise RuntimeError(f"AI生成失败：{str(e)}")
