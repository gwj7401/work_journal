# -*- coding: utf-8 -*-
"""
AI摘要服务 - 调用本地 Ollama 生成公文格式月度总结
"""
import httpx
from config import get_settings

settings = get_settings()

GONGWEN_PROMPT_TEMPLATE = """你是一名政府机关文秘，精通公文写作。请根据以下工作日志内容，按照公文写作规范，生成一份正式的月度工作总结报告。

【格式要求】
- 标题：{dept_name}{year}年{month}月工作总结
- 一、主要工作完成情况（按工作类型分条列项，逐条概括，语言简洁有力）
- 二、存在的主要问题（客观分析不足之处，1-3条）
- 三、下月工作计划（结合本月工作，提出下月重点）
- 文风：严谨、简洁，用词得当，符合党政机关公文规范
- 字数：800字至1200字之间
- 不要出现"根据您提供的日志"等表述，直接以第三人称写总结内容

【本月工作日志】
{journal_content}

请直接输出标题和正文，无需其他说明。"""


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

    # 整理日志内容
    lines = []
    for entry in sorted(journal_entries, key=lambda x: x["date"]):
        tags_str = "、".join(entry.get("tags", [])) if entry.get("tags") else ""
        tag_part = f"[{tags_str}] " if tags_str else ""
        lines.append(f"【{entry['date']}】{tag_part}{entry['content']}")
    journal_content = "\n\n".join(lines)

    if not journal_content.strip():
        return f"{dept}{year}年{month}月无工作日志记录。"

    prompt = GONGWEN_PROMPT_TEMPLATE.format(
        dept_name=dept,
        year=year,
        month=month,
        journal_content=journal_content,
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
    except httpx.ConnectError:
        raise RuntimeError("无法连接Ollama服务，请确认服务已启动（端口11434）")
    except httpx.TimeoutException:
        raise RuntimeError("Ollama生成超时，请稍后重试")
    except Exception as e:
        raise RuntimeError(f"AI生成失败：{str(e)}")
