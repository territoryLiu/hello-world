# Travel Skill 安装、部署与批量运行说明

本文档面向本地 Windows 环境，默认约定：

- 技能目录：`C:\Users\territoryliu\.codex\skills\travel-skill`
- 模型缓存目录：`C:\Users\territoryliu\.codex\data\travel-skill-model-cache\whisper`
- Python 环境：`conda activate stock-analyzer`

`travel-skill` 是技能代码目录，`travel-skill-model-cache` 是运行时缓存目录。两者必须分开，不要把模型缓存打进技能包。

## 1. 目录职责

建议按下面的职责分层：

- `C:\Users\territoryliu\.codex\skills\travel-skill`
  - 放技能代码、脚本、模板、测试数据、说明文档
- `C:\Users\territoryliu\.codex\data\travel-skill-model-cache\whisper`
  - 放 Whisper 模型缓存
- `travel-data\...`
  - 放每次研究任务的知识沉淀和中间产物
- `.tmp-tests\...`
  - 放本地临时测试产物
- `dist\travel-skill.zip`
  - 放打包后的交付物

不要把下面这些内容和技能源码混放：

- Whisper 模型文件
- 临时视频、音频、关键帧
- research run 的 `bundle.json`、`coverage.json`
- `__pycache__`、`*.pyc`

## 2. 环境准备

推荐直接复用现有环境：

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world\travel-skill
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

当前 `requirements.txt` 主要包含：

- `openai`
- `yt-dlp`
- `openai-whisper`
- `torch`
- `imageio-ffmpeg`

## 3. FFmpeg 与关键环境变量

视频回退链依赖 `ffmpeg`。当前代码按下面顺序找可执行文件：

1. `TRAVEL_SKILL_FFMPEG_PATH`
2. 系统 `PATH`
3. 已知 Windows 路径
   - `C:\lane\ffmpeg-2026-04-09-git-d3d0b7a5ee-full_build\bin\ffmpeg.exe`
   - `D:\software\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe`
4. `imageio-ffmpeg` 自带二进制

建议显式设置：

```powershell
setx TRAVEL_SKILL_FFMPEG_PATH "C:\lane\ffmpeg-2026-04-09-git-d3d0b7a5ee-full_build\bin\ffmpeg.exe"
setx TRAVEL_SKILL_MODEL_DIR "C:\Users\territoryliu\.codex\data\travel-skill-model-cache\whisper"
```

可选设置：

```powershell
setx TRAVEL_SKILL_YT_DLP_PATH "C:\Users\territoryliu\anaconda3\envs\stock-analyzer\Scripts\yt-dlp.exe"
setx TRAVEL_SKILL_WHISPER_PATH "C:\Users\territoryliu\anaconda3\envs\stock-analyzer\Scripts\whisper.exe"
```

如果要启用 Codex / OpenAI 多模态关键帧评分：

```powershell
setx OPENAI_API_KEY "<your-key>"
setx TRAVEL_SKILL_ENABLE_MULTIMODAL "1"
setx TRAVEL_SKILL_MULTIMODAL_MODEL "gpt-5"
```

说明：

- 多模态评分是增强项，不是硬依赖
- 调用失败时会自动回退到启发式评分，不会中断视频链路

## 4. 部署到 Codex Skills

### 方案 A：直接复制源码目录

适合本机持续开发。

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world\travel-skill
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

然后把整个目录复制到：

- `C:\Users\territoryliu\.codex\skills\travel-skill`

### 方案 B：打包后再部署

适合交付给别的机器或做版本归档。

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world
python travel-skill\scripts\package_skill_release.py
```

默认输出：

- `D:\vscode\hello-world\dist\travel-skill.zip`

把压缩包解压到：

- `C:\Users\territoryliu\.codex\skills\travel-skill`

技能目录至少应保留：

- `SKILL.md`
- `scripts\`
- `references\`
- `assets\`
- `agents\`
- `testdata\`
- `requirements.txt`
- `INSTALL.md`

## 5. 打包时如何处理文件

推荐规则如下：

- 技能包只带代码、模板、说明、测试数据
- 模型缓存不打包
- 每次 research run 的产物不打包
- `dist\` 只作为导出目录，不再反向打进 zip

当前打包脚本 [package_skill_release.py](d:/vscode/hello-world/travel-skill/scripts/package_skill_release.py) 会自动排除：

- `__pycache__`
- `.pytest_cache`
- `*.pyc`
- `*.pyo`
- `*.tmp`
- `*.bak`
- `*.log`

如果是对外分发，建议只交付：

1. `travel-skill.zip`
2. 本文档
3. 一份环境变量清单

不要一起交付：

1. `travel-skill-model-cache`
2. `travel-data`
3. `.tmp-tests`
4. 本机 smoke 测试视频和转录产物

## 6. 批量研究的推荐命令链

当前批量 research 的主流程已经接通。建议按下面的顺序执行。

### 步骤 1：标准化请求

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world
python travel-skill\scripts\normalize_request.py --input request.json --output normalized.json
```

