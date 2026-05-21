from __future__ import annotations

from script2storyboard.storyboard.prompt import (
    StoryboardRequest,
    build_merge_messages,
    build_repair_messages,
    build_storyboard_messages,
)


def test_storyboard_prompt_includes_director_options():
    request = StoryboardRequest(
        project_name="测试项目",
        script="女主说：\"你来了。\"",
        audience_mode="female",
        max_shot_seconds=3,
    )

    messages = build_storyboard_messages(request)
    prompt = messages[-1]["content"]

    assert "女频" in prompt
    assert "最大单镜时长" in prompt
    assert "3秒" in prompt
    assert "## 连贯性设定" in prompt
    assert "### 导演调度" in prompt
    assert "轴线与站位" in prompt


def test_repair_prompt_requires_enhanced_structure():
    request = StoryboardRequest(
        project_name="测试项目",
        script="男主说：\"开始吧。\"",
        audience_mode="male",
        max_shot_seconds=3,
    )

    messages = build_repair_messages(
        storyboard="旧分镜",
        issues=["缺导演调度"],
        original_script=request.script,
        request=request,
    )
    prompt = messages[-1]["content"]

    assert "男频" in prompt
    assert "连贯性设定" in prompt
    assert "导演调度" in prompt
    assert "转场锚点" in prompt


def test_merge_prompt_keeps_director_structure():
    messages = build_merge_messages(
        project_name="测试项目",
        partial_storyboards=["# part1", "# part2"],
        style="都市写实",
        aspect="9:16",
        clip_duration=15,
        audience_mode="male",
        max_shot_seconds=3,
    )
    prompt = messages[-1]["content"]

    assert "男频" in prompt
    assert "连贯性设定" in prompt
    assert "导演调度" in prompt
    assert "3秒" in prompt
