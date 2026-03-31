# -*- coding: utf-8 -*-
"""
AI摘要服务 - 调用本地 Ollama 生成公文格式月度总结
"""
import httpx
from config import get_settings

settings = get_settings()

import os
import re

GONGWEN_PROMPT_TEMPLATE = """你是一名政府机关文秘，精通公文写作。请根据以下工作日志内容，按照公文写作规范，生成一份正式的月度工作总结报告。

【格式要求】
- 标题：{dept_name}{year}年{month}月工作总结
- 一、主要工作完成情况（按工作类型分段落概括，语言简洁有力）
- 二、存在的主要问题（客观分析不足之处）
- 三、下月工作计划（结合本月工作，提出下月重点）
- 文风：严谨、简洁，用词得当，符合党政机关公文规范。段落开头请直接使用文字描述或“1.”、“2.”等明文编号，**绝对禁止使用“-”、“*”或“•”等无序列表符号**。
- 字数：800字至1200字之间
- 不要出现"根据您提供的日志"等表述，直接以第三人称写总结内容

【本月工作日志】
{journal_content}

请直接输出标题和正文，无需其他说明。"""

STRICT_SYSTEM_PROMPT = """你是党政机关公文写作助手。必须严格服从用户提示词中的结构、标题和风格要求，不得增删章节，不得添加开场白、解释、免责声明。输出仅为最终正文。"""

def get_custom_prompt(prompt_type: str) -> str:
    """尝试加载用户自定义的提示词模板文件"""
    # 这里将路径固定为用户工程约定的 docs/模板 下
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "模板", f"{prompt_type}提示词.txt")
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if "{journal_content}" in content:
                    return content
        except Exception:
            pass
    return None


def _is_monthly_structure_valid(text: str) -> bool:
    required = ["## 一、", "## 二、", "## 三、", "## 四、"]
    return all(item in text for item in required)


def _rewrite_followup_prompt(raw_prompt: str, first_output: str) -> str:
    return (
        f"{raw_prompt}\n\n"
        "你刚才的输出未完全遵循结构要求。请严格按提示词重写，必须包含四个二级标题：\n"
        "## 一、 核心业务与重点项目推进\n"
        "## 二、 内部管理与常规履职\n"
        "## 三、 思想建设与党风廉政\n"
        "## 四、 下阶段工作计划\n"
        "禁止输出任何说明性文字，只输出最终Markdown正文。\n\n"
        f"你上一次输出如下（仅供纠偏，不要照抄错误格式）：\n{first_output}"
    )


def _normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _render_template_from_logs(dept: str, year: int, month: int, journal_entries: list[dict]) -> str:
    core_lines = []
    internal_lines = []
    party_lines = []
    for entry in sorted(journal_entries, key=lambda x: x["date"]):
        content = _normalize_line(entry.get("content", ""))
        if not content:
            continue
        line = f"**{entry['date']}**：{content}"
        if re.search(r"(党|支部|党员|组织生活|廉政|警示教育|纪律|政绩观)", content):
            party_lines.append(line)
        elif re.search(r"(会议|培训|协调|管理|制度|设备|采购|评审|流程|保障|服务)", content):
            internal_lines.append(line)
        else:
            core_lines.append(line)
    if not core_lines:
        core_lines = internal_lines[:2] if internal_lines else ["本月围绕主责主业持续推进各项工作。"]
    if not internal_lines:
        internal_lines = ["本月持续推进内部协同、会议组织及业务保障工作。"]
    if not party_lines:
        party_lines = ["本月持续开展思想政治学习和作风建设，强化纪律意识与责任意识。"]
    plans = [
        "持续推进未完成的重点事项，明确节点、责任人和完成时限。",
        "强化党建与业务融合，将作风建设和能力提升转化为检验鉴定工作的实际成效。",
    ]
    return "\n".join(
        [
            f"# {dept}{year}年{month}月份工作总结",
            "",
            "## 一、 核心业务与重点项目推进",
            *core_lines,
            "",
            "## 二、 内部管理与常规履职",
            *internal_lines,
            "",
            "## 三、 思想建设与党风廉政",
            *party_lines,
            "",
            "## 四、 下阶段工作计划",
            *plans,
        ]
    ).strip()


def _looks_low_quality(text: str) -> bool:
    bad_phrases = ("请领导审阅", "根据您提供的", "好的，以下是")
    if any(p in text for p in bad_phrases):
        return True
    if len(text.strip()) < 650:
        return True
    return False


