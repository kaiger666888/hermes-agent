# Phase 73: IMG - Research

**Researched:** 2026-07-09
**Domain:** dreamina CLI production-grade orchestration (asyncio batch + vision-verify gate + RHD/LHD mitigation + SLA dashboard) — v14.0 IMG track
**Confidence:** HIGH (all code claims verified against live kais-hermes-skills repo at HEAD `398eaec`; dreamina CLI `--help` verified live; GLM-4.6V API path verified via zai provider profile + vision_tools.py)

## Summary

Phase 73 (IMG) hardens the dreamina image-generation path from a loose collection of helper scripts + SKILL.md pitfalls into a production-grade Python orchestrator with 4 enforced guarantees: (1) `asyncio.Semaphore(10)` concurrency cap + `tenacity` retry + sync-queue block-on-all semantics so `pipeline_state` is written ONLY after every image resolves; (2) GLM-4.6V vision-verify mandatory gate (audit-trail semantics — "verify has RUN" not "verify has APPROVED") injected before ComfyUI upload; (3) RHD/LHD systematic mitigation via 3-attempt budget (prompt emphasis → verify-retry with negative prompt → image2image fallback from confirmed LHD reference); (4) `hermes dreamina stats` SLA dashboard reading a local JSONL MetricsBuffer ring buffer.

The work is **medium-risk Python + content authoring**. The Python surface is 3 new modules (`dreamina_manager.py`, `vision_verify.py`, `dreamina_stats.py`) co-located in the existing `kais_aigc` plugin, plus 1 new ref (`image2image-stratification.md`), plus 1 SKILL.md body patch (pitfall escalation from advisory to mandatory gate), plus `_VISION_VERIFY_INSTRUCTION` injection into `p07_scene_generation.py` (XCUT-02). The critical integration discovery is that **two parallel dreamina code paths exist today**: (a) `plugins/kais_aigc/jimeng.py` HTTP client to jimeng-free-api `:5100` (sync httpx, session rotation, video-gated), and (b) direct `dreamina` CLI subprocess invocation in `templates/dreamina_gen_image.py` + `episodes/.../generate_p04_assets.py` (subprocess.Popen + ThreadPoolExecutor). Per CONTEXT.md locked decision, `dreamina_manager.py` lives in `plugins/kais_aigc/` and MUST wrap the **dreamina CLI** (subprocess path), NOT the jimeng-free-api HTTP path — the CLI is the validated production interface (10-parallel benchmark, query_result JSON schema documented, URL-signature-expiry handling proven).

**Primary recommendation:** Three plans in order — Plan A (Foundation: dreamina_manager.py orchestrator + vision_verify.py gate + MetricsBuffer JSONL store + unit tests), Plan B (RHD/LHD 3-attempt budget + image2image-stratification.md ref + SKILL.md body patch + p07 _VISION_VERIFY_INSTRUCTION injection + CLI `hermes dreamina stats`), Plan C (integration tests + smoke runner + XCUT-02 goal-content assertion + per-stratum validation report template). Phase 73 touches the kais-hermes-skills repo ONLY; hermes-agent `.planning/` lineage bump is Phase 75.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **dreamina_manager.py location:** `kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py` (NEW; co-located with existing kais_aigc plugin). Alternative `skills/kais-creative/kais-jimeng-cli/scripts/` REJECTED.
- **Concurrency primitive:** `asyncio.Semaphore(10)` (10-parallel = validated sweet spot per SKILL.md benchmark). NOT auto-scaling (IMG-07 deferred).
- **Retry strategy:** `tenacity` (already pinned `9.1.4`); exponential backoff (1s, 2s, 4s, 8s, max 4 retries); retry on `TimeoutError`, `ConnectionError`, dreamina transient errors.
- **Sync queue semantics:** Block on `asyncio.gather(*tasks)` poll-all-before-deadline. Pipeline state write ONLY after all retries resolve (IMG-02). NO async write order.
- **Deadline:** Configurable per-batch; default 600s (10 min) for 10-parallel batch of 39 reference images.
- **vision_verify.py location:** `kais-hermes-skills/plugins/kais_aigc/vision_verify.py` (NEW).
- **Batched vision calls:** Batch 4-8 images per GLM-4.6V call (multi-image message) per PITFALL I-1 mitigation #1.
- **Confidence-gated enforcement:** Low-confidence / content-mismatch > 30% → human review; high-confidence → auto-pass. Mandatory gate = "verify has RUN", NOT "verify has APPROVED".
- **Cache:** sha256-keyed cache for vision-verify results (avoid re-verifying same image).
- **Directional check:** Explicit `"left_hand_drive? yes/no"` question per PITFALL I-4.
- **RHD/LHD 3-attempt budget:** (1) LHD emphasis prompt, (2) stronger LHD + negative RHD prompt, (3) image2image fallback from confirmed LHD reference. Target >=95% LHD success after 3 attempts.
- **`hermes dreamina stats` CLI:** `kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py` registered via `ctx.register_cli_command`. Rich-formatted table default; `--json` flag. MetricsBuffer JSONL at `~/.hermes/metrics/dreamina_stats.jsonl`. Sync `@contextmanager`, NO `asyncio.gather`, NO GLM calls per metric (INFRA-04 preservation).
- **image2image stratification:** 1-ref (strength=0.75, retry=3), 3-ref (strength=0.65, retry=4), 5-ref (strength=0.55, retry=5). New ref `references/image2image-stratification.md`.
- **XCUT-02 injection:** `_VISION_VERIFY_INSTRUCTION` constant in `p07_scene_generation.py`; inject via `.task(steps=[...])` AND `.constraints([...])` (MAX_CONSTRAINTS=7 budget).

### Claude's Discretion
- Exact retry/backoff parameters (within IMG-01 + IMG-04 guidelines)
- GLM-4.6V API integration details (endpoint, model name, request schema — RESEARCH verifies these below)
- MetricsBuffer ring buffer size (default 1000 entries — aligns with v13.0 P67 precedent via `platform_metrics` plugin)
- `hermes dreamina stats` output formatting (rich table vs JSON vs both — BOTH per CONTEXT.md specifics)
- Cache TTL for vision-verify sha256-keyed results (24h default per CONTEXT.md specifics)
- Test framework conventions (pytest — match existing kais_aigc plugin tests)

