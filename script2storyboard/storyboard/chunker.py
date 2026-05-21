"""Long-script chunking and generation orchestration."""

from __future__ import annotations

import re
from typing import Protocol

from script2storyboard.storyboard.prompt import (
    StoryboardRequest,
    build_merge_messages,
    build_repair_messages,
    build_storyboard_messages,
)
from script2storyboard.storyboard.validator import ValidationResult, validate_storyboard


DEFAULT_MAX_CHARS = 24000


class TextGenerator(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 12000,
    ) -> str:
        ...


def split_script(script: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    normalized = script.strip()
    if len(normalized) <= max_chars:
        return [normalized]

    units = _split_units(normalized)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for unit in units:
        unit_len = len(unit)
        if current and current_len + unit_len + 2 > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_len = 0
        if unit_len > max_chars:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_len = 0
            chunks.extend(_hard_wrap(unit, max_chars=max_chars))
            continue
        current.append(unit)
        current_len += unit_len + 2

    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk.strip()]


def generate_storyboard(
    generator: TextGenerator,
    request: StoryboardRequest,
    *,
    temperature: float = 0.4,
    max_tokens: int = 12000,
    repair_attempts: int = 1,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> tuple[str, ValidationResult]:
    chunks = split_script(request.script, max_chars=max_chars)
    if len(chunks) == 1:
        storyboard = _generate_one(
            generator,
            request,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        partials: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            partial_request = StoryboardRequest(
                project_name=request.project_name,
                script=chunk,
                style=request.style,
                aspect=request.aspect,
                clip_duration=request.clip_duration,
                audience_mode=request.audience_mode,
                max_shot_seconds=request.max_shot_seconds,
                source_name=request.source_name,
                part_index=idx,
                total_parts=len(chunks),
            )
            partials.append(
                _generate_one(
                    generator,
                    partial_request,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
        storyboard = generator.complete(
            build_merge_messages(
                project_name=request.project_name,
                partial_storyboards=partials,
                style=request.style,
                aspect=request.aspect,
                clip_duration=request.clip_duration,
                audience_mode=request.audience_mode,
                max_shot_seconds=request.max_shot_seconds,
            ),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    result = validate_storyboard(
        storyboard,
        original_script=request.script,
        clip_duration=request.clip_duration,
        max_shot_seconds=request.max_shot_seconds,
    )
    attempts = 0
    while not result.ok and attempts < repair_attempts:
        attempts += 1
        storyboard = generator.complete(
            build_repair_messages(
                storyboard=storyboard,
                issues=result.issues,
                original_script=request.script,
                request=request,
            ),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        result = validate_storyboard(
            storyboard,
            original_script=request.script,
            clip_duration=request.clip_duration,
            max_shot_seconds=request.max_shot_seconds,
        )
    return storyboard, result


def _generate_one(
    generator: TextGenerator,
    request: StoryboardRequest,
    *,
    temperature: float,
    max_tokens: int,
) -> str:
    return generator.complete(
        build_storyboard_messages(request),
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _split_units(script: str) -> list[str]:
    scene_pattern = re.compile(r"(?=^(?:第[一二三四五六七八九十百\d]+[场幕集]|场景\s*\d+|INT\.|EXT\.).*$)", re.MULTILINE)
    parts = [part.strip() for part in scene_pattern.split(script) if part.strip()]
    if len(parts) > 1:
        return parts
    return [part.strip() for part in re.split(r"\n\s*\n", script) if part.strip()]


def _hard_wrap(text: str, *, max_chars: int) -> list[str]:
    return [text[idx : idx + max_chars].strip() for idx in range(0, len(text), max_chars)]
