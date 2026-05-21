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

导演调度规则：
1. 写分镜前先识别人物、场景、道具、人物站位、动作连续性和场景轴线。
2. 同一空间内以两个人或人物/物体连线为轴线，镜头必须保持在同一180度侧，不得无说明越轴；若确需换侧，必须用空镜、正面中性镜头或空间转场重建轴线。
3. 正反打不仅处理人物，也要处理场景正反打；人物左/右关系、视线方向和背景方位要连续。
4. 不乱切：只有台词、动作、视线、空间信息、道具状态或情绪节奏发生变化时才切镜。
5. 单镜不要过长；用景别、角度、人物反应、道具空镜和空间镜头消解视觉疲劳。
6. 转场要有锚点，可用手机、脸、门、血滴、道具、空间入口、灯光变化等做衔接；必要时插入有遐想空间的空镜。
7. 景别要连贯，都市情感戏避免从特写突然跳到大全景；打斗、危机、强爽点可以有更大景别跳变，但要说明动因。
8. 女频更重情绪流、关系张力、凝视和细微反应；男频更重目标推进、爽点、压迫感、力量变化和空间调度。
"""


AUDIENCE_MODE_GUIDES = {
    "general": "通用：平衡叙事清晰、人物关系、空间连续和镜头节奏。",
    "female": "女频：强化感觉、关系张力、凝视/反应、细微身体动作、情绪流和氛围转场。",
    "male": "男频：强化目标推进、爽点、压迫感、力量变化、空间调度、冲击空镜和结果反馈。",
}


@dataclass(frozen=True)
class StoryboardRequest:
    project_name: str
    script: str
    style: str = "都市写实"
    aspect: str = "9:16"
    clip_duration: int = 15
    audience_mode: str = "general"
    max_shot_seconds: float = 4.0
    source_name: str | None = None
    part_index: int | None = None
    total_parts: int | None = None


def build_storyboard_messages(request: StoryboardRequest) -> list[dict[str, str]]:
    label = ""
    if request.part_index and request.total_parts:
        label = f"\n这是长剧本的第 {request.part_index}/{request.total_parts} 段，请只处理本段内容。"
    audience_guide = AUDIENCE_MODE_GUIDES.get(request.audience_mode, AUDIENCE_MODE_GUIDES["general"])

    user_prompt = f"""请将下面剧本转换为文字分镜Markdown。

项目名：{request.project_name}
来源文件：{request.source_name or "未提供"}
画面风格：{request.style}
画幅：{request.aspect}
每个Clip时长：{request.clip_duration}秒
频道思维：{audience_guide}
最大单镜时长：普通对话/情绪戏每镜建议不超过{request.max_shot_seconds:g}秒，打斗、危机、强爽点可突破但必须说明动因。{label}

输出格式必须严格接近：

# 文字分镜 - {request.project_name}

## 参考图分配
- 图片1：角色A面部或全身参考
- 图片2：场景或角色B参考

## 连贯性设定
- 人物站位：角色A@图片1在画面左侧，角色B@图片2在画面右侧，后续保持左右关系。
- 场景轴线：以角色A@图片1与角色B@图片2的连线为轴线，镜头保持在轴线左侧180度内。
- 正反打方向：拍角色A@图片1时保留角色B@图片2的肩背/视线方向，拍角色B@图片2时保持相反方向，不越轴。
- 主要转场锚点：门、手机、道具、人物脸部或空间入口；必要时用空镜衔接。
- 景别节奏：从中景建立空间，逐步切到中近景/近景/特写，避免无动因大跳切。
- 频道思维：{audience_guide}

## Clip 1

### 基础信息
- 人物：角色A@图片1
- 场景：场景名@图片2
- 时长：{request.clip_duration}秒
- 内容概述：一句话概括

### 导演调度
- 轴线与站位：明确人物/物体连线、镜头所在轴线侧、画面左/右关系。
- 正反打规则：说明人物正反打和场景正反打如何保持方向一致。
- 切镜策略：只在台词、动作、视线、空间信息或道具状态变化时切，不为切而切。
- 转场锚点：指定手机、脸、门、血滴、道具或空间作为衔接点；必要时加入空镜。
- 景别节奏：控制单镜长度，按中景/中近景/近景/特写/空镜渐进切换。
- 频道思维：按{request.audience_mode}模式说明本Clip镜头重点。

### 分镜列表
- 0-3s: [中近景/轴线左侧/承接上镜] 画面描述，必须包含角色名@图片N、具体动作、镜头、光影；如有台词，写成角色名@图片N说："台词原文"
- 3-6s: [近景/同轴反打/视线衔接] ...
- 6-{request.clip_duration}s: [特写或空镜/转场锚点/景别渐进] ...

要求：
- 开头必须有“参考图分配”。
- 必须有“连贯性设定”。
- Clip编号从1开始，使用“## Clip N”标题。
- 每个Clip必须有“导演调度”。
- 所有台词原文都要出现在分镜描述中。
- 每条分镜建议写明景别、轴线侧、承接关系。
- 对话戏避免连续单人正面长镜头；用反应、手部、道具、空镜或侧面角度衔接。
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
频道思维：{AUDIENCE_MODE_GUIDES.get(request.audience_mode, AUDIENCE_MODE_GUIDES["general"])}
最大单镜时长：普通对话/情绪戏每镜建议不超过{request.max_shot_seconds:g}秒

修复时必须保留或补齐“## 连贯性设定”和每个Clip的“### 导演调度”，导演调度必须包含轴线与站位、正反打规则、切镜策略、转场锚点、景别节奏、频道思维。

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
    audience_mode: str = "general",
    max_shot_seconds: float = 4.0,
) -> list[dict[str, str]]:
    joined = "\n\n---\n\n".join(partial_storyboards)
    audience_guide = AUDIENCE_MODE_GUIDES.get(audience_mode, AUDIENCE_MODE_GUIDES["general"])
    user_prompt = f"""请把下面多个分段文字分镜合并为一份完整Markdown。

项目名：{project_name}
画面风格：{style}
画幅：{aspect}
每个Clip时长：{clip_duration}秒
频道思维：{audience_guide}
最大单镜时长：普通对话/情绪戏每镜建议不超过{max_shot_seconds:g}秒

合并要求：
- 只保留一个一级标题和一个“参考图分配”。
- 只保留一个“连贯性设定”，并统一人物站位、场景轴线、正反打方向和转场锚点。
- 重新整理参考图编号，保持角色/道具/场景引用一致。
- 将所有Clip重新编号为“## Clip 1”“## Clip 2”连续递增。
- 每个Clip必须保留“### 导演调度”，包含轴线与站位、正反打规则、切镜策略、转场锚点、景别节奏、频道思维。
- 保留全部台词原文和全部关键动作。
- 只输出Markdown正文，不要解释。

分段文字分镜：
{joined}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