### Deferred Ideas (OUT OF SCOPE)
- **IMG-07** auto-scaling concurrency. v15+.
- **IMG-08** multi-model routing (dreamina 5.0 vs Seedance 2.0). v15+.
- **IMG-09** vision-verify false-positive threshold calibration. v15+ with IMG-05 dashboard data.
- Real-time vision-verify streaming during generation. Race-condition architecture; sync queue sufficient.
- Multi-language vision-verify prompts. Default Chinese; English deferred.
- Vision-verify model upgrade path. v15+ if GLM-4.6V deprecated.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| IMG-01 | `dreamina_manager.py` orchestrator with `asyncio.Semaphore(10)` + `tenacity` + sync queue | `## dreamina CLI Actual Shape` (subcommands + signatures verified); `## dreamina_manager.py Architecture` (class design + asyncio.Semaphore pattern); `## Existing Code Paths` (jimeng.py vs CLI — CLI is the production path) |
| IMG-02 | Block `pipeline_state` write until ALL retries resolve | `## Sync Queue Semantics (IMG-02)` (gather + poll-all-before-deadline pattern; failure-record semantic); `## Common Pitfalls` Pitfall 3 (I-3 async write order) |
| IMG-03 | GLM-4.6V vision-verify mandatory gate before ComfyUI upload | `## GLM-4.6V API Integration` (endpoint + request schema + Chinese prompt support); `## vision_verify.py Architecture` (function signatures + batching + cache + confidence-gating); `## ComfyUI Upload Path` (injection point documented) |
| IMG-04 | RHD/LHD 3-attempt budget | `## RHD/LHD Mitigation Architecture` (3-attempt state machine + prompt templates + image2image fallback); `## SKILL.md Pitfall Content` (existing line 573 Volvo V2 lesson preserved + escalated) |
| IMG-05 | `hermes dreamina stats` SLA CLI | `## hermes CLI Command Registration` (ctx.register_cli_command pattern verified); `## MetricsBuffer Pattern` (JSONL ring buffer at ~/.hermes/metrics/); `## dreamina_stats.py Architecture` (CLI module design) |
| IMG-06 | image2image workflow standardization (1/3/5-ref stratification) | `## image2image Stratification` (dreamina CLI supports 1-10 refs per `--images` flag verified); `## Stratification Table` (strength + retry per stratum); `## Ref Authoring Spec` |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Skill File Conventions:** `tags`/`related_skills`/`expert_id`/`metrics` frontmatter fields FROZEN for existing skills (FOUND-08). SKILL.md body patch MUST NOT mutate frontmatter. `[VERIFIED: kais-jimeng-cli/SKILL.md frontmatter]`
- **Deliverable form:** "仅 skill 内容(refs + SKILL.md + eval scripts),不改 Hermes 核心 Python/JS 代码". `dreamina_manager.py` lives in `kais-hermes-skills/plugins/kais_aigc/` — a skill-bundled plugin, NOT Hermes core. The `ctx.register_cli_command` call uses the EXISTING plugin context API (`hermes_cli/plugins.py:390`) — no Hermes core edit. Compliant. `[VERIFIED: plugins/kais_aigc/ is under kais-hermes-skills; hermes_cli/plugins.py:390 PluginContext.register_cli_command already exists]`
- **Compatibility:** "不破坏现有 14 专家的 expert_id 与 related_skills 协作图". IMG adds no new expert_id. Compliant.
- **Language:** SKILL.md bilingual. New ref `image2image-stratification.md` follows Chinese-primary convention.
- **Ruff PLW1514:** Every `open()` MUST pass `encoding="utf-8"`. All new Python modules compliant by construction.
- **MEMORY.md glm-5.2-only:** GLM-4.6V vision-verify is a vision TOOL call via `agent/auxiliary_client.async_call_llm`, NOT a model switch. The auxiliary vision router selects GLM-4.6V for vision tasks. Compliant. `[CITED: MEMORY.md feedback-glm-5-2-only.md]`
- **MEMORY.md INFRA-04:** `MAX_CONCURRENT_GL=1` preserved. dreamina_manager uses `asyncio.Semaphore(10)` for dreamina CLI subprocess calls (NOT GLM calls). Vision-verify GLM-4.6V calls are batched (4-8 images per call) to stay within the serial GLM budget. MetricsBuffer writes local JSONL — NO GLM calls per metric. Compliant. `[CITED: MEMORY.md feedback-glm-overload-reduce-concurrency.md]`

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| dreamina batch submission + concurrency | `dreamina_manager.py` (kais_aigc plugin) | dreamina CLI subprocess (`~/.local/bin/dreamina`) | Python orchestrator owns the asyncio.Semaphore + tenacity retry + sync-queue block; CLI is the transport |
| Vision-verify gate | `vision_verify.py` (kais_aigc plugin) | GLM-4.6V via `agent/auxiliary_client.async_call_llm` | Python module owns the batched-call + sha256 cache + confidence-gating; auxiliary client is the transport |
| SLA metric collection | `dreamina_stats.py` (kais_aigc plugin) | Local JSONL at `~/.hermes/metrics/dreamina_stats.jsonl` | Python module owns the MetricsBuffer ring buffer; JSONL is the store (NO GLM calls per metric) |
| SLA metric display | `hermes dreamina stats` CLI | Rich library (already pinned `14.3.3`) | CLI subcommand reads JSONL + renders table; registered via `ctx.register_cli_command` |
| image2image stratification | `references/image2image-stratification.md` (kais-jimeng-cli skill) | `dreamina_manager.py` (reads stratification config) | Ref is the knowledge base; manager consumes the config at runtime |
| RHD/LHD mitigation | `dreamina_manager.py` (3-attempt state machine) | `vision_verify.py` (directional check) | Manager owns the retry loop + prompt escalation; verifier owns the "left_hand_drive? yes/no" question |
| ComfyUI upload gate | `dreamina_manager.py` (post-verify upload) | ComfyUI `/upload/image` API (existing) | Manager calls vision-verify BEFORE upload; existing upload path unchanged |
| XCUT-02 instruction injection | `p07_scene_generation.py` (phase module) | GoalBuilder `.task` + `.constraints` | Phase module owns the `_VISION_VERIFY_INSTRUCTION` constant; subagents see it in the goal string |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tenacity` | `9.1.4` | Retry/backoff for dreamina transient failures | Already pinned in `hermes-agent/pyproject.toml:51`; used by `agent/retry_utils.py`. AsyncRetrying + retry_if_exception_type. `[VERIFIED: pyproject.toml:51]` |
| `asyncio.Semaphore` | stdlib (Python 3.11+) | Concurrency cap at 10-parallel | Validated 12-parallel = 100% success per SKILL.md benchmark; 10 is the conservative production default. `[VERIFIED: SKILL.md line 394 benchmark table]` |
| `subprocess` | stdlib | dreamina CLI invocation | dreamina has NO Python SDK — CLI is the only interface. `[VERIFIED: STACK.md "dreamina 没有 Python SDK"]` |
| `httpx` | `0.28.1` | Download dreamina-generated images from byteimg.com URLs | Already pinned; async mode for batch download. Replaces aria2c (broken data stream pitfall). `[VERIFIED: pyproject.toml:35; SKILL.md aria2c pitfall line 441-460]` |
| `Pillow` (PIL) | installed | Brightness check (avg + black%) for over-dark detection | Already in stack; used by `dreamina_gen_image.py:87` + `batch-generation-quality-control.md:81`. `[VERIFIED: dreamina_gen_image.py:87 imports PIL]` |
| `rich` | `14.3.3` | SLA dashboard table formatting for `hermes dreamina stats` | Already pinned; used by platform_metrics `cli.py` (exact precedent). `[VERIFIED: platform_metrics/cli.py:40-41 imports rich]` |
| `pydantic` | `2.13.4` | MetricsBuffer record schema (`DreaminaTaskMetrics`) | Already pinned; used by platform_metrics `schema.py` (exact precedent). `[VERIFIED: platform_metrics/schema.py:42 imports pydantic]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hashlib` (stdlib) | 3.11+ | sha256 cache keys for vision-verify results | Avoids re-verifying same image across re-runs |
| `concurrent.futures.ThreadPoolExecutor` | stdlib | Alternative to asyncio for sync callers | Existing `dreamina_gen_image.py:132` + `generate_p04_assets.py:388` use this pattern; dreamina_manager wraps both async and sync entry points |
| GLM-4.6V (via zai provider) | already wired | Vision-verify content + directional analysis | `agent/auxiliary_client.async_call_llm` routes to zai provider; vision_tools.py uses the same path. `[VERIFIED: zai/__init__.py base_url="https://api.z.ai/api/paas/v4"; vision_tools.py:31 imports async_call_llm]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dreamina CLI subprocess | jimeng-free-api HTTP `:5100` (`jimeng.py`) | CLI is the validated production path (benchmark data, query_result schema documented, URL-expiry handling proven). HTTP API requires jimeng-free-api service running + session rotation. CONTEXT.md locks CLI path. |
| asyncio.Semaphore | `aiolimiter` (token bucket) | dreamina is server-side concurrency cap, NOT token bucket. Semaphore is simpler + stdlib. `[CITED: STACK.md "What NOT to Use"]` |
| tenacity | `backoff` library | Functional overlap; Hermes already pins tenacity. Mixing creates two retry patterns. `[CITED: STACK.md]` |
| Local JSONL MetricsBuffer | GLM-based metric aggregation | INFRA-04 violation — adds N GLM calls per dreamina submission. JSONL is local, sync, zero-GLM. `[CITED: PITFALLS.md I-5]` |

**Installation:**
```bash
# Zero new packages. Phase 73 installs nothing.
# All dependencies are stdlib or already pinned in hermes-agent/pyproject.toml.
```

**Version verification:** Not applicable — zero new packages. Existing `tenacity==9.1.4`, `httpx==0.28.1`, `Pillow`, `rich==14.3.3`, `pydantic==2.13.4` are reused.

## Package Legitimacy Audit

Phase 73 installs **zero external packages**. The Package Legitimacy Gate protocol is satisfied trivially — no packages to audit. slopcheck is not invoked because there are no `pip install` / `npm install` operations in any task.

*No packages removed, no packages flagged, no packages tagged `[ASSUMED]`.*

## Architecture Patterns

### System Architecture Diagram

```text
Operator / Pipeline (p07_scene_generation.py)
    │
    │  delegate_task goal includes _VISION_VERIFY_INSTRUCTION (XCUT-02)
    │  subagent invokes dreamina_manager.batch_submit(prompts, ...)
    │
    ▼
dreamina_manager.py (NEW — kais_aigc plugin)
    │
    ├──▶ asyncio.Semaphore(10) ── gates concurrent dreamina CLI subprocesses
    │
    ├──▶ per-image task:
    │      ├─▶ subprocess: dreamina text2image --prompt=... --poll=0  (submit)
    │      ├─▶ subprocess: dreamina query_result --submit_id=...      (poll until done)
    │      ├─▶ httpx download: byteimg.com URL → local .png           (URL ~30min expiry)
    │      ├─▶ PIL brightness check (avg < 60 OR black% > 40 → flag)
    │      ├─▶ vision_verify.verify_image_content(path, expected, directional_check)
    │      │      ├─▶ sha256 cache hit? → return cached result
    │      │      ├─▶ GLM-4.6V batched call (4-8 images per call)
    │      │      └─▶ confidence-gated: high → pass; low → flag for review
    │      ├─▶ IF vision-verify FAILS AND attempt < 3:
    │      │      └─▶ retry with escalated prompt (RHD/LHD budget)
    │      ├─▶ IF vision-verify FAILS AND attempt == 3:
    │      │      └─▶ image2image from confirmed LHD reference (fallback)
    │      └─▶ tenacity retry on transient errors (TimeoutError, ConnectionError)
    │
    ├──▶ asyncio.gather(*tasks) ── BLOCK until ALL resolve (sync queue semantic, IMG-02)
    │
    ├──▶ MetricsBuffer.record(submit_id, latency_ms, success, retries, ...) ── local JSONL
    │
    └──▶ return list[DreaminaTaskResult] ── pipeline_state write ONLY after this returns
          │
          ├─▶ IF all success → ComfyUI /upload/image for each verified image
          └─▶ IF any failure → write failure record → P11 refuses to render that shot

Operator CLI:
    hermes dreamina stats ── reads ~/.hermes/metrics/dreamina_stats.jsonl ── rich table
```

