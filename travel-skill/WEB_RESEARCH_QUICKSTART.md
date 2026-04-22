# Travel Skill Web Research Quickstart

这份文档只保留最短操作路径，不解释设计背景。

默认环境：

```powershell
conda activate stock-analyzer
cd D:\vscode\hello-world
```

## 1. 真实请求最短链路

准备一个请求文件，例如 `request.json`：

```json
{
  "title": "五一延吉长白山",
  "departure_city": "南京",
  "destinations": ["延吉", "长白山"],
  "date_range": {
    "start": "2026-04-30",
    "end": "2026-05-05"
  },
  "travelers": {
    "count": 4,
    "adults": 3,
    "children": 1,
    "age_notes": "1 位 7 岁儿童，2 位 60+ 长辈"
  },
  "budget": {
    "mode": "per_person",
    "min": 3000,
    "max": 5000
  }
}
```

第一步，生成 `runs.json`：

```powershell
python travel-skill\scripts\web_research_cli.py build-runs `
  --request request.json `
  --normalized-output normalized.json `
  --tasks-output tasks.json `
  --runs-output runs.json
```

第二步，导出给外部 `web-access` runner 的请求包：

```powershell
python travel-skill\scripts\web_research_cli.py export-request `
  --runs-file runs.json `
  --output web-access-batch.json `
  --packets-dir web-access-packets `
  --web-results-dir web-results
```

第三步，外部 `web-access` runner 执行后，把批量结果回填为本地目录结构：

```powershell
python travel-skill\scripts\web_research_cli.py materialize-results `
  --input web-access-batch-results.json `
  --web-results-dir web-results `
  --report-output web-results-materialize-report.json
```

如果你要先给外部同学交一个 handoff 包，可以插入这一步：

```powershell
python travel-skill\scripts\web_research_cli.py prepare-handoff `
  --runs-file runs.json `
  --output-dir web-access-handoff `
  --web-results-dir web-results
```

如果你拿到了对方回传的 `web-access-batch-results.json`，建议先校验再 materialize：

```powershell
python travel-skill\scripts\web_research_cli.py validate-results `
  --runs-file runs.json `
  --input web-access-batch-results.json `
  --report-output web-access-batch-validate-report.json
```

第四步，执行 finalize + aggregate：

```powershell
python travel-skill\scripts\web_research_cli.py execute-batch `
  --runs-file runs.json `
  --web-results-dir web-results `
  --output-root travel-data `
  --batch-bundle-output batch-bundle.json `
  --batch-coverage-output batch-coverage.json `
  --review-output-dir review-packet `
  --execution-report-output execution-report.json
```

执行完成后，重点看这些文件：

- `runs.json`
- `web-access-batch.json`
- `web-results\`
- `execution-report.json`
- `batch-bundle.json`
- `batch-coverage.json`
- `review-packet\research-packet.html`

## 2. Fixture Smoke 最短链路

如果你只是想验证文件协议和批处理链本身，不需要真实联网，直接跑：

```powershell
python travel-skill\scripts\web_research_cli.py smoke `
  --fixtures-root tests\fixtures\travel_skill\web_batch_smoke `
  --output-dir .tmp-tests\web-batch-smoke
```

完成后，重点看：

- `.tmp-tests\web-batch-smoke\web-access-batch.json`
- `.tmp-tests\web-batch-smoke\web-access-packets\`
- `.tmp-tests\web-batch-smoke\web-results\`
- `.tmp-tests\web-batch-smoke\execution-report.json`
- `.tmp-tests\web-batch-smoke\batch-bundle.json`
- `.tmp-tests\web-batch-smoke\review-packet\research-packet.html`

## 3. 两条最常用验收命令

只验 smoke：

```powershell
conda run -n stock-analyzer python -m unittest tests.test_intake_research.IntakeResearchTest.test_run_web_access_batch_smoke_executes_full_file_protocol_chain -v
```

验统一入口：

```powershell
conda run -n stock-analyzer python -m unittest tests.test_intake_research.IntakeResearchTest.test_web_research_cli_build_runs_chains_normalize_tasks_and_runs tests.test_intake_research.IntakeResearchTest.test_web_research_cli_smoke_subcommand_runs_fixture_chain -v
```

## 4. 最少记忆版

你只需要记住下面两条：

真实请求：

```powershell
python travel-skill\scripts\web_research_cli.py build-runs ...
python travel-skill\scripts\web_research_cli.py prepare-handoff ...
python travel-skill\scripts\web_research_cli.py export-request ...
python travel-skill\scripts\web_research_cli.py validate-results ...
python travel-skill\scripts\web_research_cli.py materialize-results ...
python travel-skill\scripts\web_research_cli.py execute-batch ...
```

本地 smoke：

```powershell
python travel-skill\scripts\web_research_cli.py smoke --fixtures-root tests\fixtures\travel_skill\web_batch_smoke --output-dir .tmp-tests\web-batch-smoke
```

## 5. Delivery Gate

Before publishing guide正文、导出分享页或打包 ZIP，必须先运行：

```powershell
python travel-skill\scripts\validate_delivery_gate.py `
  --guide-root travel-data\guides\<trip-slug> `
  --trip-root travel-data\trips\<trip-slug> `
  --output delivery-gate-report.json
```

Pass conditions:
- `request\gate-report.json` exists and `can_proceed=true`
- CDP ready evidence exists, or there is an actual `web-access` execution record
- `batch-coverage.json` / `coverage.json` contains `coverage_status` for `xiaohongshu`, `douyin`, and `bilibili`

If this gate fails:
- do not ship the guide正文
- do not package ZIP
- fix collection gaps first or record explicit failure reasons
