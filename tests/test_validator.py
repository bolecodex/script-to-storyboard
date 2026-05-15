from __future__ import annotations

from pathlib import Path

from script2storyboard.storyboard.validator import validate_storyboard


FIXTURES = Path(__file__).parent / "fixtures"


def test_good_storyboard_passes_with_script_dialogue():
    storyboard = (FIXTURES / "good_storyboard.md").read_text(encoding="utf-8")
    script = (FIXTURES / "demo_script.md").read_text(encoding="utf-8")

    result = validate_storyboard(storyboard, original_script=script)

    assert result.ok


def test_validator_detects_missing_structure_and_dialogue():
    bad = """# 文字分镜

## Clip 1

### 分镜列表
- 0-15s: 她走进房间，说了一句道歉。
"""
    script = '苏棠说："对不起……陆衍，对不起。"'

    result = validate_storyboard(bad, original_script=script)

    assert not result.ok
    assert any("参考图分配" in issue for issue in result.issues)
    assert any("基础信息" in issue for issue in result.issues)
    assert any("@图片N" in issue for issue in result.issues)
    assert any("台词原文未保留" in issue for issue in result.issues)