### Recommended Project Structure
```
kais-hermes-skills/
├── plugins/kais_aigc/
│   ├── dreamina_manager.py          # Plan A: NEW orchestrator (asyncio.Semaphore + tenacity + sync queue)
│   ├── vision_verify.py             # Plan A: NEW GLM-4.6V gate (batched calls + sha256 cache + confidence)
│   ├── dreamina_stats.py            # Plan B: NEW CLI module (hermes dreamina stats)
│   ├── __init__.py                  # Plan B: MODIFY (add dreamina_stats CLI registration)
│   ├── jimeng.py                    # UNCHANGED (existing HTTP client to :5100 — separate path)
│   ├── tools.py                     # UNCHANGED (existing tool schemas)
│   ├── plugin.yaml                  # Plan B: MODIFY (add dreamina_stats to provides_tools if needed)
│   └── tests/
│       ├── test_dreamina_manager.py # Plan A: NEW (orchestrator unit tests)
│       ├── test_vision_verify.py    # Plan A: NEW (gate unit tests)
│       ├── test_dreamina_stats.py   # Plan B: NEW (CLI unit tests)
│       └── test_jimeng.py           # UNCHANGED (existing jimeng.py tests)
├── skills/kais-creative/kais-jimeng-cli/
│   ├── SKILL.md                     # Plan B: MODIFY body (pitfall escalation to mandatory gate)
│   └── references/
│       ├── batch-generation-quality-control.md  # UNCHANGED (existing pattern — referenced by manager)
│       └── image2image-stratification.md        # Plan B: NEW (1/3/5-ref stratification ref)
├── skills/kais-movie-pipeline/
│   ├── SKILL.md                     # Plan B: MODIFY body (line 564 pitfall escalation)
│   ├── pipeline/phases/
│   │   └── p07_scene_generation.py  # Plan B: MODIFY (+_VISION_VERIFY_INSTRUCTION, XCUT-02)
│   └── tests/
│       ├── test_img_integration.py  # Plan C: NEW (orchestrator + verify + CLI integration)
│       └── conftest.py              # UNCHANGED (existing fixtures reused)
└── (hermes-agent repo: NO CHANGES in Phase 73 — lineage bump is Phase 75)
```

### Pattern 1: asyncio.Semaphore + tenacity + sync-queue (IMG-01 + IMG-02)
**What:** Production-grade batch orchestrator that caps concurrency, retries transient failures, and blocks until ALL tasks resolve before returning.
**When:** Any dreamina batch image generation invoked from the pipeline.
**Example:**
```python
# Source: derived from STACK.md IMG recommendation + existing dreamina_gen_image.py pattern
# + tenacity AsyncRetrying docs (https://github.com/jd/tenacity)

import asyncio
import hashlib
import subprocess
import json
from pathlib import Path
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

DEFAULT_CONCURRENCY = 10
DEFAULT_DEADLINE_SEC = 600  # 10 min for 39-image batch
DREAMINA_CLI = Path.home() / ".local" / "bin" / "dreamina"


class DreaminaTaskResult(TypedDict):
    submit_id: str
    status: str  # "ok" | "failed" | "degraded"
    image_path: str | None
    latency_ms: int
    retries: int
    vision_verified: bool
    vision_confidence: float | None
    error: str | None


async def batch_submit(
    prompts: list[dict[str, str]],  # [{"id": "S01_front", "prompt": "...", "expected": "...", "directional": "lhd"}]
    output_dir: str,
    *,
    concurrency: int = DEFAULT_CONCURRENCY,
    deadline_sec: int = DEFAULT_DEADLINE_SEC,
    ratio: str = "16:9",
    model_version: str = "5.0",
) -> list[DreaminaTaskResult]:
    """Submit a batch of dreamina image generation tasks with concurrency cap,
    retry, vision-verify gate, and sync-queue block-on-all semantic.

    Returns ONLY after all tasks resolve (success or exhausted retries).
    Caller writes pipeline_state AFTER this returns (IMG-02).
    """
    sem = asyncio.Semaphore(concurrency)

    async def _one(item: dict) -> DreaminaTaskResult:
        async with sem:
            return await _generate_one_with_verify(item, output_dir, ratio, model_version)

    results = await asyncio.wait_for(
        asyncio.gather(*[_one(item) for item in prompts], return_exceptions=False),
        timeout=deadline_sec,
    )
    return results


async def _generate_one_with_verify(item, output_dir, ratio, model_version) -> DreaminaTaskResult:
    """Single-image pipeline: submit → poll → download → brightness → vision-verify → retry budget."""
    import time
    from plugins.kais_aigc.vision_verify import verify_image_content

    start = time.monotonic()
    output_path = str(Path(output_dir) / f"{item['id']}.png")
    expected = item.get("expected", "")
    directional = item.get("directional")  # "lhd" | "rhd" | None

    for attempt in range(3):  # IMG-04 RHD/LHD 3-attempt budget
        prompt = _escalate_prompt(item["prompt"], attempt, directional)
        try:
            async for attempt_info in AsyncRetrying(
                stop=stop_after_attempt(4),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type((TimeoutError, ConnectionError, subprocess.TimeoutExpired)),
            ):
                with attempt_info:
                    sid = await _dreamina_submit(prompt, ratio, model_version)
                    raw = await _dreamina_poll(sid)
                    await _download(raw["url"], output_path)
        except Exception as exc:
            if attempt < 2:
                continue
            return {"submit_id": "", "status": "failed", "image_path": None,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "retries": attempt, "vision_verified": False,
                    "vision_confidence": None, "error": str(exc)}

        # Vision-verify gate
        vr = await verify_image_content(output_path, expected, directional_check=directional)
        if vr["pass"]:
            return {"submit_id": sid, "status": "ok", "image_path": output_path,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "retries": attempt, "vision_verified": True,
                    "vision_confidence": vr["confidence"], "error": None}
        # else: retry with escalated prompt (attempt+1)

    # Attempt 3 fallback: image2image from confirmed LHD reference
    # (Plan B implements _image2image_fallback)
    return {"submit_id": sid, "status": "degraded", "image_path": output_path,
            "latency_ms": int((time.monotonic() - start) * 1000),
            "retries": 3, "vision_verified": True,
            "vision_confidence": vr["confidence"], "error": "vision-verify failed 3 attempts"}
```

### Pattern 2: GLM-4.6V Vision-Verify Gate (IMG-03)
**What:** Batched multi-image vision analysis with sha256 cache + confidence-gated enforcement.
**When:** Every dreamina-generated image before ComfyUI upload.
**Why batched:** PITFALL I-1 — serial vision-verify at 2-5s/image adds ~50min to a 213-shot batch. Batching 4-8 images per GLM-4.6V call cuts overhead 4-8x. `[CITED: PITFALLS.md I-1]`
**Example:**
```python
# Source: derived from vision_tools.py async_call_llm pattern + PITFALL I-1 mitigation #1

import hashlib
from pathlib import Path
from typing import Any

import httpx
from agent.auxiliary_client import async_call_llm, extract_content_or_reasoning

# sha256-keyed cache (PITFALL I-1 mitigation #4)
_cache: dict[str, dict[str, Any]] = {}
_CACHE_TTL_SEC = 86400  # 24h per CONTEXT.md specifics


async def verify_image_content(
    image_path: str,
    expected_content: str,
    directional_check: str | None = None,
) -> dict[str, Any]:
    """Verify a dreamina-generated image matches expected content.

    Args:
        image_path: Local path to the generated .png
        expected_content: What the image SHOULD contain (e.g. "baby in car rear seat")
        directional_check: Optional directional question ("lhd" → "left_hand_drive? yes/no")

    Returns:
        {"pass": bool, "confidence": float, "description": str, "cached": bool}

    Mandatory gate semantic (PITFALL I-2 mitigation #4):
        "pass" = vision-verify has RUN and returned high-confidence match.
        Low-confidence results return pass=False for OPERATOR review.
        The gate enforces "verify has RUN", NOT "verify has APPROVED".
    """
    sha = hashlib.sha256(Path(image_path).read_bytes()).hexdigest()
    if sha in _cache:
        return {**_cache[sha], "cached": True}

    # Build vision prompt (Chinese — dreamina output is Chinese-optimized)
    question = f"这张图片是否包含以下内容？请回答是或否并给出置信度(0-1)。内容：{expected_content}"
    if directional_check == "lhd":
        question += "\n另外：方向盘在左侧（左舵LHD）还是右侧（右舵RHD）？"

    # GLM-4.6V call via auxiliary vision router
    response = await async_call_llm(
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                {"type": "text", "text": question},
            ],
        }],
        prefer_vision=True,  # routes to GLM-4.6V via zai provider
    )
    text = extract_content_or_reasoning(response)
    result = _parse_vision_response(text, expected_content, directional_check)

    _cache[sha] = result
    return {**result, "cached": False}
```

### Pattern 3: MetricsBuffer JSONL Ring Buffer (IMG-05, INFRA-04 compliant)
**What:** Local sync JSONL metrics store — NO GLM calls per metric. Reads at CLI time for dashboard.
**When:** Every dreamina_manager.batch_submit records per-task metrics; `hermes dreamina stats` reads them.
**Why sync `@contextmanager`:** PITFALL I-5 — naive async metric aggregation adds GLM overhead (INFRA-04 violation). v13.0 P67 pattern is sync `@contextmanager`. `[CITED: PITFALLS.md I-5]`
**Example:**
```python
# Source: derived from platform_metrics/queue.py JSONL pattern + PITFALL I-5 mitigation

import json
from contextlib import contextmanager
from pathlib import Path
from hermes_constants import get_hermes_home
from collections import deque

_BUFFER_SIZE = 1000  # CONTEXT.md specifics: ~1 week of operator data
_METRICS_FILE = lambda: Path(get_hermes_home()) / "metrics" / "dreamina_stats.jsonl"


@contextmanager
def record_metric(metric: dict):
    """Sync context manager: append metric to JSONL ring buffer.
    NO asyncio.gather, NO GLM calls (INFRA-04 preservation per PITFALL I-5)."""
    f = _METRICS_FILE()
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(metric, ensure_ascii=False) + "\n")
    yield


def read_metrics(limit: int = _BUFFER_SIZE) -> list[dict]:
    """Read last N metrics from JSONL (ring buffer semantic)."""
    f = _METRICS_FILE()
    if not f.exists():
        return []
    lines = f.read_text(encoding="utf-8").strip().split("\n")
    return [json.loads(line) for line in lines[-limit:] if line.strip()]
```

