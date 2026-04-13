# Travel Skill Dedup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理 `.codex/skills/travel-skill` 的历史冗余文件与多点规则定义，并用测试约束关键配置和文档不再漂移。

**Architecture:** 以 `scripts/travel_config.py` 作为运行时常量唯一来源，以 `references/` 作为文档型权威来源，把 `SKILL.md` 和 `agents/openai.yaml` 收紧成入口与执行合同。先补一致性测试，再做文档与模板删除，最后跑回归验证。

**Tech Stack:** Python `unittest`, repo-local skill scripts, Markdown/YAML/HTML assets, Git worktree

---

### Task 1: 补规则与文档一致性测试

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/travel_config.py`
- Modify: `tests/test_config_centralization.py`
- Test: `tests/test_config_centralization.py`

- [ ] **Step 1: 写失败测试，锁定距离阈值和文档路径一致性**

```python
class TravelConfigCentralizationTest(unittest.TestCase):
    def test_transport_threshold_is_1000km(self):
        config = load_module("travel_config")
        self.assertEqual(config.FLIGHT_HYBRID_THRESHOLD_KM, 1000)

    def test_sharing_modes_reference_guides_root(self):
        sharing_modes = (SKILL_DIR / "references" / "sharing-modes.md").read_text(encoding="utf-8")
        self.assertIn("guides/<slug>/desktop", sharing_modes)
        self.assertNotIn("trips/<slug>/desktop", sharing_modes)
```

- [ ] **Step 2: 运行测试，确认当前会失败**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_config_centralization.py -q`
Expected: FAIL，因为当前 `sharing-modes.md` 仍含旧的 `trips/<slug>/...` 路径，且还没有针对文档一致性的断言。

- [ ] **Step 3: 最小实现，保证测试围绕共享配置与权威文档工作**

```python
FLIGHT_HYBRID_THRESHOLD_KM = 1000
LONG_DISTANCE_RULE_OVER = f"over-{FLIGHT_HYBRID_THRESHOLD_KM}km"
LONG_DISTANCE_RULE_WITHIN = f"within-{FLIGHT_HYBRID_THRESHOLD_KM}km"
```

```python
def test_runtime_publish_artifacts_match_reference():
    config = load_module("travel_config")
    sharing_modes = (SKILL_DIR / "references" / "sharing-modes.md").read_text(encoding="utf-8")
    self.assertIn(config.PUBLISH_ARTIFACTS["portal"], sharing_modes)
    self.assertIn(config.PUBLISH_ARTIFACTS["recommended"], sharing_modes)
    self.assertIn(config.PUBLISH_ARTIFACTS["share"], sharing_modes)
```