def _extract_coverage_info(summary_text: str, journal_entries: list[dict]) -> tuple[int, int, list[str]]:
    total_logs = len(journal_entries)
    if total_logs == 0:
        return 0, 0, []
    covered_dates = set()
    for entry in journal_entries:
        date_str = (entry.get("date") or "").strip()
        if not date_str:
            continue
        try:
            _, mm, dd = date_str.split("-")
            m = int(mm)
            d = int(dd)
        except Exception:
            continue
        patterns = [
            re.compile(rf"(?<!\d){re.escape(date_str)}(?!\d)"),
            re.compile(rf"(?<!\d)0?{m}月0?{d}日?"),
            re.compile(rf"(?<!\d)0?{m}[./-]0?{d}(?!\d)"),
        ]
        if any(p.search(summary_text) for p in patterns):
            covered_dates.add(date_str)
    unique_dates = sorted({(e.get("date") or "").strip() for e in journal_entries if (e.get("date") or "").strip()})
    missing_dates = [d for d in unique_dates if d not in covered_dates]
    return total_logs, len(covered_dates), missing_dates


def _prepend_coverage_hint(summary_text: str, journal_entries: list[dict]) -> str:
    total_logs, covered_dates_count, missing_dates = _extract_coverage_info(summary_text, journal_entries)
    if total_logs == 0:
        return summary_text
    coverage = covered_dates_count / max(1, len({e.get("date") for e in journal_entries if e.get("date")}))
    hint = f"覆盖率提示：本月共 {total_logs} 条日志，正文已覆盖 {covered_dates_count} 个日期（覆盖率 {coverage:.0%}）"
    if missing_dates:
        preview = "、".join(missing_dates[:8])
        if len(missing_dates) > 8:
            preview += " 等"
        hint += f"；未覆盖日期：{preview}"
    return f"{hint}\n\n{summary_text}".strip()


async def generate_monthly_summary(
    year: int,
    month: int,
    journal_entries: list[dict],
    dept_name: str = None,
) -> str:
    """
    调用 Ollama 生成月度总结，返回生成的文本内容。
    journal_entries: [{"date": "2025-03-01", "content": "...", "tags": ["开会"]}]
    """
    dept = dept_name or settings.dept_name

    def strip_img(text: str) -> str:
        if not text: return ""
        return re.sub(r'<img[^>]*>', '', re.sub(r'!\[.*?\]\([^)]*\)', '', text))

    # 整理日志内容
    lines = []
    for entry in sorted(journal_entries, key=lambda x: x["date"]):
        tags_str = "、".join(entry.get("tags", [])) if entry.get("tags") else ""
        tag_part = f"[{tags_str}] " if tags_str else ""
        safe_content = strip_img(entry['content'])
        lines.append(f"【{entry['date']}】{tag_part}{safe_content}")
    journal_content = "\n\n".join(lines)

    if not journal_content.strip():
        return f"{dept}{year}年{month}月无工作日志记录。"

    custom_prompt = get_custom_prompt("月度")
    template_to_use = custom_prompt if custom_prompt else GONGWEN_PROMPT_TEMPLATE

    try:
        prompt = template_to_use.format(
            dept_name=dept,
            year=year,
            month=month,
            journal_content=journal_content,
        )
    except KeyError as e:
        raise RuntimeError(f"月度提示词存在未定义占位符：{str(e)}")

    try:
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "system": STRICT_SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.85,
                        "repeat_penalty": 1.1,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            first = data.get("response", "").strip()
            if _is_monthly_structure_valid(first) and not _looks_low_quality(first):
                return _prepend_coverage_hint(first, journal_entries)

            retry_prompt = _rewrite_followup_prompt(prompt, first)
            retry_resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "system": STRICT_SYSTEM_PROMPT,
                    "prompt": retry_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.8,
                        "repeat_penalty": 1.12,
                    },
                },
            )
            retry_resp.raise_for_status()
            retry_data = retry_resp.json()
            second = retry_data.get("response", "").strip()
            if _is_monthly_structure_valid(second) and not _looks_low_quality(second):
                return _prepend_coverage_hint(second, journal_entries)
            return _prepend_coverage_hint(_render_template_from_logs(dept, year, month, journal_entries), journal_entries)
    except httpx.ConnectError:
        raise RuntimeError("无法连接Ollama服务，请确认服务已启动（端口11434）")
    except httpx.TimeoutException:
        raise RuntimeError("Ollama生成超时，请稍后重试")
    except Exception as e:
        raise RuntimeError(f"AI生成失败：{str(e)}")
