from __future__ import annotations

from script2storyboard.storyboard.chunker import generate_storyboard, split_script
from script2storyboard.storyboard.prompt import StoryboardRequest


class FakeGenerator:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages, *, temperature=0.4, max_tokens=12000):
        self.calls.append(messages)
        text = messages[-1]["content"]
        if "合并" in text:
            return GOOD_STORYBOARD.replace("测试分镜", "长剧本")
        return GOOD_STORYBOARD


GOOD_STORYBOARD = """# 文字分镜 - 测试分镜

## 参考图分配
- 图片1：女主参考
- 图片2：病房场景参考

## Clip 1

### 基础信息
- 人物：女主@图片1
- 场景：病房@图片2
- 时长：15秒
- 内容概述：女主进入病房并道歉。

### 分镜列表
- 0-7s: 女主@图片1推门进入病房@图片2，镜头缓慢推近，冷白灯光落在她脸侧，她说："对不起。"
- 7-15s: 女主@图片1站在床边，手指扣紧床单，镜头从手部上摇到脸部。
"""


def test_split_script_chunks_long_text():
    chunks = split_script("第一场\n" + "a" * 30 + "\n\n第二场\n" + "b" * 30, max_chars=40)

    assert len(chunks) >= 2


def test_generate_storyboard_merges_long_script():
    generator = FakeGenerator()
    request = StoryboardRequest(
        project_name="长剧本",
        script='第一场\n女主说："对不起。"\n\n第二场\n' + "动作。" * 100,
    )

    storyboard, result = generate_storyboard(
        generator,
        request,
        max_chars=60,
        repair_attempts=0,
    )

    assert "## Clip 1" in storyboard
    assert result.ok
    assert len(generator.calls) >= 3
