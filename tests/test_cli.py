from __future__ import annotations

from typer.testing import CliRunner

from script2storyboard.cli.main import app


runner = CliRunner()


def test_check_command_passes_fixture():
    result = runner.invoke(app, ["check", "tests/fixtures/good_storyboard.md"])

    assert result.exit_code == 0
    assert "校验通过" in result.output


def test_convert_refuses_to_overwrite(tmp_path, monkeypatch):
    script = tmp_path / "script.md"
    script.write_text("第一场\n女主说：\"你好。\"", encoding="utf-8")
    output = tmp_path / "文字分镜.md"
    output.write_text("exists", encoding="utf-8")
    monkeypatch.setenv("S2S_ARK_API_KEY", "key")
    monkeypatch.setenv("S2S_TEXT_MODEL", "model")

    result = runner.invoke(app, ["convert", str(script), "--output", str(output)])

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_help_command():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "剧本转分镜" in result.output


def test_convert_help_includes_director_options():
    result = runner.invoke(app, ["convert", "--help"])

    assert result.exit_code == 0
    assert "--audience-mode" in result.output
    assert "--max-shot-seconds" in result.output


def test_check_prints_warnings_without_failure(tmp_path):
    storyboard = tmp_path / "legacy.md"
    storyboard.write_text(
        """# 文字分镜 - 旧格式

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
- 0-3s: 女主@图片1推开房间@图片2的门。
- 3-6s: 女主@图片1走到桌边。
- 6-9s: 女主@图片1低头看手机。
- 9-12s: 女主@图片1抬头。
- 12-15s: 女主@图片1走出房间@图片2。
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", str(storyboard)])

    assert result.exit_code == 0
    assert "连贯性设定" in result.output
    assert "校验通过" in result.output
