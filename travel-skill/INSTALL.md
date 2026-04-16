# Travel Skill 安装与操作

## 1. 适用目录

- 技能目录:
  - `C:\Users\territoryliu\.codex\skills\travel-skill`
- 模型缓存目录:
  - `C:\Users\territoryliu\.codex\data\travel-skill-model-cache\whisper`

说明:

- `travel-skill` 是技能本体，应该放在 `.codex\skills` 下。
- `travel-skill-model-cache` 是运行时缓存，不属于技能代码，不要跟技能一起打包或提交。
- 当前默认逻辑会把 Whisper 模型缓存写到 `~\.codex\data\travel-skill-model-cache\whisper`。

## 2. 推荐环境

- Python 环境: 复用现有 conda 环境 `stock-analyzer`
- 依赖安装:

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world\travel-skill
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

`requirements.txt` 当前包含:

- `openai`
- `yt-dlp`
- `openai-whisper`
- `torch`
- `imageio-ffmpeg`

## 3. FFmpeg

视频回退链依赖 `ffmpeg`。当前代码会按以下顺序找它:

1. `TRAVEL_SKILL_FFMPEG_PATH`
2. 系统 `PATH`
3. 已知 Windows 路径:
   - `C:\lane\ffmpeg-2026-04-09-git-d3d0b7a5ee-full_build\bin\ffmpeg.exe`
   - `D:\software\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe`
4. `imageio-ffmpeg` 自带二进制

如果你想显式固定路径，建议设置:

```powershell
setx TRAVEL_SKILL_FFMPEG_PATH "C:\lane\ffmpeg-2026-04-09-git-d3d0b7a5ee-full_build\bin\ffmpeg.exe"
```

## 4. 关键环境变量

推荐设置:

```powershell
setx TRAVEL_SKILL_MODEL_DIR "C:\Users\territoryliu\.codex\data\travel-skill-model-cache\whisper"
```

可选设置:

```powershell
setx TRAVEL_SKILL_YT_DLP_PATH "C:\Users\territoryliu\.conda\envs\stock-analyzer\Scripts\yt-dlp.exe"
setx TRAVEL_SKILL_WHISPER_PATH "C:\Users\territoryliu\.conda\envs\stock-analyzer\Scripts\whisper.exe"
```

如果要启用 Codex / OpenAI 多模态关键帧评分:

```powershell
setx OPENAI_API_KEY "<your-key>"
setx TRAVEL_SKILL_ENABLE_MULTIMODAL "1"
setx TRAVEL_SKILL_MULTIMODAL_MODEL "gpt-5"
```

说明:

- 多模态评分是可选增强。
- 一旦多模态调用失败，流程会自动回退到启发式评分，不会阻断整条视频链。

## 5. 部署到 Codex Skills

如果你是在当前仓库内开发，最终落地步骤建议如下:

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world
python travel-skill\scripts\package_skill_release.py
```

默认会生成:

- `D:\vscode\hello-world\dist\travel-skill.zip`

然后把压缩包解压到:

- `C:\Users\territoryliu\.codex\skills\travel-skill`

目录下至少应保留:

- `SKILL.md`
- `scripts\`
- `references\`
- `assets\`
- `agents\`
- `testdata\`
- `requirements.txt`
- `INSTALL.md`

## 6. 不要一起带走的文件

下面这些属于运行产物、缓存或临时文件，不要随 skill 一起分发:

- `travel-skill-model-cache\`
- `dist\`
- `__pycache__\`
- `*.pyc`
- `.tmp-tests\`
- 生成出来的 research outputs
- 本地 smoke 测试产物

## 7. 首次安装操作步骤

### 方案 A: 从仓库直接部署

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world\travel-skill
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
setx TRAVEL_SKILL_MODEL_DIR "C:\Users\territoryliu\.codex\data\travel-skill-model-cache\whisper"
```

然后把整个 `travel-skill` 目录复制到:

- `C:\Users\territoryliu\.codex\skills\travel-skill`

### 方案 B: 用打包产物部署

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world
python travel-skill\scripts\package_skill_release.py
```

把 `dist\travel-skill.zip` 解压到:

- `C:\Users\territoryliu\.codex\skills\travel-skill`

## 8. 运行链路说明

当前视频增强链路已经包含:

1. 页面信息或本地视频输入
2. `yt-dlp` 下载视频
3. `ffmpeg` 抽音频
4. `ffmpeg` 抽关键帧
5. `whisper` 生成 `audio.json`
6. 关键帧打分
7. 优先使用多模态评分，可失败回退到启发式评分
8. 落盘:
   - `audio.json`
   - `keyframes.json`
   - `frame-scores.json`

## 9. 验证命令

开发机上建议串行运行，避免 Windows 下 `conda` 并发临时文件冲突:

```powershell
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_video_pipeline -v
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_video_media_scoring -v
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_package_skill_release -v
```

## 10. 常见问题

### Q1. `travel-skill-model-cache` 要不要放进 `.codex\skills`?

不要。

- `skills\travel-skill` 放代码和说明。
- `data\travel-skill-model-cache\whisper` 放 Whisper 模型缓存。

### Q2. 多模态分析失败会不会中断?

不会。

- 成功时，`frame-scores.json` 会标 `score_source=multimodal`
- 失败时，会回退到 `heuristic` 或 `heuristic-fallback`

### Q3. 打包出去时一来一回文件怎么处理?

建议规则:

- 代码只认 `travel-skill.zip`
- 缓存只在本机重建，不打包
- 研究产物按任务目录单独存，不塞进技能包
- 升级 skill 时直接覆盖 `skills\travel-skill`
- 不要删除 `data\travel-skill-model-cache\whisper`，这样可以复用已下载模型
