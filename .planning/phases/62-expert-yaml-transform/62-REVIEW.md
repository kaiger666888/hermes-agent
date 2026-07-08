---
phase: 62-expert-yaml-transform
reviewed: 2026-07-08T00:38:52Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - scripts/validate_phase62_yamls.py
  - tests/scripts/test_validate_phase62_yamls.py
  - /home/kai/.hermes/agents/animation_studio.agent.yaml
  - /home/kai/.hermes/agents/colorist.agent.yaml
  - /home/kai/.hermes/agents/compliance_gate.agent.yaml
  - /home/kai/.hermes/agents/creative_source.agent.yaml
  - /home/kai/.hermes/agents/documentary_maker.agent.yaml
  - /home/kai/.hermes/agents/performer.agent.yaml
  - /home/kai/.hermes/agents/production.agent.yaml
  - /home/kai/.hermes/agents/prompt_injector.agent.yaml
  - /home/kai/.hermes/agents/scene_builder.agent.yaml
  - /home/kai/.hermes/agents/script_auditor.agent.yaml
  - /home/kai/.hermes/agents/storyboard_designer.agent.yaml
  - /home/kai/.hermes/agents/visual_executor.agent.yaml
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: fixed
---

# Phase 62: Code Review Report

**Reviewed:** 2026-07-08T00:38:52Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Phase 62 交付物包括 1 个 validator 脚本 + 1 个 pytest 测试文件 + 12 个 agent YAML。
整体质量良好:validator 正确使用 `Draft202012Validator` + `yaml.safe_load`,
所有 12 个 YAML 通过 schema 校验(21/21 PASS),14/14 测试通过,lineage
`skill_sha256` 全部与源 SKILL.md 实际 SHA-256 匹配(逐个核对),DAG `related_agents`
零 dangling edges,prompt-injection 扫描零命中。

但 review 发现 4 个 WARNING + 5 个 INFO 级问题,主要集中点:
1. `documentary_maker` persona 含明显 typo "Flaherty romantic-romantic"(应为
   "Flaherty romantic tradition" 或类似),损害专家权威性。
2. `visual_executor` 与 `continuity_auditor` 在 `prerequisites.tools` 列出
   `hermes_llm_vision` 但 `tools`(运行时白名单)未列入 — 这是 schema 允许的
   (prereq ≠ runtime grants),但源 SKILL 明确将该工具用于运行时图像比较,
   存在语义不一致。
3. validator 脚本顶层 `import hashlib` 标注 "reserved" 但实际未使用 — dead import。
4. `compliance_gate.transform_notes` 引用 `aliases: [compliance_marketing]` 字段,
   但该字段不在 18-field schema 中 — 文档自引用不可解析。

无 BLOCKER。代码可发布,建议在发布前修复 WARNING。

## Structural Findings (fallow)

本次 review 未接收 `<structural_findings>` 输入;以下为 narrative findings。

## Narrative Findings (AI reviewer)

### Warnings

### WR-01: `documentary_maker` persona 含明显 typo "Flaherty romantic-romantic"

**File:** `/home/kai/.hermes/agents/documentary_maker.agent.yaml:8-9`
**Issue:**
persona 写道 "the 4 documentary schools (Flaherty romantic-romantic / Vertov
kino-eye / Grierson creative-treatment-of-actuality / Direct-Vérité
observational-trust)"。"Flaherty romantic-romantic" 是 tautology(romantic-romantic
无意义),且与源 SKILL.md 不符 — 源用 "Flaherty 模式"(Flaherty mode/pattern),
电影学标准术语是 "Flaherty romantic tradition" 或 "Flaherty romantic-nanook
style"。其余 3 个学派的描述符(Vertov kino-eye / Grierson creative-treatment-of-actuality
/ Direct-Vérité observational-trust)都是单一概念,唯独 Flaherty 的描述符
退化成了无意义的叠词。这会被 LLM 读为"Flaherty 学派叫 romantic-romantic",
污染下游生成 + 损害专家权威性。

