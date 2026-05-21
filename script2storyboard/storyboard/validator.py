"""Offline storyboard validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


CLIP_RE = re.compile(r"^##\s+Clip\s+(\d+)\s*$", re.MULTILINE | re.IGNORECASE)
REFERENCE_RE = re.compile(r"^##\s+参考图分配\s*$", re.MULTILINE)
CONTINUITY_RE = re.compile(r"^##\s+连贯性设定\s*$", re.MULTILINE)
CHAR_BINDING_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_（）()·-]+@图片\d+")
SPEECH_RE = re.compile(
    r"(?:[“\"]([^”\"]{1,200})[”\"]|「([^」]{1,200})」|『([^』]{1,200})』)"
)
SHOT_LINE_RE = re.compile(r"^-\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)s[:：](.*)$")
VIEW_KEYWORDS = ("远景", "全景", "大全景", "中景", "中近景", "近景", "特写", "大特写", "空镜")
AXIS_KEYWORDS = ("轴线", "越轴", "同轴", "180", "左侧", "右侧", "画面左", "画面右")
REVERSE_SHOT_KEYWORDS = ("正反打", "反打", "视线", "肩背", "方向")
TRANSITION_KEYWORDS = ("转场", "锚点", "衔接", "承接", "空镜", "道具", "门", "手机", "脸", "血滴", "空间")
CUTTING_KEYWORDS = ("切镜", "切换", "不乱切", "台词", "动作", "视线", "空间信息", "道具状态")
AUDIENCE_KEYWORDS = ("频道思维", "女频", "男频", "通用", "爽点", "情绪流", "关系张力")


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_storyboard(
    storyboard: str,
    *,
    original_script: str | None = None,
    clip_duration: int = 15,
    max_shot_seconds: float = 4.0,
) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []

    if not REFERENCE_RE.search(storyboard):
        issues.append("缺少“## 参考图分配”章节。")
    if not CONTINUITY_RE.search(storyboard):
        warnings.append("缺少“## 连贯性设定”：建议明确人物站位、场景轴线、正反打方向和转场锚点。")
    else:
        _validate_continuity_section(storyboard, warnings=warnings)

    clip_matches = list(CLIP_RE.finditer(storyboard))
    if not clip_matches:
        issues.append("缺少“## Clip N”章节。")
    else:
        clip_numbers = [int(match.group(1)) for match in clip_matches]
        expected = list(range(1, len(clip_numbers) + 1))
        if clip_numbers != expected:
            issues.append(f"Clip编号不连续，应为 {expected}，实际为 {clip_numbers}。")

        for idx, match in enumerate(clip_matches):
            start = match.start()
            end = clip_matches[idx + 1].start() if idx + 1 < len(clip_matches) else len(storyboard)
            block = storyboard[start:end]
            clip_no = clip_numbers[idx]
            _validate_clip_block(
                block,
                clip_no=clip_no,
                clip_duration=clip_duration,
                max_shot_seconds=max_shot_seconds,
                issues=issues,
                warnings=warnings,
            )

    if original_script:
        for line in _extract_dialogue(original_script):
            if line not in storyboard:
                issues.append(f"台词原文未保留：{line}")

    return ValidationResult(ok=not issues, issues=issues, warnings=warnings)


def _validate_clip_block(
    block: str,
    *,
    clip_no: int,
    clip_duration: int,
    max_shot_seconds: float,
    issues: list[str],
    warnings: list[str],
) -> None:
    required = ["### 基础信息", "### 分镜列表", "- 人物：", "- 场景：", "- 时长："]
    for marker in required:
        if marker not in block:
            issues.append(f"Clip {clip_no} 缺少 {marker}。")
    if "### 导演调度" not in block:
        warnings.append(f"Clip {clip_no} 缺少“### 导演调度”：建议补充轴线、正反打、切镜、转场、景别和频道思维。")
    else:
        _validate_director_block(block, clip_no=clip_no, warnings=warnings)

    duration_patterns = [
        f"时长：{clip_duration}秒",
        f"时长: {clip_duration}秒",
        f"时长：{clip_duration} 秒",
        f"时长: {clip_duration} 秒",
    ]
    if not any(pattern in block for pattern in duration_patterns):
        issues.append(f"Clip {clip_no} 未标明 {clip_duration} 秒时长。")

    shot_lines = [
        line.strip()
        for line in block.splitlines()
        if SHOT_LINE_RE.match(line.strip())
    ]
    if not shot_lines:
        issues.append(f"Clip {clip_no} 缺少带时间段的分镜条目。")
    else:
        _validate_shot_lines(
            shot_lines,
            clip_no=clip_no,
            max_shot_seconds=max_shot_seconds,
            warnings=warnings,
        )

    lines_needing_binding = []
    for line in shot_lines:
        if "@" not in line and any(ch in line for ch in ("他", "她", "男", "女", "主", "角色")):
            lines_needing_binding.append(line[:80])
    if lines_needing_binding:
        issues.append(f"Clip {clip_no} 存在未绑定@图片N的角色/指代：{lines_needing_binding[0]}")

    if "@" in block and not CHAR_BINDING_RE.search(block):
        issues.append(f"Clip {clip_no} 的@图片绑定格式不正确。")


def _validate_continuity_section(storyboard: str, *, warnings: list[str]) -> None:
    start = CONTINUITY_RE.search(storyboard)
    if not start:
        return
    next_clip = CLIP_RE.search(storyboard, start.end())
    section = storyboard[start.end() : next_clip.start() if next_clip else len(storyboard)]
    checks = [
        ("人物站位", ("站位", "画面左", "画面右", "左侧", "右侧")),
        ("场景轴线", AXIS_KEYWORDS),
        ("正反打方向", REVERSE_SHOT_KEYWORDS),
        ("主要转场锚点", TRANSITION_KEYWORDS),
        ("景别节奏", VIEW_KEYWORDS),
    ]
    for label, keywords in checks:
        if not _contains_any(section, keywords):
            warnings.append(f"连贯性设定缺少{label}提示。")


def _validate_director_block(block: str, *, clip_no: int, warnings: list[str]) -> None:
    start = block.find("### 导演调度")
    end = block.find("### 分镜列表", start)
    section = block[start : end if end != -1 else len(block)]
    checks = [
        ("轴线与站位", AXIS_KEYWORDS + ("站位",)),
        ("正反打规则", REVERSE_SHOT_KEYWORDS),
        ("切镜策略", CUTTING_KEYWORDS),
        ("转场锚点", TRANSITION_KEYWORDS),
        ("景别节奏", VIEW_KEYWORDS),
        ("频道思维", AUDIENCE_KEYWORDS),
    ]
    for label, keywords in checks:
        if label not in section and not _contains_any(section, keywords):
            warnings.append(f"Clip {clip_no} 导演调度缺少{label}。")


def _validate_shot_lines(
    shot_lines: list[str],
    *,
    clip_no: int,
    max_shot_seconds: float,
    warnings: list[str],
) -> None:
    view_count = 0
    has_axis_or_continuity = False
    has_transition_or_empty = False

    for line in shot_lines:
        match = SHOT_LINE_RE.match(line)
        if not match:
            continue
        start_s = float(match.group(1))
        end_s = float(match.group(2))
        duration = end_s - start_s
        if duration > max_shot_seconds:
            warnings.append(
                f"Clip {clip_no} 存在单镜过长：{start_s:g}-{end_s:g}s 共{duration:g}秒，建议普通戏不超过{max_shot_seconds:g}秒。"
            )
        if _contains_any(line, VIEW_KEYWORDS):
            view_count += 1
        if _contains_any(line, AXIS_KEYWORDS + ("承接", "衔接")):
            has_axis_or_continuity = True
        if _contains_any(line, TRANSITION_KEYWORDS):
            has_transition_or_empty = True

    if len(shot_lines) >= 2 and view_count < 2:
        warnings.append(f"Clip {clip_no} 景别变化不足：建议至少出现两类景别或空镜。")
    if not has_axis_or_continuity:
        warnings.append(f"Clip {clip_no} 分镜条目缺少轴线侧或承接关系提示。")
    if not has_transition_or_empty:
        warnings.append(f"Clip {clip_no} 分镜条目缺少转场锚点、空镜或衔接提示。")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _extract_dialogue(script: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in SPEECH_RE.finditer(script):
        text = next(group for group in match.groups() if group)
        cleaned = text.strip()
        if cleaned and cleaned not in seen:
            found.append(cleaned)
            seen.add(cleaned)
    return found
