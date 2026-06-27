# Feedback Evolution Loop — Implementation Record

**Created:** 2026-06-27 (session: Kimi feedback-translator + Kai architecture review + implementation)
**Status:** NL feedback path **implemented** (34 tests + E2E pass). Platform API path designed-but-unimplemented.

---

## 1. What was built this session

### Modules (under `plugins/`)

```
plugins/
├── formula_library/
│   ├── __init__.py              # exports lookup_formulas, Formula
│   ├── schema.py                # Formula + PlatformFit Pydantic models
│   ├── lookup.py                # genre/mood/platform → sorted top-k formulas
│   ├── library_writer.py        # apply_suggestion() / reject_suggestion()
│   ├── library/
│   │   └── urban-fantasy-light.json   # 3 seed formulas (contrast/peak/suspense)
│   └── tests/
│       ├── test_formula_library.py    # 12 tests
│       └── test_library_writer.py     # 10 tests
├── feedback_translator/
│   ├── __init__.py              # exports translate_feedback + queue API
│   ├── schema.py                # TuningSuggestion Pydantic model
│   ├── queue.py                 # JSONL 3-file queue (init/append/read/move)
│   ├── translator.py            # NL feedback → LLM → TuningSuggestion
│   └── tests/
│       └── test_feedback_translator.py  # 12 tests
└── e2e_test.py                  # full loop verification (1 test)
```

**Total: 35/35 tests passing.**

### Architecture: two parallel input paths

Kai's original requirement: "根据专家经验，社区反馈，我的点评意见进行迭代进化"

Three input types map to two paths:
- **Expert experience + operator critiques** → natural language → `feedback_translator` (Path B, implemented)
- **Community feedback** (completion rate, engagement, etc.) → numeric metrics → `tuning_loop` (Path A, not yet implemented — needs platform API keys)

Both paths produce `TuningSuggestion` records that flow through the **same JSONL queue** → operator approve → `library_writer.apply_suggestion()` → formula eval_score update.

### eval_score delta logic

Fixed ±0.05 based on Chinese keyword detection in `suggested_action` text:
- **+0.05:** 加强 / 提升 / 增加
- **−0.05:** 减弱 / 降低 / 删除 / 太 (covers "开头太平了")
- Clamped to [0.0, 1.0]

### What was NOT built (designed, deferred)

| Component | Reason for deferral |
|-----------|---------------------|
| `plugins/platform_metrics/` (5 API adapters) | Operator hasn't configured platform API keys |
| `tuning_loop.py` (MetricTrigger rules) | Depends on platform_metrics; Path B covers the immediate need |
| Step 14 platform slicing | Operator said "暂缓" — manual cutting is not a current pain point |
| Step 6.5 LTX2 preview | Operator said "暂缓" — requires GPU runtime not yet configured |
| `hermes formula stats` CLI | Nice-to-have dashboard; Python API works for now |

---

## 2. Key decisions made by operator (2026-06-27)

1. **Step 0 (formula_library):** ✅ Keep — lowest cost, highest immediate value
2. **Step 6.5 (LTX2 preview):** ⏸️ Defer — GPU dependency
3. **Step 14 (platform slicing):** ⏸️ Defer — not a current pain point
4. **Step 15 (data convergence):** Add NL feedback path, defer numeric API path
5. **"不碰平台 API":** Means implement Path B (NL feedback) first; Path A (API metrics) later when keys are configured. Two paths are parallel, non-dependent.

---

## 3. Test infrastructure notes

- **Pydantic object access:** `read_pending()` returns `list[TuningSuggestion]` (Pydantic models). Use `.suggestion_id` not `["suggestion_id"]`.
- **Test path calculation:** Test files at `plugins/<pkg>/tests/test_foo.py` use `parents[2]` to reach `plugins/` for sys.path.
- **Cross-plugin import:** `library_writer.py` (in `formula_library/`) imports `feedback_translator.queue` — resolved via `sys.path.insert(0, <plugins_dir>)` at import time.
- **Seed formula format:** `library/urban-fantasy-light.json` stores formulas as a **JSON array** (not one-file-per-formula). `library_writer` preserves the original layout (single object vs array) on write.

---

## 4. Next steps (when operator is ready)

1. **Wrap as hermes skill** — make `translate_feedback` callable from Telegram (operator types critique → auto-translates → queues)
2. **Platform API path** — when operator configures 5 API keys, implement `plugins/platform_metrics/` adapters
3. **tuning_loop.py** — numeric MetricTrigger rules (4 thresholds from `data-convergence.md` §5)
4. **eval_score parameterization** — ±0.05 is fixed; could become per-trigger configurable