**Fix:**
```yaml
# 修改 line 8-9,将 "Flaherty romantic-romantic" 改为有意义的电影学术语:
persona: 'I am the Documentary Maker Expert (纪录片创作专家). I apply the 6 documentary types
  per Bill Nichols (poetic / expository / observational / participatory / reflexive
  / performative) and the 4 documentary schools (Flaherty romantic-tradition / Vertov
  kino-eye / Grierson creative-treatment-of-actuality / Direct-Vérité observational-trust)
  as my theoretical backbone. ...'
```
推荐用 "romantic-tradition"(《Nanook of the North》代表的浪漫化纪录传统)。

---

### WR-02: `visual_executor` 与 `continuity_auditor` 的 `prerequisites.tools` 引用 `hermes_llm_vision` 但运行时 `tools` 白名单未列入

**File:** `/home/kai/.hermes/agents/visual_executor.agent.yaml:16-22,63-66`
**File:** `/home/kai/.hermes/agents/continuity_auditor.agent.yaml:13-16,42-45`
**Issue:**
两个 YAML 都在 `prerequisites.tools` 列出 `hermes_llm_vision`,但运行时 `tools`
白名单只列 `hermes_llm`。schema(`agents-schema.yaml` §2.5 + §2.12)明确二者
不同:prereq 是 activation CONDITIONS,runtime tools 是 GRANTS。所以 schema-valid。

但源 SKILL.md 明确把 `hermes_llm_vision` 用于**运行时**操作:
- `visual_executor/SKILL.md:177,179`: "Character Consistency Check — Validate
  against reference (uses `hermes_llm_vision`)"、"Quality Check — Verify against
  thresholds (uses `hermes_llm_vision`)"
- `continuity_auditor/SKILL.md:21,25`: "Uses `hermes_llm_vision` for image
  comparison"

若 dispatcher 严格按 `tools` 白名单过滤(ARCHITECTURE §4.3),agent 在运行时
拿不到 vision 能力,无法执行 persona 声明的"4-dimension cross-shot audit"或
"visual quality check"。`prerequisites.tools` 仅作为激活门,不授予运行时权限。

注:这是 Phase 49(v11.0 已 ship 的 continuity_auditor)沿袭下来的同一模式,
不是 Phase 62 引入的新问题;但 Phase 62 的 visual_executor 是新交付物,应明确
该工具的运行时归属。

**Fix:**
明确二选一并文档化:
- **方案 A(推荐)**:若 `hermes_llm_vision` 是 `hermes_llm` 的子能力(通过 model
  选择启用,不是独立工具),则在两处 `tools` 白名单显式列入 `hermes_llm_vision`
  以消除歧义,或从 `prerequisites.tools` 移除(避免误导 dispatcher 实现)。
- **方案 B**:若 `hermes_llm_vision` 是独立工具且 dispatcher 已实现按
  `prerequisites.tools` 自动授权,则在 `transform_notes` 显式声明该语义。

```yaml
# 方案 A — visual_executor.agent.yaml
tools:
- hermes_llm
- hermes_llm_vision   # 显式授予,与 persona "Quality Check uses hermes_llm_vision" 对齐
- dreamina_cli
- read_file
- write_file
- patch
```

---

### WR-03: validator 脚本顶层 `import hashlib` 标注 "reserved" 但实际未使用(dead import)

**File:** `scripts/validate_phase62_yamls.py:31`
**Issue:**
```python
import hashlib  # reserved: Plan 04 SHA spot-check import compat (do not remove)
```
模块顶层导入 `hashlib` 但全文无任何 `hashlib.` 引用(grep 验证:仅 docstring
提及 + import 行本身)。注释声称"Plan 04 SHA spot-check import compat",但:
1. Plan 04 的 SHA spot-check 应在该 plan 自己的脚本中导入,不需要本脚本预留。
2. CLAUDE.md "Code Style" 明确"No `from x import *`",反推亦不鼓励 unused import。
3. Ruff 配置只开 `PLW1514`(`pyproject.toml:270-282`),所以 `F401` 未启用、
   此 import 不会被 lint 拦截 — 这是 lint gap,不应当成"通过了所以没问题"。
