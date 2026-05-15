"""Prompt templates for script-to-storyboard generation."""

from __future__ import annotations

from dataclasses import dataclass


SYSTEM_PROMPT = """你是资深短剧文字分镜导演，擅长把中文剧本转为可拍摄的15秒Clip文字分镜。

硬性规则：
1. 只输出Markdown正文，不要解释过程。
2. 每个Clip默认15秒，除非用户指定其他时长。
3. 必须保留剧本中的每一句角色台词原文，不得概括、删改或用动作替代。
4. 每次提及角色必须使用“角色名@图片N”，每次提及有参考图的道具必须使用“道具名@图片N”。
5. 用具体物理动作、表情细节、空间关系、镜头运动和光影替代抽象情绪词。
6. 每个分镜项必须能在对应时间段内完成，时间段总和覆盖当前Clip。
7. 不生成视频提示词，不写模型参数，不写视频生成命令。
"""


@dataclass(frozen=True)
class StoryboardRequest:
    project_name: str
    script: str
    style: str = "都市写实"
    aspect: str = "9:16"
    clip_duration: int = 15
    source_name: str | None = None
    part_index: int | None = None
    total_parts: int | None = None


def build_storyboard_messages(request: StoryboardRequest) -> list[dict[str, str]]:
    label = ""
    if request.part_index and request.total_parts:
        label = f"\n这是长剧本的第 {request.part_index}/{request.total_parts} 段，请只处理本段内容。"

    user_prompt = f"""请将下面剧本转换为文字分镜Markdown。

项目名：{request.project_name}
来源文件：{request.source_name or "未提供"}
画面风格：{request.style}
画幅：{request.aspect}
每个Clip时长：{request.clip_duration}秒{label}

输出格式必须严格接近：

# 文字分镜 - {request.project_name}

## 参考图分配
- 图片1：角色A面部或全身参考
- 图片2：场景或角色B参考

## Clip 1

### 基础信息
- 人物：角色A@图片1
- 场景：场景名@图片2
- 时长：{request.clip_duration}秒
- 内容概述：一句话概括

### 分镜列表
- 0-3s: 画面描述，必须包含角色名@图片N、具体动作、镜头、光影；如有台词，写成角色名@图片N说："台词原文"
- 3-7s: ...
- 7-{request.clip_duration}s: ...

要求：
- 开头必须有“参考图分配”。
- Clip编号从1开始，使用“## Clip N”标题。
- 所有台词原文都要出现在分镜描述中。
- 不要输出JSON。
- 不要使用代码块包裹结果。

剧本：
{request.script}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def build_repair_messages(
    *,
    storyboard: str,
    issues: list[str],
    original_script: str,
    request: StoryboardRequest,
) -> list[dict[str, str]]:
    issue_text = "\n".join(f"- {issue}" for issue in issues)
    user_prompt = f"""下面的文字分镜未通过校验，请在保留内容的基础上修复，并只输出完整Markdown。

项目名：{request.project_name}
画面风格：{request.style}
画幅：{request.aspect}
每个Clip时长：{request.clip_duration}秒

校验问题：
{issue_text}

原剧本：
{original_script}

待修复文字分镜：
{storyboard}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def build_merge_messages(
    *,
    project_name: str,
    partial_storyboards: list[str],
    style: str,
    aspect: str,
    clip_duration: int,
) -> list[dict[str, str]]:
    joined = "\n\n---\n\n".join(partial_storyboards)
    user_prompt = f"""请把下面多个分段文字分镜合并为一份完整Markdown。

项目名：{project_name}
画面风格：{style}
画幅：{aspect}
每个Clip时长：{clip_duration}秒

合并要求：
- 只保留一个一级标题和一个“参考图分配”。
- 重新整理参考图编号，保持角色/道具/场景引用一致。
- 将所有Clip重新编号为“## Clip 1”“## Clip 2”连续递增。
- 保留全部台词原文和全部关键动作。
- 只输出Markdown正文，不要解释。

分段文字分镜：
{joined}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
