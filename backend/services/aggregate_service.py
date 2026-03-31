# -*- coding: utf-8 -*-
"""
聚合AI摘要服务 - 季度总结 & 年度总结
数据来源优先级：按行政级别逐层向上提取（不支持越级穿透底层记录）
"""
import re
import os
import httpx
from config import get_settings

settings = get_settings()

QUARTER_MONTHS = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
QUARTER_NAMES = {1: "第一季度", 2: "第二季度", 3: "第三季度", 4: "第四季度"}

# --- 原有的写死prompt已忽略，移到下面通过动态获取替代，这里保留给兜底用 ---
QUARTERLY_PROMPT = """你是一名政府机关文秘，精通公文写作。请根据以下{quarter_name}内各个月度的工作总结，按照公文写作规范，提取提炼成正式的季度工作总结报告。

【格式要求】
- 标题：{dept_name}{year}年{quarter_name}工作总结
- 一、主要工作完成情况（综合本季度成果，重点突出，分项列述）
- 二、存在的主要问题（客观分析，1-3条）
- 三、下季度工作计划（具体可行，承上启下）
- 文风：严谨、简洁，符合党政机关公文规范
- 字数：1000字至1500字之间
- 不要出现"根据您提供的"等表述，直接以第一人称写总结

【当季月度工作资料来源】
{content}

请直接输出标题和正文，无需其他说明。"""

ANNUAL_PROMPT = """你是一名政府机关文秘，精通公文写作。请综合以下全年各月度和季度工作总结，按照公文写作规范，生成一份正式的年度工作总结报告。

【格式要求】
- 标题：{dept_name}{year}年度工作总结
- 一、年度工作绩效与完成情况（！重点！：必须着重提炼全年的【工作绩效】，突出数据与成果产出）
- 二、存在的主要问题和不足
- 三、下一年度工作思路与计划
- 文风：高度凝练、严谨正式，符合党政机关年度公文规范
- 字数：1500字至2000字之间
- 不要出现"根据您提供的"等表述，直接以第一人称写总结

【年度工作资料来源】
{content}

请直接输出标题和正文，无需其他说明。"""

def get_custom_prompt(prompt_type: str) -> str:
    """尝试加载用户自定义的提示词模板文件"""
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "模板", f"{prompt_type}提示词.txt")
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if "{content}" in content:
                    return content
        except Exception:
            pass
    return None

def strip_images(text: str) -> str:
    """脱水处理器：强制过滤所有 Markdown 图片代码或 HTML img，只留存纯文字信息供给上级报告"""
    if not text:
        return ""
    # 将 ![alt](url) 的标记移除
    text = re.sub(r'!\[.*?\]\([^)]*\)', '', text)
    # 也过滤掉原始链接型可能混入的 <img src="...">
    text = re.sub(r'<img[^>]*>', '', text)
    return text

async def _call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=180.0, trust_env=False) as client:
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
    dept_name: str = None,
) -> str:
    dept = dept_name or settings.dept_name
    quarter_name = QUARTER_NAMES[quarter]
    months = QUARTER_MONTHS[quarter]

    sections = []
    
    # 完全依赖次级(月度)摘要
    for ms in monthly_summaries:
        if ms["month"] in months:
            safe_text = strip_images(ms['content'])
            if safe_text.strip():
                sections.append(f"## {ms['month']}月工作总结\n{safe_text}")

    if not sections:
        return f"{dept}{year}年{quarter_name}暂无对应的月度工作总结，未能生成提炼报告。"

    content = "\n\n".join(sections)
    
    custom_prompt = get_custom_prompt("季度")
    template_to_use = custom_prompt if custom_prompt else QUARTERLY_PROMPT
    
    prompt = template_to_use.format(
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
    dept_name: str = None,
) -> str:
    dept = dept_name or settings.dept_name

    sections = []

    if quarterly_summaries:
        for qs in sorted(quarterly_summaries, key=lambda x: x["quarter"]):
            safe_text = strip_images(qs['content'])
            if safe_text.strip():
                sections.append(f"## {QUARTER_NAMES[qs['quarter']]}总结\n{safe_text}")
    elif monthly_summaries:
        for ms in sorted(monthly_summaries, key=lambda x: x["month"]):
            safe_text = strip_images(ms['content'])
            if safe_text.strip():
                sections.append(f"## {ms['month']}月工作总结\n{safe_text}")

    if not sections:
        return f"{dept}{year}年暂无下层季度/月度资料，无法汇总绩效。"

    content = "\n\n".join(sections)
    
    custom_prompt = get_custom_prompt("年度")
    template_to_use = custom_prompt if custom_prompt else ANNUAL_PROMPT
    
    prompt = template_to_use.format(dept_name=dept, year=year, content=content)
    try:
        return await _call_ollama(prompt)
    except httpx.ConnectError:
        raise RuntimeError("无法连接Ollama服务，请确认服务已启动（端口11434）")
    except httpx.TimeoutException:
        raise RuntimeError("Ollama生成超时，请稍后重试")
    except Exception as e:
        raise RuntimeError(f"AI生成失败：{str(e)}")