4. 若未来有人误以为 `hashlib` 已 import,在脚本中加 SHA 校验逻辑,不会触发
   重导入警告,可能掩盖实际需要的 `import` 漏写。

注释 `(do not remove)` 强化了"保留即正确"的错觉。

**Fix:**
```python
# 直接删除 line 31。若 Plan 04 真的需要 hashlib,在自己的脚本中导入。
# 删除前可加一行注释指向 Plan 04:
# NOTE: Plan 04 SHA spot-check 应在自己的脚本中导入 hashlib,本文件不预留。
```

---

### WR-04: `compliance_gate.transform_notes` 引用 `aliases: [compliance_marketing]` 字段,但该字段不在 18-field schema 中

**File:** `/home/kai/.hermes/agents/compliance_gate.agent.yaml:31`
**Issue:**
```
transform_notes: 'Rule IDs: §2.15 compliance_gate (...). ... Renamed
  from legacy compliance_marketing (aliases: [compliance_marketing]). Transform
  timestamp: 2026-07-08T00:00:00Z.'
```
源 SKILL.md 的 frontmatter 确实有 `metadata.hermes.aliases: [compliance_marketing]`,
但 18-field agent YAML schema(`agents-schema.yaml`)无 `aliases` 字段 — 该字段
在 SKILL→agent transform 中被丢弃(不在 ARCHITECTURE §1.2 disposition 的
"9 copy / 2 drop / 1 rewrite" 任何一类中明确处理,实际结果是不可见)。

transform_notes 自引用一个 YAML 不具备的字段会造成:
1. curator 的 SKILL↔agent drift 检测可能困惑(查找 `aliases` 字段不存在)。
2. 未来 transform-CLI 实现者读到这条 notes,误以为应在 YAML 中保留 `aliases`。
3. FOUND-08 backward-compat 路径若依赖 `expert_id` map 而非 `aliases` 字段,
   此 notes 会误导维护者。

**Fix:**
改写为不引用不存在字段的版本:
```yaml
transform_notes: 'Rule IDs: §2.15 compliance_gate (hard-gate red-line authority,
  3 v9.0 red-lines). CONTEXT.md locked decision overrides §2.15/§3.6 recommendation:
  default_invocation=mcp_tool (NOT disabled) per all-12-active-experts policy. Renamed
  from legacy expert_id compliance_marketing (Phase 13 RENAME-02) — backward-compat
  routing via expert_id map, not via a YAML aliases field (18-field schema has no
  aliases). Transform timestamp: 2026-07-08T00:00:00Z.'
```

---

### Info

### IN-01: validator `--batch` choices 与 config 块描述不一致

**File:** `scripts/validate_phase62_yamls.py:160-172`
**Issue:**
config 块描述 `--batch A|B|all`,但 argparse `choices=("A", "B")` 只接受 A/B
(`all` 由 no-flag 实现)。`--help` 输出 `usage: validate_phase62_yamls.py [-h] [--batch {A,B}]`
是准确的,但 phase config 与脚本注释存在轻微 drift。

非功能 bug,但会让 reviewer/操作员短暂困惑"为何 `--batch all` 报 invalid choice"。

**Fix:**
统一表述:在 docstring line 6 与 phase config 都改成 `--batch {A|B}` 或
`--batch {A|B} or no-flag for the full sweep`(脚本 help 已是后者,以此为准)。

---

### IN-02: validator `main()` 在 schema 文件缺失时抛裸 FileNotFoundError traceback

**File:** `scripts/validate_phase62_yamls.py:185`
**Issue:**
`schema = load_schema()` 在 `SCHEMA_PATH` 不存在时抛 `FileNotFoundError`,
`main()` 未捕获,CLI 用户会看到完整 Python traceback。对 CLI 工具而言不友好
(虽然 exit code 非 0 正确)。

非阻塞 — 操作员能从 traceback 中看到文件路径,但用户体验差。

**Fix:**
```python
def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        schema = load_schema()
    except FileNotFoundError as exc:
        print(f"ERROR: schema file missing: {exc}", file=sys.stderr)
        return 2  # distinct exit code for infra-missing vs validation-fail
    # ...
```

---