- [ ] **Step 4: 再跑测试，确认通过**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_config_centralization.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add .codex/skills/travel-skill/scripts/travel_config.py tests/test_config_centralization.py
git commit -m "test: 补充 travel-skill 规则一致性校验"
```

### Task 2: 收紧 `SKILL.md` 与 `agents/openai.yaml`

**Files:**
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Modify: `.codex/skills/travel-skill/agents/openai.yaml`
- Test: `tests/test_contract.py`

- [ ] **Step 1: 写失败测试，锁定入口文档和 agent 合同的收紧目标**

```python
class TravelContractTest(unittest.TestCase):
    def test_openai_prompt_no_longer_hardcodes_600km(self):
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertNotIn("600km transport rule", text)
        self.assertIn("runtime config", text)

    def test_skill_doc_points_to_references_instead_of_repeating_schema(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/content-schema.md", text)
        self.assertIn("references/sharing-modes.md", text)
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_contract.py -q`
Expected: FAIL，因为当前 `agents/openai.yaml` 仍包含 `600km transport rule`，`SKILL.md` 仍手写大量 contract 细节。

- [ ] **Step 3: 最小实现，收紧入口文档与执行合同**

```yaml
default_prompt: |
  Travel Skill execution contract:
  1. Run intake first and normalize the request payload.
  2. Build concrete site tasks and run online collection through web-access.
  3. Validate site coverage before review-gate and report missing coverage explicitly.
  4. Compose, localize, render, package, and verify using runtime config and skill references.
```

```markdown
## Canonical References

- Schema: `references/content-schema.md`
- Sharing modes: `references/sharing-modes.md`
- Research contract: `references/web-access-research-contract.md`
- Source priority: `references/source-priority.md`
```

- [ ] **Step 4: 再跑测试，确认通过**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_contract.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add .codex/skills/travel-skill/SKILL.md .codex/skills/travel-skill/agents/openai.yaml tests/test_contract.py
git commit -m "refactor: 收紧 travel-skill 入口文档与执行合同"
```

### Task 3: 收敛 reference 文档并修正旧路径

**Files:**
- Modify: `.codex/skills/travel-skill/references/sharing-modes.md`
- Modify: `.codex/skills/travel-skill/references/research-checklists.md`
- Modify: `.codex/skills/travel-skill/references/content-schema.md`
- Test: `tests/test_contract.py`

- [ ] **Step 1: 写失败测试，锁定 reference 的职责边界**

```python
def test_sharing_modes_drops_duplicate_ordered_sections():
    text = (SKILL_DIR / "references" / "sharing-modes.md").read_text(encoding="utf-8")
    self.assertNotIn("## Ordered Sections", text)
    self.assertIn("content-schema.md", text)

def test_research_checklists_stays_review_oriented():
    text = (SKILL_DIR / "references" / "research-checklists.md").read_text(encoding="utf-8")
    self.assertNotIn("Required persisted fields", text)
    self.assertIn("## Delivery", text)
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_contract.py -q`
Expected: FAIL，因为 `sharing-modes.md` 还包含重复的 ordered sections，且旧路径仍存在。

- [ ] **Step 3: 最小实现，保留权威 reference，删除重复定义**

```markdown
## Output Layout

- `guides/<slug>/desktop/route-first/index.html`
- `guides/<slug>/desktop/decision-first/index.html`
- `guides/<slug>/mobile/route-first/index.html`
- `guides/<slug>/notes/sources.md`

Section ordering and layer structure are defined in `content-schema.md` and runtime config.
```

```markdown
## Delivery

- desktop and mobile contain the same facts
- share package includes `portal.html`, `recommended.html`, `share.html`, `package.zip`
- final render passes static checks and Playwright checks
```

- [ ] **Step 4: 再跑测试，确认通过**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_contract.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add .codex/skills/travel-skill/references/sharing-modes.md .codex/skills/travel-skill/references/research-checklists.md .codex/skills/travel-skill/references/content-schema.md tests/test_contract.py
git commit -m "docs: 收敛 travel-skill reference 权威来源"
```

### Task 4: 删除未引用旧模板并补防回归测试

**Files:**
- Delete: `.codex/skills/travel-skill/assets/templates/guide-template-classic.html`
- Delete: `.codex/skills/travel-skill/assets/templates/guide-template-minimalist.html`
- Delete: `.codex/skills/travel-skill/assets/templates/guide-template-original.html`
- Delete: `.codex/skills/travel-skill/assets/templates/guide-template-vintage.html`
- Delete: `.codex/skills/travel-skill/assets/templates/guide-template-zen.html`
- Delete: `.codex/skills/travel-skill/assets/templates/desktop-index.html`
- Delete: `.codex/skills/travel-skill/assets/templates/mobile-index.html`
- Delete: `.codex/skills/travel-skill/assets/templates/mobile-classic.html`
- Delete: `.codex/skills/travel-skill/assets/templates/mobile-minimalist.html`
- Delete: `.codex/skills/travel-skill/assets/templates/mobile-original.html`
- Delete: `.codex/skills/travel-skill/assets/templates/mobile-vintage.html`
- Delete: `.codex/skills/travel-skill/assets/templates/mobile-zen.html`
- Modify: `tests/test_render_package.py`
- Test: `tests/test_render_package.py`

- [ ] **Step 1: 写失败测试，锁定当前活跃模板只来自 `template-*.html`**

```python
def test_only_template_dash_first_files_drive_rendering(self):
    template_dir = SKILL_DIR / "assets" / "templates"
    active = sorted(path.name for path in template_dir.glob("template-*.html"))
    self.assertEqual(active, [
        "template-decision-first.html",
        "template-destination-first.html",
        "template-lifestyle-first.html",
        "template-route-first.html",
        "template-transport-first.html",
    ])
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_render_package.py -q`
Expected: FAIL，如果测试同时断言旧模板不应存在，则当前会失败。

- [ ] **Step 3: 删除未引用旧模板，并保留现有五套活跃模板**

```text
保留:
- template-decision-first.html
- template-destination-first.html
- template-lifestyle-first.html
- template-route-first.html
- template-transport-first.html

删除:
- guide-template-*.html
- desktop-index.html
- mobile-*.html
```

- [ ] **Step 4: 再跑测试，确认通过**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_render_package.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_render_package.py .codex/skills/travel-skill/assets/templates
git commit -m "refactor: 删除未使用的 travel-skill 历史模板"
```

### Task 5: 跑渲染与校验回归

**Files:**
- Modify: `tests/test_verify.py`
- Test: `tests/test_verify.py`
- Test: `tests/test_config_centralization.py`
- Test: `tests/test_contract.py`
- Test: `tests/test_render_package.py`

- [ ] **Step 1: 写失败测试，锁定最终校验仍覆盖五模板与来源页**

```python
def test_verify_trip_still_requires_five_templates_and_source_notes(self):
    payload = module.verify_trip(guide_root)
    self.assertTrue(payload["content_checks"]["desktop_templates_complete"])
    self.assertTrue(payload["content_checks"]["mobile_templates_complete"])
    self.assertTrue(payload["content_checks"]["share_artifacts_present"])
```

- [ ] **Step 2: 运行单测，确认当前实现若有回归会被抓到**

Run: `set PYTHONPATH=d:\vscode\hello-world && python -m pytest tests/test_verify.py -q`
Expected: PASS 或 FAIL；若 FAIL，先修行为再继续，不允许带已知回归进入最终验证。

- [ ] **Step 3: 运行完整相关测试集**

```bash
set PYTHONPATH=d:\vscode\hello-world
python -m pytest tests/test_config_centralization.py tests/test_contract.py tests/test_render_package.py tests/test_verify.py -q
```

Expected: 全部 PASS

- [ ] **Step 4: 读取 git 状态并整理验证结果**

Run: `git -c core.quotepath=false status --short --branch`
Expected: 只剩本次分支中的预期改动，无额外临时产物污染

- [ ] **Step 5: 提交**

```bash
git add tests/test_verify.py tests/test_config_centralization.py tests/test_contract.py tests/test_render_package.py .codex/skills/travel-skill
git commit -m "test: 完成 travel-skill 冗余清理回归"
```

## Spec Coverage Self-Review

- 规则漂移：Task 1、Task 2、Task 3 覆盖 `1000km` 与路径一致性。
- 死文件残留：Task 4 覆盖旧模板删除。
- 文档多点维护：Task 2、Task 3 覆盖入口文档、agent 合同、reference 收敛。
- 回归验证：Task 5 覆盖渲染、校验与产物完整性。

## Placeholder Scan

- 已检查，无 `TBD`、`TODO`、`implement later`、`similar to task` 这类占位描述。

## Type Consistency

- 距离阈值统一为 `FLIGHT_HYBRID_THRESHOLD_KM`
- 模板目录统一使用 `template-*.html`
- 输出路径统一使用 `guides/<slug>/...`

