---
name: script-to-storyboard
description: 将剧本、短剧台本、小说片段转换为文字分镜。用于用户要求“剧本转分镜”“生成分镜”“拆成15秒clip”“输出文字分镜.md”等场景。
---

# 剧本转分镜

## Workflow

优先使用 `script2storyboard` CLI 生成 `文字分镜.md`：

```bash
script2storyboard convert <剧本文件> --output 单集制作/EP001/文字分镜.md
```

如果用户要求人工撰写、CLI 未安装，或当前环境无法调用模型，则按下方规则直接输出 Markdown。

## Output Rules

- 输出文件默认命名为 `文字分镜.md`。
- 每个 Clip 默认 15 秒，标题使用 `## Clip N`。
- 文件开头必须包含 `## 参考图分配`，明确图片、音频、视频编号的用途。
- 每个 Clip 包含 `### 基础信息` 和 `### 分镜列表`。
- 基础信息至少包含人物、场景、时长、内容概述。
- 分镜条目使用 `0-3s:` 这类时间段，时间段合计覆盖当前 Clip。

## Writing Rules

- 保留剧本中的每一句台词原文，不用动作概括替代台词。
- 每次提及角色都写成 `角色名@图片N`，不要只写角色名。
- 有参考图的道具写成 `道具名@图片N`。
- 用具体物理动作、表情、空间关系、镜头运动、光线方向和色温表达情绪。
- 不写视频提示词，不写视频生成命令，不输出 JSON。

## CLI Notes

- 配置项：`S2S_ARK_API_KEY`、`S2S_TEXT_MODEL`、可选 `S2S_ARK_BASE_URL`。
- 运行 `script2storyboard auth check` 检查配置。
- 运行 `script2storyboard check <文字分镜.md>` 离线检查结构和关键规则。
