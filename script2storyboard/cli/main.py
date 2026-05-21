"""Typer command line entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from script2storyboard import __version__
from script2storyboard.client.ark_text import ArkTextClient
from script2storyboard.config import load_config
from script2storyboard.errors import S2SError
from script2storyboard.storyboard.chunker import generate_storyboard
from script2storyboard.storyboard.prompt import StoryboardRequest
from script2storyboard.storyboard.validator import validate_storyboard


console = Console()
err_console = Console(stderr=True)
AUDIENCE_MODES = ["general", "female", "male"]

app = typer.Typer(
    add_completion=False,
    help="剧本转分镜 CLI：调用火山方舟文本模型生成15秒Clip文字分镜Markdown。",
)
auth_app = typer.Typer(help="配置与连通性检查。")
app.add_typer(auth_app, name="auth")


def version_callback(value: bool) -> None:
    if value:
        console.print(__version__)
        raise typer.Exit()


@app.callback()
def root(
    version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True, help="显示版本号。"),
) -> None:
    return None


@auth_app.command("check")
def auth_check(
    api_key: str | None = typer.Option(None, "--api-key", help="临时指定火山方舟API Key。"),
    model: str | None = typer.Option(None, "--model", help="临时指定文本模型或端点ID。"),
    base_url: str | None = typer.Option(None, "--base-url", help="临时指定火山方舟基础地址。"),
    env_file: Path | None = typer.Option(None, "--env-file", help="指定.env文件路径。"),
) -> None:
    """Validate configuration and run a short Chat Completions request."""

    try:
        config = load_config(api_key=api_key, model=model, base_url=base_url, env_file=env_file)
        client = ArkTextClient(config)
        client.complete(
            [
                {"role": "system", "content": "你只回答OK。"},
                {"role": "user", "content": "连通性检查"},
            ],
            temperature=0,
            max_tokens=16,
        )
    except S2SError as exc:
        _fail(exc)
    console.print("[green]配置和方舟文本接口检查通过。[/green]")


@app.command("convert")
def convert(
    script: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help="输入剧本文件。"),
    output: Path = typer.Option(Path("单集制作/EP001/文字分镜.md"), "--output", "-o", help="输出Markdown路径。"),
    project_name: str | None = typer.Option(None, "--project-name", help="项目名；默认取输入文件名。"),
    style: str = typer.Option("都市写实", "--style", help="画面风格。"),
    aspect: str = typer.Option("9:16", "--aspect", help="画幅。"),
    clip_duration: int = typer.Option(15, "--clip-duration", min=1, help="每个Clip秒数。"),
    audience_mode: str = typer.Option(
        "general",
        "--audience-mode",
        help="频道思维：general通用、female女频、male男频。",
    ),
    max_shot_seconds: float = typer.Option(4.0, "--max-shot-seconds", min=0.5, help="普通戏建议单镜最大秒数。"),
    temperature: float = typer.Option(0.4, "--temperature", min=0, max=2, help="模型temperature。"),
    max_tokens: int = typer.Option(12000, "--max-tokens", min=256, help="单次生成最大token。"),
    repair_attempts: int = typer.Option(1, "--repair-attempts", min=0, help="校验失败后的模型修复次数。"),
    force: bool = typer.Option(False, "--force", help="覆盖已有输出文件。"),
    api_key: str | None = typer.Option(None, "--api-key", help="临时指定火山方舟API Key。"),
    model: str | None = typer.Option(None, "--model", help="临时指定文本模型或端点ID。"),
    base_url: str | None = typer.Option(None, "--base-url", help="临时指定火山方舟基础地址。"),
    env_file: Path | None = typer.Option(None, "--env-file", help="指定.env文件路径。"),
) -> None:
    """将剧本文件转换为文字分镜Markdown。"""

    try:
        if output.exists() and not force:
            raise S2SError(f"Output already exists: {output}. Pass --force to overwrite.")

        config = load_config(api_key=api_key, model=model, base_url=base_url, env_file=env_file)
        script_text = script.read_text(encoding="utf-8").strip()
        if not script_text:
            raise S2SError(f"Input script is empty: {script}")
        if audience_mode not in AUDIENCE_MODES:
            raise S2SError(f"Invalid --audience-mode: {audience_mode}. Choose one of: {', '.join(AUDIENCE_MODES)}.")

        client = ArkTextClient(config)
        request = StoryboardRequest(
            project_name=project_name or script.stem,
            script=script_text,
            style=style,
            aspect=aspect,
            clip_duration=clip_duration,
            audience_mode=audience_mode,
            max_shot_seconds=max_shot_seconds,
            source_name=str(script),
        )
        storyboard, result = generate_storyboard(
            client,
            request,
            temperature=temperature,
            max_tokens=max_tokens,
            repair_attempts=repair_attempts,
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(storyboard.rstrip() + "\n", encoding="utf-8")
    except S2SError as exc:
        _fail(exc)

    if not result.ok:
        console.print(f"[yellow]已生成文字分镜，但仍有校验提醒：{output}[/yellow]")
        for issue in result.issues:
            console.print(f"[red]- {issue}[/red]")
    elif result.warnings:
        console.print(f"[yellow]已生成文字分镜，并有导演规则提醒：{output}[/yellow]")
    else:
        console.print(f"[green]已生成文字分镜：{output}[/green]")
    for warning in result.warnings:
        console.print(f"[yellow]- {warning}[/yellow]")


@app.command("check")
def check(
    storyboard: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help="文字分镜Markdown。"),
    script: Path | None = typer.Option(None, "--script", exists=True, file_okay=True, dir_okay=False, help="原剧本，用于检查台词保留。"),
    clip_duration: int = typer.Option(15, "--clip-duration", min=1, help="每个Clip秒数。"),
    max_shot_seconds: float = typer.Option(4.0, "--max-shot-seconds", min=0.5, help="普通戏建议单镜最大秒数。"),
) -> None:
    """离线校验文字分镜Markdown文件。"""

    content = storyboard.read_text(encoding="utf-8")
    original = script.read_text(encoding="utf-8") if script else None
    result = validate_storyboard(
        content,
        original_script=original,
        clip_duration=clip_duration,
        max_shot_seconds=max_shot_seconds,
    )
    for warning in result.warnings:
        console.print(f"[yellow]- {warning}[/yellow]")
    if result.ok:
        console.print("[green]文字分镜校验通过。[/green]")
        return
    for issue in result.issues:
        err_console.print(f"[red]- {issue}[/red]")
    raise typer.Exit(4)


def _fail(exc: S2SError) -> None:
    err_console.print(f"[red]{exc.message}[/red]")
    raise typer.Exit(exc.exit_code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