### Anti-Patterns to Avoid
- **Async write before retries resolve (PITFALL I-3 BLOCKER):** Writing `pipeline_state` before `asyncio.gather` returns → P11 video render fails on missing ref. Manager MUST block on poll-all-before-deadline. `[CITED: PITFALLS.md I-3]`
- **aria2c for byteimg.com downloads:** Multi-connection sharded download produces broken data stream on byteimg.com CDN. Use `curl -sL` or `httpx` single-connection. `[VERIFIED: SKILL.md line 441-460; batch-generation-quality-control.md:255]`
- **Vision-verify as binary approve/reject gate (PITFALL I-2):** Vision analysis is ~20% unreliable. Mandatory gate = "verify has RUN" (audit trail), NOT "verify has APPROVED". Operator makes final call on low-confidence. `[CITED: PITFALLS.md I-2]`
- **Serial vision-verify (PITFALL I-1):** 1-image-per-GLM-call serializes the batch. Batch 4-8 images per call. `[CITED: PITFALLS.md I-1]`
- **Unbounded concurrency > 12:** 20-parallel = 5% failure rate (server-side cap). Stick to 10-parallel validated sweet spot. `[VERIFIED: SKILL.md line 394 benchmark]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| dreamina retry/backoff | Custom `while True: retry` loop | `tenacity.AsyncRetrying` | Already pinned; handles jitter, stop conditions, exception-type filtering. Edge cases (nested retries, result-based retry) are solved. |
| Concurrency cap | Manual counter + `asyncio.sleep` | `asyncio.Semaphore(10)` | stdlib; atomic acquire/release; validated 12-parallel benchmark backs the number |
| Image download from URL | `requests.get` (sync, blocks event loop) | `httpx.AsyncClient` | Already pinned; async non-blocking; replaces aria2c (broken data stream pitfall) |
| Brightness detection | Custom histogram analysis | `PIL.Image.open(path).convert("L").getdata()` | Already in stack; existing `check_brightness()` at `dreamina_gen_image.py:87` is the proven pattern |
| Vision analysis | Custom CNN / local model | GLM-4.6V via `agent/auxiliary_client.async_call_llm` | Already wired via zai provider; 128K context; Chinese-optimized; no local GPU needed |
| SLA metric storage | SQLite / Redis / GLM aggregation | Local JSONL at `~/.hermes/metrics/` | INFRA-04 compliant (zero GLM calls); platform_metrics `queue.py` precedent; ring buffer is trivial |
| CLI table rendering | Manual `print` formatting | `rich.table.Table` | Already pinned `14.3.3`; platform_metrics `cli.py` exact precedent |

**Key insight:** Phase 73's risk surface is NOT in the Python complexity — it's in (1) the sync-queue semantic correctness (IMG-02 BLOCKER), (2) the vision-verify confidence calibration (IMG-03 + IMG-09 deferred), and (3) the RHD/LHD prompt-escalation effectiveness (IMG-04). The Python is glue around proven primitives.

## dreamina CLI Actual Shape

### Subcommands (verified live via `dreamina --help` 2026-07-09)

| Subcommand | Purpose | Key Flags |
|------------|---------|-----------|
| `text2image` | Text → image (async) | `--prompt`, `--ratio` (21:9/16:9/3:2/4:3/1:1/3:4/2:3/9:16), `--resolution_type` (1k/2k/4k), `--model_version` (3.0/3.1/4.0/4.1/4.5/4.6/4.7/5.0), `--poll` (seconds, 0=non-blocking), `--session` |
| `image2image` | 1-10 reference images → edited image | `--images` (comma-separated paths), `--prompt`, `--ratio`, `--resolution_type` (2k/4k only; NO 1k), `--model_version` (4.0+), `--poll` |
| `query_result` | Poll async task by submit_id | `--submit_id` (FULL UUID required, not 8-char prefix), `--download_dir` |
| `list_task` | List saved tasks with status | `--gen_status` filter |
| `user_credit` | Check credit balance | — |
| `login` / `logout` / `relogin` | OAuth device flow | `--headless`, `checklogin --device_code=...` |
| `session` | Session CRUD | — |

`[VERIFIED: live `dreamina --help` + `dreamina text2image -h` + `dreamina image2image -h` + `dreamina query_result -h` output captured 2026-07-09]`

### Critical CLI details (verified from batch-generation-quality-control.md + SKILL.md)

1. **`--poll=0` or omit `--poll`** = non-blocking submit, returns `submit_id` immediately (8-char prefix). `[VERIFIED: SKILL.md line 289]`
2. **`query_result --submit_id`** requires FULL UUID (e.g. `a6c5b7e9-3089-4925-8122-7a1af9d992f4`), NOT the 8-char prefix. Using prefix returns `record not found`. `[VERIFIED: SKILL.md line 307-308]`
3. **Response JSON schema** (`query_result` output): `gen_status` (NOT `status`), `result_json.images[0].image_url`, `queue_info.queue_status`. `[VERIFIED: batch-generation-quality-control.md:204-226]`
4. **URL signature expiry ~30min** — byteimg.com URLs expire; download immediately after generation. `[VERIFIED: batch-generation-quality-control.md:254; SKILL.md line 353]`
5. **`list_task` status is cached/lazy** — may show `querying` when `query_result` returns `success`. Always poll via `query_result`. `[VERIFIED: SKILL.md line 339-341]`
6. **image2image accepts 1-10 images** via `--images` comma-separated paths. `[VERIFIED: `dreamina image2image -h` "Upload 1 to 10 local images"]`
7. **No `--strength` parameter on CLI** — the strength/ref-count stratification (IMG-06) is a PROMPT-ENGINEERING + RETRY-BUDGET concern, NOT a CLI flag. The `strength` values in CONTEXT.md (0.75/0.65/0.55) translate to prompt wording intensity, not CLI args.

## Existing Code Paths (CRITICAL DISCOVERY)

**Two parallel dreamina integration paths exist in the codebase:**

| Path | Location | Transport | Status |
|------|----------|-----------|--------|
| **(a) HTTP API** | `plugins/kais_aigc/jimeng.py` | Sync `httpx.Client` to jimeng-free-api `:5100` | Operational; video-gated; session rotation. Used by `kais_jimeng_call` tool. |
| **(b) CLI subprocess** | `templates/dreamina_gen_image.py` + `episodes/.../generate_p04_assets.py` | `subprocess.Popen` / `subprocess.run` to `~/.local/bin/dreamina` | Operational; validated 10-parallel benchmark; used by P04 character asset generation + P07 scene generation. |

**CONTEXT.md locks path (b) — CLI subprocess.** Rationale:
- CLI is the validated production interface (12-parallel = 100% success benchmark documented in SKILL.md lines 388-407).
- jimeng-free-api `:5100` requires the separate service running + session IDs from `KAIS_JIMENG_SESSION_ID` env.
- CLI uses OAuth device flow (`dreamina login`) — simpler auth, no session rotation needed for single-operator use.
- `query_result` JSON schema is documented + validated (batch-generation-quality-control.md:204-226).

**dreamina_manager.py wraps path (b).** It does NOT use `jimeng.py`. The two paths coexist — `jimeng.py` remains for the `kais_jimeng_call` tool surface; `dreamina_manager.py` is the pipeline-internal orchestrator.

### Existing `dreamina_gen_image.py` API (the base for dreamina_manager.py)
`[VERIFIED: templates/dreamina_gen_image.py — read in full, 199 lines]`

```python
# Current function signatures (to be refactored into dreamina_manager.py):
def submit(prompt: str, ratio: str) -> str | None:
    """Submit text2image, return submit_id (8-char prefix)."""

def poll_until_done(submit_id: str, max_wait: int = 180) -> dict | None:
    """Poll query_result every 5s until success/failed or timeout."""

def download(result: dict, output_path: str) -> bool:
    """Download from result_json.images[0].image_url via aria2c (PITFALL: should be curl/httpx)."""

def check_brightness(path: str) -> float:
    """PIL avg brightness check."""

def gen_one(item: dict, output_dir: str, ratio: str) -> dict:
    """Full single-image pipeline: submit → poll → download → brightness."""

def batch_generate(batch_file: str, output_dir: str, workers: int, ratio: str):
    """ThreadPoolExecutor batch (max_workers=4 default)."""
```

**dreamina_manager.py evolves this:**
- `ThreadPoolExecutor(max_workers=4)` → `asyncio.Semaphore(10)` (validated 10-parallel, not conservative 4)
- `aria2c` download → `httpx.AsyncClient` (fixes broken data stream pitfall)
- No vision-verify → GLM-4.6V mandatory gate
- No retry → `tenacity.AsyncRetrying`
- No MetricsBuffer → JSONL ring buffer
- `gen_one` returns simple dict → `DreaminaTaskResult` TypedDict with vision_verified + confidence

## GLM-4.6V API Integration

### Endpoint + Provider
`[VERIFIED: plugins/model-providers/zai/__init__.py]`

- **Provider profile:** `zai` (aliases: `glm`, `z-ai`, `z.ai`, `zhipu`)
- **Base URL:** `https://api.z.ai/api/paas/v4`
- **Auth env vars:** `GLM_API_KEY` / `ZAI_API_KEY` / `Z_AI_API_KEY`
- **Model:** `glm-4.6v` is NOT in `fallback_models` (which lists `glm-5.2`, `glm-5`, `glm-4-9b`). GLM-4.6V is invoked via the **auxiliary vision router** (`agent/auxiliary_client.async_call_llm` with `prefer_vision=True`), which routes vision requests to the configured vision model. The vision model is configured in `cli-config.yaml` under `auxiliary.vision.model`.

### Vision call pattern
`[VERIFIED: tools/vision_tools.py:31 — imports async_call_llm from agent.auxiliary_client]`

