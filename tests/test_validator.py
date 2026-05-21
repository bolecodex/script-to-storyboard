from __future__ import annotations

from pathlib import Path

from script2storyboard.storyboard.validator import validate_storyboard


FIXTURES = Path(__file__).parent / "fixtures"


def test_good_storyboard_passes_with_script_dialogue():
    storyboard = (FIXTURES / "good_storyboard.md").read_text(encoding="utf-8")
    script = (FIXTURES / "demo_script.md").read_text(encoding="utf-8")

    result = validate_storyboard(storyboard, original_script=script)

    assert result.ok
    assert result.warnings == []


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


def test_legacy_storyboard_passes_with_director_warnings():
    legacy = """# 文字分镜 - 旧格式

## 参考图分配
- 图片1：女主参考
- 图片2：房间参考

## Clip 1

### 基础信息
- 人物：女主@图片1
- 场景：房间@图片2
- 时长：15秒
- 内容概述：女主进入房间。

### 分镜列表
- 0-3s: 女主@图片1推开房间@图片2的门，冷光从门缝落在她脸上。
- 3-6s: 女主@图片1走到桌边，低声说："我回来了。"
- 6-9s: 女主@图片1抬头看向窗外。
- 9-12s: 女主@图片1伸手拿起桌上的钥匙。
- 12-15s: 女主@图片1转身走出房间@图片2。
"""
    result = validate_storyboard(legacy, original_script='女主说："我回来了。"')

    assert result.ok
    assert any("连贯性设定" in warning for warning in result.warnings)
    assert any("导演调度" in warning for warning in result.warnings)


def test_director_warnings_detect_missing_cinematic_rules():
    storyboard = """# 文字分镜 - 缺导演细节

## 参考图分配
- 图片1：女主参考
- 图片2：男主参考
- 图片3：客厅参考

## 连贯性设定
- 人物站位：女主@图片1和男主@图片2在客厅@图片3里对峙。

## Clip 1

### 基础信息
- 人物：女主@图片1、男主@图片2
- 场景：客厅@图片3
- 时长：15秒
- 内容概述：两人对峙。

### 导演调度
- 切镜策略：两人说话时切镜。

### 分镜列表
- 0-5s: 女主@图片1看着男主@图片2，说："你终于来了。"
- 5-10s: 男主@图片2看着女主@图片1，说："我不会再逃。"
- 10-15s: 女主@图片1沉默地转身。
"""
    result = validate_storyboard(storyboard, original_script='女主说："你终于来了。"\n男主说："我不会再逃。"')

    assert result.ok
    assert any("正反打" in warning for warning in result.warnings)
    assert any("转场" in warning or "空镜" in warning for warning in result.warnings)
    assert any("景别" in warning for warning in result.warnings)


def test_long_shot_generates_warning():
    storyboard = """# 文字分镜 - 长镜头

## 参考图分配
- 图片1：女主参考
- 图片2：房间参考

## 连贯性设定
- 人物站位：女主@图片1位于房间@图片2画面左侧，保持画面左/右关系。
- 场景轴线：以女主@图片1和房门连线为轴线，镜头保持轴线左侧180度内。
- 正反打方向：女主@图片1与房门正反打保持视线方向。
- 主要转场锚点：门和手机作为转场锚点，使用空镜衔接。
- 景别节奏：中景、近景、特写渐进。

## Clip 1

### 基础信息
- 人物：女主@图片1
- 场景：房间@图片2
- 时长：15秒
- 内容概述：女主长时间独白。

### 导演调度
- 轴线与站位：女主@图片1站在画面左侧，镜头保持轴线左侧。
- 正反打规则：女主@图片1与房门反打保持方向。
- 切镜策略：台词和动作变化时切换，不乱切。
- 转场锚点：手机和门作为衔接锚点，插入空镜。
- 景别节奏：中景、近景、特写切换。
- 频道思维：通用模式。

### 分镜列表
- 0-8s: [中景/轴线左侧/承接上镜] 女主@图片1站在房间@图片2里，看向手机说："我知道了。"
- 8-11s: [近景/同轴反打/手机转场锚点] 女主@图片1低头看向手机。
- 11-15s: [特写/轴线左侧/空镜衔接] 手机屏幕冷光映在女主@图片1脸上。
"""
    result = validate_storyboard(storyboard, original_script='女主说："我知道了。"', max_shot_seconds=4)

    assert result.ok
    assert any("单镜过长" in warning for warning in result.warnings)