### IN-03: 测试 `test_no_yaml_load_in_source` 的 inline-comment 剥离不严谨

**File:** `tests/scripts/test_validate_phase62_yamls.py:300-310`
**Issue:**
测试用 `code = line.split("#", 1)[0]` 剥离行内注释后再 grep `yaml.load(`。
但若源码中出现字符串字面量含 `#`(如 `path = "a#b.yaml"`),该剥离会错误截断。
当前 validator 脚本不含此类字符串,所以测试目前 PASS,但测试本身的鲁棒性不足,
未来若加 `"#"-containing` 字符串会漏报。

非阻塞,但属于 test-quality 缺陷。

**Fix:**
用 `ast` 模块解析源码、遍历 AST 找 `Call(func=Attribute(attr='load'))` 节点,
替代字符串 split。或保留当前实现但在 docstring 中明示该限制。

---

### IN-04: `production.transform_notes` 称 "Filtered CJK tag '制作管理'" — 标签过滤发生在 SKILL→YAML,但未声明 schema-driven 根因

**File:** `/home/kai/.hermes/agents/production.agent.yaml:23-24`
**Issue:**
```
Filtered CJK tag ''制作管理'' from source tags (fails schema ^[a-z0-9-]+$ pattern;
concept surfaced in persona + description instead).
```
该过滤是正确的(schema `tags` pattern `^[a-z0-9-]+$` 确实拒绝 CJK),且概念被
surface 到 persona/description 是好实践。但 transform_notes 把 schema 规则
写成 inline 字符串,未引用 `agents-schema.yaml §2.9`(tags 字段的 schema 章节)。
其他 YAML 的 §2.x 引用都指向 04-MIGRATION-PATH.md 的 per-expert 章节,这里是
schema 字段章节 — 引用 namespace 混淆。

非阻塞 — 信息足够,但引用风格不一致。

**Fix:**
明确引用 schema 字段章节:`Filtered CJK tag ''制作管理'' from source tags
(fails agents-schema.yaml §2.9 tags pattern ^[a-z0-9-]+$; concept surfaced in
persona + description instead)`。

---

### IN-05: `scene_builder` transform_notes 同时引用 §2.1(defaults)+ §2.7(cinematographer 吸收上下文),但未明确 scene_builder 自身没有 §2.x 章节

**File:** `/home/kai/.hermes/agents/scene_builder.agent.yaml:22-26`
**Issue:**
```
transform_notes: 'Rule IDs: §2.1 defaults + §2.7 absorption context. CONTEXT.md
  reactivates scene_builder as an independent agent ... §2.7 absorption into
  cinematographer+style_genome documented; standalone transform chosen per CONTEXT.'
```
04-MIGRATION-PATH.md 的 §2.x 是 per-expert 章节(§2.2=hook_retention,
§2.7=cinematographer,...)。`scene_builder` 在该表中没有自己的 §2.x 章节是因为
Phase 17 标记 deprecated-into-cinematographer。CONTEXT.md 的 reactivation 决策
让 scene_builder 重新独立,但 04-MIGRATION-PATH.md 未补 §2.x 章节为 scene_builder
落规则。

`transform_notes` 引用 §2.7 实际是引用 cinematographer 章节中关于吸收 scene_builder
的那段文字 — 这是 indirect citation,未来若 §2.7 章节重排,该引用会断裂。

非阻塞 — 当前可解析,但引用脆弱。

**Fix:**
两条路径任选其一:
1. 在 04-MIGRATION-PATH.md 补一个 §2.x `scene_builder` 章节(类似 §2.19 cross-table
   中可加一行),把规则固化下来。
2. 在 transform_notes 中更精确地引用:`§2.7 cinematographer row (Phase 17
   absorption contract for scene_builder)` — 让引用自带上下文。

---

_Reviewed: 2026-07-08T00:38:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

## Fix Iteration 1 (2026-07-08T00:43:48Z)

Status: `issues_found` → `fixed`. All 4 WARNING findings resolved.
INFO findings deferred to tech_debt per default `/gsd:code-review --fix`
scope. See `62-REVIEW-FIX.md` for per-finding verification details.