### 步骤 2：生成 research tasks

```powershell
python travel-skill\scripts\build_research_tasks.py --input normalized.json --output tasks.json
```

### 步骤 3：生成 web runs

```powershell
python travel-skill\scripts\build_web_research_runs.py --input tasks.json --output runs.json
```

此时 `runs.json` 已经包含：

- `batch_id`
- `runs[*].run_id`
- `runs[*].expected_bundle_path`
- `runs[*].expected_coverage_path`
- `batch_manifest`

`batch_manifest` 已经可以直接给聚合器使用。

### 步骤 4：逐个执行 web-access run

这一步通常由外层调度器或人工循环执行。每个 run 需要：

1. 使用 `run.prompt` 调起 web-access
2. 把 web-access 返回结果保存成 `web-result.json`
3. 调用 `finalize_web_research_run.py` 完成归一化、校验和落盘

示例：

```powershell
python travel-skill\scripts\finalize_web_research_run.py `
  --run-file one-run.json `
  --web-result one-run-web-result.json `
  --bundle-output travel-data\trips\demo-trip\research\web-runs\demo-run\bundle.json `
  --coverage-output travel-data\trips\demo-trip\research\web-runs\demo-run\coverage.json `
  --output-root travel-data
```

### 步骤 5：聚合整个 batch

现在聚合器支持两种输入：

1. 纯 `manifest.json`
2. 完整 `runs.json`，它会自动读取里面的 `batch_manifest`

直接用 `runs.json` 即可：

```powershell
python travel-skill\scripts\aggregate_web_research_batch.py `
  --input runs.json `
  --bundle-output batch-bundle.json `
  --coverage-output batch-coverage.json `
  --review-output-dir review-packet
```

聚合结果会包含：

- 批量 `bundle.json`
- 批量 `coverage.json`
- `research-packet.md`
- `research-packet.html`

## 7. 视频回退链当前能力

当前视频增强链已经具备：

1. 页面信息提取
2. 本地视频或远程视频输入
3. `yt-dlp` 下载视频
4. `ffmpeg` 抽音频
5. `ffmpeg` 抽关键帧
6. `whisper` 生成 `audio.json`
7. 关键帧评分
   - 优先多模态评分
   - 失败时回退到启发式评分
8. 落盘产物
   - `audio.json`
   - `keyframes.json`
   - `frame-scores.json`
   - `selected-frames.json` 或等价选择结果

这意味着“视频下载、音频转文字、关键帧分析”现在都已经进入可运行状态；只是多模态评分仍然是可选增强，不是硬依赖。

## 8. 首次安装后的最小验收

建议至少跑下面几组串行验证。Windows 下不要并发跑多个 `conda run`。

```powershell
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_video_pipeline -v
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_video_media_scoring -v
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_package_skill_release -v
conda run -n stock-analyzer python -m unittest travel-skill.tests.test_build_research_tasks tests.test_intake_research tests.test_research_packet -v
```

如果只想做语法检查：

```powershell
conda run -n stock-analyzer python -m py_compile `
  travel-skill\scripts\build_web_research_runs.py `
  travel-skill\scripts\aggregate_web_research_batch.py `
  travel-skill\scripts\video_pipeline.py
```

## 9. 常见问题

### Q1. `travel-skill-model-cache` 要不要放进 `C:\Users\territoryliu\.codex\skills\travel-skill`？

不要。

- `skills\travel-skill` 只放技能源码
- `data\travel-skill-model-cache\whisper` 放模型缓存

升级技能时直接覆盖源码目录即可，不要删缓存目录。这样 Whisper 模型可以复用。

### Q2. 多模态分析失败会不会让整条视频链中断？

不会。

- 成功时，关键帧评分会标记为多模态来源
- 失败时，会自动回退到启发式评分

### Q3. 对外打包时，一来一回的研究产物怎么处理？

建议这样做：

- 技能包只交付代码
- 缓存由目标机器首次运行时自动建立
- research 产物按任务目录单独保存
- 不要把 `travel-data` 里的具体任务结果塞进技能包

### Q4. 现在是不是一个完整的 skill 了？

从结构上看，已经具备一个可部署 skill 的核心条件：

- 有 `SKILL.md`
- 有脚本目录和依赖清单
- 有安装文档
- 有打包脚本
- 有视频回退链
- 有 batch research 聚合链

还没有做的是更高层的外部调度器和线上服务化。这不影响它作为本地 Codex skill 使用和分发。
