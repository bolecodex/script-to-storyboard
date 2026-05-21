# 剧本转分镜

把剧本、短剧台本或小说片段转换为 15 秒 Clip 的文字分镜 Markdown。第一版只输出 `文字分镜.md`，不生成视频 prompt，也不生成视频。

## 安装

```bash
python3.11 -m pip install -e ".[dev]"
```

也可以安装技能和 CLI：

```bash
bash scripts/setup.sh
```

脚本会安装当前 Python 包，并把 `skills/` 同步到 `${ARKCLAW_SKILLS_DIR:-$HOME/.agents/skills}`。

## 配置

在当前工作区创建 `.env`：

```bash
cp .env.example .env
```

填写：

```bash
S2S_ARK_API_KEY=你的火山方舟APIKey
S2S_TEXT_MODEL=你的文本模型或端点ID
S2S_ARK_BASE_URL=https://ark.cn-beijing.volces.com
```

`ARK_API_KEY` 可作为 `S2S_ARK_API_KEY` 的 fallback。

## 使用

检查配置：

```bash
script2storyboard auth check
```

生成文字分镜：

```bash
script2storyboard convert examples/demo_script.md --force
```

默认输出：

```text
单集制作/EP001/文字分镜.md
```

离线校验：

```bash
script2storyboard check 单集制作/EP001/文字分镜.md
```

常用参数：

```bash
script2storyboard convert 剧本.md \
  --project-name "短剧第一集" \
  --style "都市写实" \
  --aspect 9:16 \
  --audience-mode female \
  --max-shot-seconds 4 \
  --clip-duration 15 \
  --output 单集制作/EP001/文字分镜.md \
  --force
```

## 导演规则

生成结果会使用增强结构：

- `## 连贯性设定`：记录人物站位、场景轴线、正反打方向、转场锚点和景别节奏。
- 每个 `## Clip N` 包含 `### 导演调度`：明确轴线与站位、正反打规则、切镜策略、转场锚点、景别节奏和频道思维。
- 分镜条目建议写成 `- 0-3s: [中近景/轴线左侧/承接上镜] ...`，让镜头不越轴、不乱切，转场更连贯。

频道参数：

```bash
# 女频：情绪流、关系张力、凝视/反应、细微动作和氛围转场
script2storyboard convert 剧本.md --audience-mode female

# 男频：目标推进、爽点、压迫感、力量变化、空间调度和冲击空镜
script2storyboard convert 剧本.md --audience-mode male --max-shot-seconds 3
```

`script2storyboard check` 会把台词遗漏、Clip 编号等基础问题作为错误；导演规则缺失会作为黄色提醒，不阻止旧格式分镜继续使用。
