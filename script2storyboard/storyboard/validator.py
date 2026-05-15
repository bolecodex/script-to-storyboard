"""Offline storyboard validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


CLIP_RE = re.compile(r"^##\s+Clip\s+(\d+)\s*$", re.MULTILINE | re.IGNORECASE)
REFERENCE_RE = re.compile(r"^##\s+参考图分配\s*$", re.MULTILINE)
CHAR_BINDING_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_（）()·-]+@图片\d+")
SPEECH_RE = re.compile(
    r"(?:[“\"]([^”\"]{1,200})[”\"]|「([^」]{1,200})」|『([^』]{1,200})』)"
)


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str] = field(default_factory=list)


def validate_storyboard(
    storyboard: str,
    *,
    original_script: str | None = None,
    clip_duration: int = 15,
) -> ValidationResult:
    issues: list[str] = []

    if not REFERENCE_RE.search(storyboard):
        issues.append("缺少“## 参考图分配”章节。")

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
            _validate_clip_block(block, clip_no=clip_no, clip_duration=clip_duration, issues=issues)

    if original_script:
        for line in _extract_dialogue(original_script):
            if line not in storyboard:
                issues.append(f"台词原文未保留：{line}")

    return ValidationResult(ok=not issues, issues=issues)


def _validate_clip_block(block: str, *, clip_no: int, clip_duration: int, issues: list[str]) -> None:
    required = ["### 基础信息", "### 分镜列表", "- 人物：", "- 场景：", "- 时长："]
    for marker in required:
        if marker not in block:
            issues.append(f"Clip {clip_no} 缺少 {marker}。")

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
        if re.match(r"^-\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?s[:：]", line.strip())
    ]
    if not shot_lines:
        issues.append(f"Clip {clip_no} 缺少带时间段的分镜条目。")

    lines_needing_binding = []
    for line in shot_lines:
        if "@" not in line and any(ch in line for ch in ("他", "她", "男", "女", "主", "角色")):
            lines_needing_binding.append(line[:80])
    if lines_needing_binding:
        issues.append(f"Clip {clip_no} 存在未绑定@图片N的角色/指代：{lines_needing_binding[0]}")

    if "@" in block and not CHAR_BINDING_RE.search(block):
        issues.append(f"Clip {clip_no} 的@图片绑定格式不正确。")


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