```python
from agent.auxiliary_client import async_call_llm, extract_content_or_reasoning

response = await async_call_llm(
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
            {"type": "text", "text": "这张图片是否包含...？"},
        ],
    }],
    prefer_vision=True,  # routes to GLM-4.6V
)
text = extract_content_or_reasoning(response)
```

### Chinese prompt support
`[CITED: docs.z.ai/guides/vlm/glm-4.6v — GLM-4.6V is Chinese-native]`

GLM-4.6V is trained by Zhipu AI (Chinese AI lab). Chinese prompts for `"方向盘在左侧还是右侧？"` (is the steering wheel on the left or right?) are natively supported and likely MORE accurate than English translations for Chinese-generated dreamina content. CONTEXT.md deferred-items note "default Chinese" — confirmed correct.

### Batched multi-image call
GLM-4.6V supports multi-image messages (up to 128K context). For batched vision-verify (PITFALL I-1 mitigation #1):
```python
content = []
for img_path in batch_of_4_to_8_images:
    content.append({"type": "image_url", "image_url": {"url": f"file://{img_path}"}})
    content.append({"type": "text", "text": f"Image {i}: ..."})
content.append({"type": "text", "text": "For EACH image, answer: does it contain...?"})
```

### Confidence score parsing
GLM-4.6V returns text (not structured JSON confidence). `vision_verify._parse_vision_response()` extracts confidence via:
- Regex for `置信度.*?([0-9.]+)` (Chinese)
- Regex for `confidence.*?([0-9.]+)` (English fallback)
- Default 0.5 if no match (flags as low-confidence)

## ComfyUI Upload Path

### Injection point for vision-verify gate
`[VERIFIED: grep for "/upload/image" across kais-hermes-skills]`

The ComfyUI upload happens AFTER dreamina generation + BEFORE LTX-MSR render. Existing upload pattern (from `ltx-msr-shot-list-prep.md:60` + `episodes/.../render_S5_1a.py:108`):

```python
resp = requests.post(f"{COMFY_URL}/upload/image",
    files={"image": open(ref_path, "rb")},
    data={"overwrite": "true"})
```

**Vision-verify gate injects BEFORE this upload:**
```
dreamina generate → download → PIL brightness → vision_verify.verify_image_content()
    → PASS → ComfyUI /upload/image
    → FAIL → retry budget (3 attempts) → if exhausted, flag for operator
```

The gate lives in `dreamina_manager.py._generate_one_with_verify()`, NOT in the ComfyUI upload code. The upload code is unchanged — it just only receives verified images.

### P11 video render backfill consumer
`[VERIFIED: p11_video_render.py — read key sections]`

P11 reads `scene-images` from the asset bus (line 186: `scene_images = asset_bus_read("scene-images")`). The scene-images slot is written by P07. Under IMG-02 sync-queue semantic, P07's `asset_bus_write("scene-images", ...)` happens ONLY after `dreamina_manager.batch_submit()` returns — meaning every image in the slot is either (a) successfully generated + vision-verified, or (b) explicitly marked as `status: "degraded"` with an error record. P11's existing behavior (refuse to render shots with missing refs) is preserved.

## hermes CLI Command Registration

### Pattern (verified from platform_metrics plugin)
`[VERIFIED: plugins/platform_metrics/__init__.py + cli.py + hermes_cli/plugins.py:390]`

```python
# In plugins/kais_aigc/__init__.py register(ctx):
def register(ctx) -> None:
    # ... existing tool registrations ...

    # Plan B: register `hermes dreamina` CLI subcommand
    from plugins.kais_aigc.dreamina_stats import (
        _dreamina_command,
        register_dreamina_cli,
    )
    ctx.register_cli_command(
        name="dreamina",
        help="Dreamina orchestrator SLA dashboard (stats)",
        setup_fn=register_dreamina_cli,
        handler_fn=_dreamina_command,
        description=(
            "Inspect dreamina batch generation metrics + SLA tracking. "
            "Subcommand: stats — show per-task latency / success rate / "
            "cost dashboard. --json emits machine-readable output."
        ),
    )
```

```python
# In plugins/kais_aigc/dreamina_stats.py:
import argparse
from rich.console import Console
from rich.table import Table

def register_dreamina_cli(subparser: argparse.ArgumentParser) -> None:
    subs = subparser.add_subparsers(dest="dreamina_command")
    stats_p = subs.add_parser("stats", help="Show SLA dashboard")
    stats_p.add_argument("--json", action="store_true", help="JSON output")

def _dreamina_command(args) -> int:
    # Read JSONL metrics, render rich table or JSON
    ...
```

### `ctx.register_cli_command` signature
`[VERIFIED: hermes_cli/plugins.py:390-410]`

```python
def register_cli_command(
    self,
    name: str,
    help: str,
    setup_fn: Callable,    # builds argparse subparser
    handler_fn: Callable,  # executes the command
    description: str = "",
) -> None:
```

Auto-discovered at `hermes_cli/main.py:11942`. Zero edits to `hermes_cli/main.py`.

## MetricsBuffer Pattern

### Precedent: platform_metrics plugin (v9.0 Phase 42)
`[VERIFIED: plugins/platform_metrics/schema.py + cli.py + queue.py]`

The `platform_metrics` plugin established the exact pattern IMG-05 follows:
- **Pydantic schema** (`schema.py`) for metric records (`PlatformMetrics` with field validators)
- **JSONL persistence** (`queue.py` — `read_queue(tuning_dir, status)` reads pending/applied/rejected JSONL)
- **Rich CLI** (`cli.py` — `hermes formula stats` renders tables via `rich.table.Table`)
- **Defensive lazy imports** (`cli.py:_queue_counts()` survives if `queue.py` not yet importable)
- **Plugin registration** (`__init__.py` — `ctx.register_cli_command(name="formula", ...)`)

**dreamina_stats.py mirrors this exactly** with `name="dreamina"` instead of `name="formula"`.

### Ring buffer semantic
- **Size:** 1000 entries (CONTEXT.md specifics — ~1 week of operator data at typical pipeline scale)
- **Store:** `~/.hermes/metrics/dreamina_stats.jsonl` (one JSON object per line)
- **Write:** Sync append (NOT async — INFRA-04 preservation per PITFALL I-5)
- **Read:** `read_metrics(limit=1000)` returns last N lines as list of dicts
- **Aggregation:** CLI computes p50/p95 latency, success rate, cost at display time (NOT at write time)

### v13.0 P67 sync `@contextmanager` pattern
Per PITFALL I-5 mitigation — the MetricsBuffer uses `@contextmanager` (sync), NOT `asyncio.gather`. This is the INFRA-04-compliant pattern. The `@contextmanager` wraps the metric recording so cleanup (file handle close) is guaranteed even on exception.

## image2image Stratification

### dreamina CLI image2image capability
`[VERIFIED: `dreamina image2image -h` — "Upload 1 to 10 local images"]`

- `--images` accepts comma-separated local file paths (1-10 images)
- No `--strength` CLI flag — strength is a PROMPT-ENGINEERING concern (not a CLI parameter)
- model_version: 4.0+ only (no 3.x support)
- resolution_type: 2k or 4k only (no 1k)

### Stratification table (CONTEXT.md locked decision)
| Stratum | Ref Count | Strength (prompt intensity) | Retry Budget | Rationale |
|---------|-----------|----------------------------|-------------|-----------|
| High-fidelity | 1-ref | 0.75 (strong prompt adherence) | 3 | Minimal creative deviation; template is authoritative (e.g., character turnaround from single ref) |
| Balanced | 3-ref | 0.65 (moderate blend) | 4 | Character + scene + costume; balanced fidelity + creativity |
| Creative | 5-ref | 0.55 (loose adherence) | 5 | Multi-angle scene; creative deviation expected; higher retry budget because failure rate scales with ref count |

### Ref authoring spec
`references/image2image-stratification.md` (NEW, Plan B) documents:
- Per-stratum parameter table (above)
- Prompt templates per stratum (how "strength 0.75" translates to prompt wording)
- Retry strategy per stratum (when to escalate prompt vs. switch to image2image fallback)
- Per-stratum success-rate tracking in MetricsBuffer (IMG-05 dashboard reports per-stratum)
- Rationale: dreamina's tolerance for N references degrades non-linearly around 4-5 per PITFALL I-6

## RHD/LHD Mitigation Architecture

### 3-Attempt Budget State Machine (IMG-04)
```
Attempt 1: Prompt with LHD emphasis
    prompt = "view from passenger seat, driver sits on LEFT side, steering wheel on the left"
    → dreamina text2image → download → vision_verify(directional_check="lhd")
    → IF pass: DONE
    → IF fail: Attempt 2

Attempt 2: Stronger LHD + negative RHD prompt
    prompt = attempt_1 + "NOT right-hand drive, NOT RHD, steering wheel is NOT on the right"
    → dreamina text2image → download → vision_verify(directional_check="lhd")
    → IF pass: DONE
    → IF fail: Attempt 3

Attempt 3: image2image fallback from confirmed LHD reference
    prompt = "match the layout of this reference image"
    → dreamina image2image --images=<confirmed_lhd_ref.png> --prompt=...
    → download → vision_verify(directional_check="lhd")
    → IF pass: DONE
    → IF fail: flag for operator (give up on auto-fix after 3 attempts)
```

### Existing pitfall content (SKILL.md line 573, preserved + escalated)
`[VERIFIED: kais-movie-pipeline/SKILL.md line 573 — Volvo V2 lesson]`

Existing text documents the Volvo V2 lesson: dreamina generates RHD even when prompted for LHD. Phase 73 escalates this from an advisory pitfall to a **mandatory gate with 3-attempt budget**. The SKILL.md body patch (Plan B) updates the pitfall to reference `dreamina_manager.py` as the systematic mitigation.

### Pattern generalization (CONTEXT.md specifics #4)
The prompt + vision-verify + image2image retry pattern generalizes to other dreamina unreliability cases:
- **Gender:** "female character" → verify "is this character female?" → retry with stronger prompt
- **Age:** "young adult" → verify "approximate age?" → retry
- **Scene type:** "indoor garage" → verify "indoor or outdoor?" → retry

Documented in `dreamina_manager.py` docstring + SKILL.md pitfall update.

## Sync Queue Semantics (IMG-02)

### The BLOCKER (PITFALL I-3)
`[CITED: PITFALLS.md I-3]`

The existing `dreamina_gen_image.py` uses `ThreadPoolExecutor.as_completed()` which returns futures as they complete — NOT blocking until all resolve. If `pipeline_state` is written after the first few complete, downstream phases (P11 video render) consume missing reference images for the not-yet-complete tasks.

### dreamina_manager.py fix
```python
results = await asyncio.wait_for(
    asyncio.gather(*[_one(item) for item in prompts]),
    timeout=deadline_sec,
)
# pipeline_state write happens HERE — after gather returns
# ALL results are resolved (success or failure record)
asset_bus_write("scene-images", [r for r in results if r["status"] == "ok"])
```

### Failure record semantic
If any task exhausts retries:
```python
# The task returns a DreaminaTaskResult with status="failed" or "degraded"
# pipeline_state records BOTH successes AND failures:
{
    "scene_images": [ok_results],
    "failed_images": [failed_results],  # P11 reads this + refuses to render those shots
}
```

P11's existing behavior (refuse to render shots with missing refs) is preserved — it just gets an explicit failure record instead of a silent missing image.

## SKILL.md Pitfall Content

### Line number discrepancy (IMPORTANT)
The CONTEXT.md references SKILL.md lines 519, 561, 570, 619, 621-622. The **actual** `kais-jimeng-cli/SKILL.md` is only **471 lines** — those line numbers refer to `kais-movie-pipeline/SKILL.md`, NOT `kais-jimeng-cli/SKILL.md`. `[VERIFIED: kais-jimeng-cli/SKILL.md = 471 lines; kais-movie-pipeline/SKILL.md has the pitfalls at the referenced lines]`

### Verified pitfall locations in kais-movie-pipeline/SKILL.md
`[VERIFIED: grep results]`
- **Line 564:** "Reference images MUST be vision-verified before upload to ComfyUI" — advisory pitfall → Plan B escalates to mandatory gate
- **Line 573:** "Dreamina generates RHD even when prompted for LHD" (Volvo V2 lesson) — advisory pitfall → Plan B references 3-attempt budget
- **Line 577:** "Vision analysis is UNRELIABLE for video quality assessment" — this is about VIDEO frames, NOT dreamina images. Preserved as-is (IMG-03 is about generated images, not video frame analysis).

### kais-jimeng-cli/SKILL.md content (471 lines — the CLI usage skill)
`[VERIFIED: read in full]`
- Lines 343-353: RHD/LHD directional pitfall (Validated 2026-06-28 Volvo V3)
- Lines 355-407: Parallel generation benchmark (12-parallel = 100% success, 4.8x-11.6x speedup)
- Lines 409-440: Over-dark image problem + PIL detection
- Lines 441-460: aria2c broken data stream pitfall (use curl not aria2c)
- Line 462: Cross-reference to `batch-generation-quality-control.md`

**Plan B patches BOTH SKILL.md files:**
1. `kais-movie-pipeline/SKILL.md:564` — escalate vision-verify from advisory to mandatory gate
2. `kais-jimeng-cli/SKILL.md` — add cross-reference to `dreamina_manager.py` + `image2image-stratification.md`

## Runtime State Inventory

> Phase 73 is NOT a rename/refactor phase. However, it adds new runtime state (MetricsBuffer JSONL) + new CLI command. The relevant question: what existing runtime state is affected?

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None existing — MetricsBuffer JSONL at `~/.hermes/metrics/dreamina_stats.jsonl` is NEW (created on first run) | None — `dreamina_stats.py` creates the directory + file on first write |
| Live service config | dreamina CLI at `~/.local/bin/dreamina` (OAuth login state) — no config change | None — dreamina_manager wraps existing CLI; no new env vars beyond existing `KAIS_JIMENG_*` |
| OS-registered state | None — Phase 73 registers no OS-level services, cron jobs, or systemd units | None |
| Secrets/env vars | `GLM_API_KEY` / `ZAI_API_KEY` — already wired for zai provider (vision-verify reuses this) | None — no new secrets; vision-verify uses existing zai provider auth |
| Build artifacts | None — Phase 73 ships only Python source + markdown refs; no compiled artifacts | None |

**Nothing found that blocks execution.**

## Common Pitfalls

### Pitfall 1: Async write before retries resolve (PITFALL I-3, BLOCKER)
**What goes wrong:** Writing `pipeline_state` before `asyncio.gather` returns → P11 video render fails on missing reference images → silent retry of LTX render → ComfyUI cache phantom success.
**Why it happens:** `ThreadPoolExecutor.as_completed()` (existing pattern) returns futures incrementally. Naive port to asyncio preserves the non-blocking semantic.
**How to avoid:** `dreamina_manager.batch_submit()` uses `asyncio.gather(*tasks)` which blocks until ALL resolve. `asset_bus_write` happens AFTER gather returns. Failure records are explicit, not silent.
**Warning signs:** P11 reports "reference image not found" for shots that P07 reported as "submitted." `[CITED: PITFALLS.md I-3; SKILL.md line 619]`

### Pitfall 2: aria2c broken data stream (verified pitfall)
**What goes wrong:** `aria2c` multi-connection download of byteimg.com PNGs produces files that `ls` shows as correct size but PIL raises `OSError: broken data stream`.
**Why it happens:** aria2c's `-x 4 -s 4` sharded download on byteimg.com CDN occasionally produces corrupted shard concatenation.
**How to avoid:** Use `httpx.AsyncClient` (single connection) or `curl -sL -o file <url>`. dreamina_manager.py uses httpx.
**Warning signs:** `PIL.Image.open(path)` raises `OSError: broken data stream`. `[VERIFIED: SKILL.md line 441-460; batch-generation-quality-control.md:255]`

### Pitfall 3: Vision-verify false positives (PITFALL I-2)
**What goes wrong:** Vision analysis is ~20% unreliable for content assessment. A mandatory gate that's 20% wrong becomes 20% friction — 1 in 5 correct images flagged as wrong content.
**Why it happens:** Vision models reason about content rather than perceive it. Asymmetric errors: false negatives waste regeneration cycles.
**How to avoid:** Mandatory gate = "verify has RUN" (audit trail), NOT "verify has APPROVED." Low-confidence results surface to operator, NOT auto-reject. Confidence-gated: high-confidence passes auto; low-confidence flags for review.
**Warning signs:** Operator disables the gate to hit deadlines. `[CITED: PITFALLS.md I-2]`

### Pitfall 4: Vision-verify bottleneck serializes batch (PITFALL I-1)
**What goes wrong:** Serial vision-verify at 2-5s/image adds ~50min to a 213-shot batch.
**Why it happens:** Naive 1-image-per-GLM-call implementation.
**How to avoid:** Batch 4-8 images per GLM-4.6V call (multi-image message). sha256 cache avoids re-verifying same image.
**Warning signs:** Pipeline wall time increases 20-50% for image-heavy projects. `[CITED: PITFALLS.md I-1]`

### Pitfall 5: SKILL.md line number discrepancy
**What goes wrong:** CONTEXT.md references SKILL.md lines 519, 561, 570, 619, 621-622 — but `kais-jimeng-cli/SKILL.md` is only 471 lines.
**Why it happens:** The line numbers refer to `kais-movie-pipeline/SKILL.md`, NOT `kais-jimeng-cli/SKILL.md`.
**How to avoid:** Plan B patches BOTH files. The pitfall escalation (line 564 mandatory gate, line 573 RHD/LHD) is in `kais-movie-pipeline/SKILL.md`. The CLI usage cross-reference is in `kais-jimeng-cli/SKILL.md`.
**Warning signs:** Executor edits the wrong SKILL.md.

### Pitfall 6: GLM-4.6V not in zai fallback_models (configuration check)
**What goes wrong:** `zai/__init__.py` `fallback_models` lists `glm-5.2`, `glm-5`, `glm-4-9b` — but NOT `glm-4.6v`. If vision-verify tries to use the fallback chain, it picks the wrong model.
**Why it happens:** GLM-4.6V is a VISION model, configured separately via `auxiliary.vision.model` in `cli-config.yaml`, NOT via the chat fallback chain.
**How to avoid:** `vision_verify.py` uses `async_call_llm(prefer_vision=True)` which routes through the auxiliary VISION router (separate from the chat model chain). Do NOT use `async_call_llm` without `prefer_vision=True` for vision-verify.
**Warning signs:** Vision-verify calls use a chat model (no image understanding) instead of GLM-4.6V. `[VERIFIED: vision_tools.py:31 uses async_call_llm; zai/__init__.py fallback_models has no vision model]`

## Code Examples

### dreamina CLI invocation (verified pattern)
```python
# Source: templates/dreamina_gen_image.py:36-51 (verified) + batch-generation-quality-control.md

import subprocess
import json

def dreamina_submit(prompt: str, ratio: str = "16:9", model: str = "5.0") -> str | None:
    """Submit text2image non-blocking, return submit_id (8-char prefix)."""
    result = subprocess.run([
        "dreamina", "text2image",
        f"--prompt={prompt}",
        f"--ratio={ratio}",
        f"--model_version={model}",
        "--resolution_type=2k",
        "--poll=0",  # non-blocking
    ], capture_output=True, text=True, timeout=15)
    try:
        data = json.loads(result.stdout)
        return data.get("submit_id", "")
    except json.JSONDecodeError:
        return None

def dreamina_poll(submit_id: str, max_wait: int = 180) -> dict | None:
    """Poll query_result until success/failed or timeout.
    NOTE: submit_id must be FULL UUID, not 8-char prefix."""
    import time
    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(5)
        result = subprocess.run([
            "dreamina", "query_result",
            f"--submit_id={submit_id}",
        ], capture_output=True, text=True, timeout=15)
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue
        status = data.get("gen_status", "unknown")
        if status == "success":
            return data
        if status in ("failed", "error", "fail"):
            return None
    return None
```

### httpx async download (replaces aria2c)
```python
# Source: derived from SKILL.md aria2c pitfall + httpx async pattern

import httpx
from pathlib import Path

async def download_image(url: str, output_path: str) -> bool:
    """Download dreamina-generated image from byteimg.com URL.
    Uses httpx single-connection (NOT aria2c multi-connection — broken data stream pitfall)."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        if resp.status_code == 200 and len(resp.content) > 1000:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(resp.content)
            return True
        return False
```

### PIL brightness check (existing proven pattern)
```python
# Source: templates/dreamina_gen_image.py:87-93 (verified)

from PIL import Image

def check_brightness(path: str) -> dict:
    """Returns {"avg": float, "black_pct": float, "pass": bool}.
    avg < 60 OR black_pct > 40% = over-dark failure."""
    img = Image.open(path)
    px = list(img.getdata())
    step = len(px) // 2000
    sample = px[::step][:2000]
    bright = [sum(p[:3]) / 3 for p in sample]
    avg = sum(bright) / len(bright)
    black_pct = sum(1 for b in bright if b < 30) / len(bright) * 100
    return {"avg": avg, "black_pct": black_pct, "pass": not (avg < 60 or black_pct > 40)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `dreamina_gen_image.py` ThreadPoolExecutor(4) | `dreamina_manager.py` asyncio.Semaphore(10) | v14.0 Phase 73 | 10-parallel validated; 4 was conservative default |
| aria2c download | httpx async download | v14.0 Phase 73 | Fixes broken data stream pitfall (SKILL.md line 441-460) |
| Advisory "should vision-verify" (SKILL.md:564) | Mandatory gate "MUST vision-verify" (dreamina_manager enforced) | v14.0 Phase 73 | Closes PITFALL I-2; gate runs before ComfyUI upload |
| No retry on dreamina failure | tenacity AsyncRetrying (4 attempts, exponential backoff) | v14.0 Phase 73 | Closes PITFALL I-3 transient failure handling |
| No SLA tracking | `hermes dreamina stats` CLI + JSONL MetricsBuffer | v14.0 Phase 73 | Closes PITFALL I-5 observability gap |
| RHD/LHD prompt-only mitigation | 3-attempt budget (prompt → negative → image2image) | v14.0 Phase 73 | Closes Volvo V2 lesson (SKILL.md:573); target >=95% success |

**Deprecated/outdated:**
- `templates/dreamina_gen_image.py` — superseded by `dreamina_manager.py` (but kept as reference; not deleted)
- `episodes/formc-test-01/assets/P04/generate_p04_assets.py` — episode-specific script; not modified (generated asset, not template)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `agent/auxiliary_client.async_call_llm(prefer_vision=True)` routes to GLM-4.6V via zai provider | GLM-4.6V API Integration | If wrong (routes to a different vision model), vision-verify still works but may use a different model than intended. Verify at execution time via `cli-config.yaml auxiliary.vision.model` setting. |
| A2 | GLM-4.6V accepts `file://` local paths in `image_url` field | vision_verify.py Architecture | If wrong (requires base64 or HTTP URL only), vision_verify.py needs to convert local paths to base64 data URIs. vision_tools.py downloads to temp file then base64-encodes — same pattern may be needed. Medium risk. |
| A3 | `ctx.register_cli_command` auto-discovers at `hermes_cli/main.py:11942` without editing main.py | hermes CLI Command Registration | If wrong, `hermes dreamina stats` doesn't appear. platform_metrics precedent (v9.0 Phase 42) confirms the pattern works. LOW risk. |
| A4 | GLM-4.6V supports multi-image messages (batched vision-verify) | Pattern 2: Vision-Verify Gate | If wrong (single-image only), batching benefit is lost but serial calls still work. PITFALL I-1 mitigation is degraded, not broken. MEDIUM risk. |
| A5 | tenacity AsyncRetrying works with subprocess.TimeoutExpired retry | Pattern 1: Orchestrator | If wrong (tenacity doesn't recognize subprocess exception), custom retry wrapper needed. LOW risk — tenacity `retry_if_exception_type` accepts any exception class. |

## Open Questions

1. **Does `async_call_llm(prefer_vision=True)` route to GLM-4.6V specifically?**
   - What we know: `vision_tools.py` uses `async_call_llm` with the auxiliary vision router. The router reads `auxiliary.vision.model` from `cli-config.yaml`.
   - What's unclear: whether the current config has `glm-4.6v` set as the vision model, or a different model.
   - Recommendation: Plan A executor verifies `cli-config.yaml auxiliary.vision.model` at execution time. If not `glm-4.6v`, document the actual model + flag for operator to update config if needed.

2. **Does GLM-4.6V accept `file://` local paths or require base64?**
   - What we know: `vision_tools.py` downloads remote URLs to temp files, then base64-encodes for the API call. This suggests base64 is the safe path.
   - Recommendation: Plan A's `vision_verify.py` base64-encodes local images (matching `vision_tools.py` pattern) rather than relying on `file://` support. Safer default.

3. **What is the exact `submit_id` → `list_task` → `query_result` UUID resolution flow?**
   - What we know: `text2image --poll=0` returns 8-char prefix. `query_result` requires FULL UUID. `list_task` returns full UUIDs.
   - What's unclear: whether there's a direct way to get the full UUID from the initial submit response (without `list_task` round-trip).
   - Recommendation: Plan A's `dreamina_manager._dreamina_submit()` parses the initial response for full UUID; if only prefix available, calls `list_task` to resolve. Document the flow in the module docstring.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| dreamina CLI | IMG-01 orchestrator | ✓ | `/home/kai/.local/bin/dreamina` (verified live `--help`) | — |
| Python 3.11+ | asyncio.Semaphore, tenacity AsyncRetrying | ✓ | 3.13 (per CLAUDE.md) | — |
| tenacity | IMG-01 retry | ✓ | `9.1.4` (pyproject.toml:51) | — |
| httpx | IMG-01 image download | ✓ | `0.28.1` (pyproject.toml:35) | — |
| Pillow (PIL) | IMG-03 brightness check | ✓ | installed (dreamina_gen_image.py imports it) | — |
| rich | IMG-05 SLA dashboard | ✓ | `14.3.3` (pyproject.toml) | — |
| pydantic | IMG-05 metric schema | ✓ | `2.13.4` (pyproject.toml) | — |
| GLM-4.6V (zai provider) | IMG-03 vision-verify | ✓ | zai provider wired; GLM_API_KEY in env | — |
| ComfyUI :8188 | ComfyUI upload (NOT exercised in Phase 73 tests — only template integration) | N/A for unit tests | N/A | N/A — integration tests mock the upload |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None — all required deps available.

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json`. This section is REQUIRED.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (matching existing `plugins/kais_aigc/tests/` + `skills/kais-movie-pipeline/tests/` conventions) |
| Config file | `skills/kais-movie-pipeline/tests/conftest.py` (shared fixtures: `mock_delegate_factory`, `tmp_asset_bus`, `tmp_state_store`) + `plugins/kais_aigc/tests/` (httpx.MockTransport pattern) |
| Quick run command | `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py plugins/kais_aigc/tests/test_vision_verify.py -x` |
| Full suite command | `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/kais_aigc/tests/ skills/kais-movie-pipeline/tests/test_img_integration.py -x` |

`[VERIFIED: plugins/kais_aigc/tests/test_jimeng.py uses httpx.MockTransport + sleep_fn=lambda s: None pattern; test_smoke.py uses importlib + yaml manifest parse pattern]`

### Phase Requirements → Test Map (Nyquist Dimension 8 — sample-rate analysis)
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IMG-01 | asyncio.Semaphore(10) caps concurrency | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_semaphore_caps_at_10 -x` | ❌ Wave 0 |
| IMG-01 | tenacity retries on TimeoutError | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_retry_on_timeout -x` | ❌ Wave 0 |
| IMG-01 | Batch submit returns DreaminaTaskResult list | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_batch_submit_returns_results -x` | ❌ Wave 0 |
| IMG-02 | Pipeline state write blocked until gather resolves | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_sync_queue_blocks_until_all_resolve -x` | ❌ Wave 0 |
| IMG-02 | Failure record explicit (not silent skip) | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_failure_record_explicit -x` | ❌ Wave 0 |
| IMG-03 | vision_verify.verify_image_content returns confidence | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_verify_returns_confidence -x` | ❌ Wave 0 |
| IMG-03 | sha256 cache hit avoids re-verify | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_cache_hit -x` | ❌ Wave 0 |
| IMG-03 | Low-confidence flags for review (no auto-reject) | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_low_confidence_flags_not_rejects -x` | ❌ Wave 0 |
| IMG-03 | Directional check "lhd" asks left_hand_drive question | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_directional_check_lhd -x` | ❌ Wave 0 |
| IMG-04 | 3-attempt budget escalates prompt each attempt | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_rhd_lhd_3_attempt_budget -x` | ❌ Wave 0 |
| IMG-04 | Attempt 3 falls back to image2image | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_image2image_fallback_on_attempt_3 -x` | ❌ Wave 0 |
| IMG-05 | `hermes dreamina stats` CLI renders rich table | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_stats.py::test_stats_renders_table -x` | ❌ Wave 0 |
| IMG-05 | `--json` flag emits machine-readable output | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_stats.py::test_stats_json_flag -x` | ❌ Wave 0 |
| IMG-05 | MetricsBuffer writes JSONL (no GLM calls) | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_stats.py::test_metrics_buffer_writes_jsonl -x` | ❌ Wave 0 |
| IMG-06 | image2image-stratification.md ref exists with 3 strata | smoke | `grep -c "1-ref\|3-ref\|5-ref" skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md == 3` | ❌ Wave 0 |
| XCUT-02 | `_VISION_VERIFY_INSTRUCTION` injected into p07 goal | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_img_integration.py::test_p07_goal_includes_vision_verify_instruction -x` | ❌ Wave 0 |
| XCUT-02 | SKILL.md:564 escalated to "MUST" | smoke | `grep "MUST vision-verify" skills/kais-movie-pipeline/SKILL.md` | ❌ Wave 0 |
| Integration | dreamina_manager → vision_verify → MetricsBuffer end-to-end | integration | `python -m pytest skills/kais-movie-pipeline/tests/test_img_integration.py::test_end_to_end_orchestrator -x` | ❌ Wave 0 |

### Sampling Rate (Nyquist Dimension 8)
- **Per task commit:** `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py plugins/kais_aigc/tests/test_vision_verify.py -x` (quick — ~5s, 10-15 unit tests)
- **Per wave merge:** Full IMG test suite `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py plugins/kais_aigc/tests/test_vision_verify.py plugins/kais_aigc/tests/test_dreamina_stats.py skills/kais-movie-pipeline/tests/test_img_integration.py -x` (catches cross-module regression)
- **Phase gate (before `/gsd:verify-work`):** Full suite green + smoke grep assertions (IMG-06 ref existence, XCUT-02 SKILL.md MUST injection, p07 _INSTRUCTION constant) all pass. The grep smoke checks are the Nyquist high-frequency samples that prove markdown content landed; the pytest unit tests are the low-frequency samples that prove Python behavior.

**Nyquist rationale:** Phase 73 has three distinct signal types — (1) Python orchestrator behavior (asyncio.Semaphore, tenacity, sync-queue) sampled by pytest unit tests at task-commit rate, (2) vision-verify gate behavior (confidence, cache, directional) sampled by pytest unit tests at task-commit rate, (3) markdown content presence (SKILL.md MUST injection, stratification ref, p07 _INSTRUCTION) sampled by grep smoke checks at wave-merge rate. Sampling only one type would alias the others. All three sampling rates are required.

### Wave 0 Gaps
- [ ] `plugins/kais_aigc/tests/test_dreamina_manager.py` — NEW file covering IMG-01 (Semaphore + tenacity + batch) + IMG-02 (sync-queue block) + IMG-04 (RHD/LHD 3-attempt). ~8 tests.
- [ ] `plugins/kais_aigc/tests/test_vision_verify.py` — NEW file covering IMG-03 (confidence, cache, directional, low-confidence-not-reject). ~5 tests.
- [ ] `plugins/kais_aigc/tests/test_dreamina_stats.py` — NEW file covering IMG-05 (rich table, JSON flag, JSONL write). ~3 tests.
- [ ] `skills/kais-movie-pipeline/tests/test_img_integration.py` — NEW file covering XCUT-02 (p07 _INJECTION) + end-to-end orchestrator integration. ~3 tests.
- [ ] No framework install needed — pytest already available; httpx.MockTransport pattern reused from test_jimeng.py.

*(If no other gaps: existing `conftest.py` fixtures cover PipelineState round-trip + delegate spy patterns — reuse them.)*

## Security Domain

> Phase 73 has two network-input surfaces: (1) dreamina CLI subprocess (local binary, OAuth-authenticated), (2) GLM-4.6V vision API call (remote, API-key-authenticated). The security concern is primarily input validation (dreamina response parsing) + SSRF (image URL download).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — dreamina CLI auth is OAuth (handled by CLI, not by Phase 73 code); GLM-4.6V auth is API key (handled by zai provider) |
| V3 Session Management | no | N/A — no sessions |
| V4 Access Control | no | N/A — no privileged operations |
| V5 Input Validation | yes | dreamina CLI JSON response parsing: `json.loads()` in try/except; `submit_id` validated as string; `image_url` validated as HTTP(S) URL before download |
| V6 Cryptography | no | N/A — sha256 is for cache keys, not crypto |
| V8 Data Protection | yes | MetricsBuffer JSONL at `~/.hermes/metrics/` — no PII; metrics are operational (latency, success, retry count), not user data |

### Known Threat Patterns for IMG stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious dreamina response (injected URL) | Tampering | `image_url` validated as HTTP(S) via `_image_url_shape_ok()` pattern from vision_tools.py; `submit_id` validated as alphanumeric + hyphen |
| SSRF via crafted image URL | Tampering / Information Disclosure | `httpx.AsyncClient.get(url)` follows redirects but vision_tools.py `_validate_image_url_async()` pattern blocks private/internal addresses. dreamina_manager reuses this check. |
| dreamina CLI path injection | Tampering | `DREAMINA_CLI` is a hardcoded `Path.home() / ".local" / "bin" / "dreamina"` — not user-controllable |
| Subprocess command injection | Tampering | `subprocess.run([list], ...)` form (not shell=True) — no shell injection surface |

## Sources

### Primary (HIGH confidence)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/jimeng.py` — JimengClient HTTP API client (read in full, 393 lines). Sync httpx to :5100 with session rotation + exponential backoff. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/tools.py` — tool schemas + dispatch handlers (read in full, 355 lines). `_handle_kais_jimeng_call` dispatch pattern. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/plugin.yaml` — manifest declaring 5 tools. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/__init__.py` — `register(ctx)` with `ctx.register_tool` loop (read in full, 70 lines). `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_jimeng.py` — httpx.MockTransport test pattern (read in full, first 80 lines). `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_smoke.py` — importlib + yaml manifest parse pattern (read in full, first 50 lines). `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/__init__.py` — `ctx.register_cli_command` pattern (read in full, 71 lines). `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/cli.py` — `hermes formula stats` CLI implementation (read first 140 lines). Rich Table + argparse pattern. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/schema.py` — Pydantic v2 metric schemas (read in full, 361 lines). Field validator + model_config=ConfigDict(extra="forbid") pattern. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/dreamina_gen_image.py` — existing CLI wrapper (read in full, 199 lines). submit/poll/download/brightness/batch pattern. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/episodes/formc-test-01/assets/P04/generate_p04_assets.py` — episode-level CLI wrapper (read lines 280-460). dreamina_text2image / dreamina_image2image / crop_turnaround. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/SKILL.md` — CLI usage skill (read in full, 471 lines). Benchmark tables, pitfalls, parallel mode. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/references/batch-generation-quality-control.md` — batch pattern ref (read in full, 263 lines). query_result JSON schema, URL expiry, submit_id mapping. `[VERIFIED]`
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py` — P07 phase module (read first 170 lines). GoalBuilder + execution_hint with dreamina_gen_image.py invocation. `[VERIFIED]`
- `/data/workspace/hermes-agent/plugins/model-providers/zai/__init__.py` — zai provider profile (read in full, 23 lines). base_url, env_vars, fallback_models. `[VERIFIED]`
- `/data/workspace/hermes-agent/tools/vision_tools.py` — vision_analyze_tool implementation (read first 180 lines). async_call_llm + image download + base64 pattern. `[VERIFIED]`
- `/data/workspace/hermes-agent/hermes_cli/plugins.py:390-470` — PluginContext.register_cli_command + register_command signatures. `[VERIFIED]`
- Live `dreamina --help` + `dreamina text2image -h` + `dreamina image2image -h` + `dreamina query_result -h` output (captured 2026-07-09). `[VERIFIED]`

### Secondary (MEDIUM confidence)
- `.planning/research/v14-4track-upgrade/STACK.md` — IMG stack recommendation (tenacity + asyncio.Semaphore + Pillow + httpx). `[CITED]`
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — I-1 through I-6 IMG pitfalls. `[CITED]`
- `.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — IMG touch points table + Pattern 2 Vision-Verify Pipeline. `[CITED]`
- `.planning/phases/72-dub/72-PATTERNS.md` — XCUT-02 _INSTRUCTION injection pattern (3-site: constant + .task + .constraints + test). `[CITED]`

### Tertiary (LOW confidence — needs validation)
- GLM-4.6V multi-image message support — `[ASSUMED]` based on 128K context + vision model design; validate at execution time.
- `async_call_llm(prefer_vision=True)` routing to GLM-4.6V specifically — `[ASSUMED]` based on vision_tools.py pattern; verify `cli-config.yaml auxiliary.vision.model` at execution time.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; all verified against pyproject.toml + live imports.
- Architecture: HIGH — two code paths (jimeng.py HTTP vs dreamina CLI subprocess) verified; CONTEXT.md locks CLI path; existing `dreamina_gen_image.py` is the direct base for `dreamina_manager.py`.
- dreamina CLI shape: HIGH — `--help` output captured live for all relevant subcommands.
- GLM-4.6V integration: MEDIUM — zai provider verified; `async_call_llm` pattern verified from vision_tools.py; exact model routing (`prefer_vision=True` → GLM-4.6V) is `[ASSUMED]` pending cli-config.yaml check.
- Pitfalls: HIGH — all 6 pitfalls (I-1 through I-6) cross-verified against live SKILL.md + batch-generation-quality-control.md + PITFALLS.md research.

**Research date:** 2026-07-09
**Valid until:** 2026-08-08 (30 days — stable; the only currency risk is dreamina CLI version update changing subcommand signatures, which is LOW risk given the CLI is at a mature v1.4.5+ with stable command surface)
