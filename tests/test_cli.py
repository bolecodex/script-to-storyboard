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
