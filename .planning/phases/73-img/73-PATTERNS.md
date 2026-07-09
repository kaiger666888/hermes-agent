# Phase 73: IMG - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 16 (6 Plan A code/tests + 5 Plan B integration/CLI/docs + 3 Plan B refs/SKILL + 2 Plan C tests/smoke)
**Analogs found:** 15 / 16 (1 partial: image2image-stratification.md is twin-by-spec but the 1/3/5-ref strength/retry table content is greenfield)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py` (NEW) | service/orchestrator | batch + event-driven | `templates/dreamina_gen_image.py` (199 lines — direct CLI subprocess base) + `plugins/kais_aigc/jimeng.py` (393 lines — degrade envelope + backoff pattern) | exact |
| `kais-hermes-skills/plugins/kais_aigc/vision_verify.py` (NEW) | service | request-response | `tools/vision_tools.py:950-1002` (`async_call_llm(task="vision")` + `extract_content_or_reasoning` + base64 data URL pattern) | exact |
| `kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py` (NEW) | CLI module + model | request-response | `plugins/platform_metrics/cli.py` (349 lines — exact template) + `plugins/platform_metrics/schema.py` (Pydantic) + `plugins/platform_metrics/queue.py` (JSONL ring buffer) | exact-twin |
| `kais-hermes-skills/plugins/kais_aigc/__init__.py` (MODIFY — +dreamina_stats CLI registration) | config/plugin-loader | request-response | `plugins/platform_metrics/__init__.py:33-70` (`register(ctx)` + `ctx.register_cli_command`) | exact-twin |
| `kais-hermes-skills/plugins/kais_aigc/plugin.yaml` (MODIFY — optional provides_tools entry) | config/manifest | file-I/O | same file (current 5-tool manifest at lines 1-5) | exact |
| `kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_manager.py` (NEW) | test | request-response | `plugins/kais_aigc/tests/test_jimeng.py:1-118` (httpx.MockTransport + `_client(handler)` factory pattern) + `tests/test_p09_unit.py:56-63` (`_make_delegate_spy` for goal assertion if p07 is touched) | exact |
| `kais-hermes-skills/plugins/kais_aigc/tests/test_vision_verify.py` (NEW) | test | request-response | `plugins/kais_aigc/tests/test_jimeng.py:24-42` (mock handler pattern — adapt to mock `async_call_llm`) | role-match |
| `kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_stats.py` (NEW) | test | file-I/O | `plugins/platform_metrics/tests/` (sibling — read at execution) + `test_jimeng.py` (pytest fixture conventions) | role-match |
| `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py` (MODIFY — +`_VISION_VERIFY_INSTRUCTION` XCUT-02) | service/orchestration | event-driven | `pipeline/phases/p09_shot_breakdown.py:51-70, 80-89` (`_CROSS_CUTTING_INSTRUCTION` + `_FORM_FACTOR_INSTRUCTION`) + `pipeline/phases/p10_voice.py` (DUB precedent — `_TTS_ENGINE_INSTRUCTION`) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md:564` (MODIFY — vision-verify advisory → MUST gate) | documentation/skill-body | request-response | `SKILL.md:433` (authoritative-source rule) + Phase 72 `SKILL.md:457` edit pattern (IndexTTS2 → CosyVoice demotion) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md:573` (MODIFY — Volvo V2 RHD/LHD lesson → 3-attempt budget reference) | documentation/skill-body | request-response | same file (existing pitfall line 573 — preserved + escalated) | exact |
| `kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/SKILL.md` (MODIFY — +dreamina_manager.py cross-reference + vision-verify pitfall) | documentation/skill-body | request-response | same file (lines 343-460 — existing dreamina pitfalls; append cross-reference to dreamina_manager) | exact |
| `kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md` (NEW) | reference-doc | file-I/O | `references/batch-generation-quality-control.md` (263 lines — Chinese-primary ref structure) + `cinematographer/references/vertical-screen-framing.md` (header block format) | role-match (twin-by-spec) |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_img_integration.py` (NEW — XCUT-02 + e2e) | test | event-driven | `tests/test_p09_unit.py:56-63, 159-184` (delegate spy + goal-content assertion) + `tests/conftest.py:104-111` (tmp_state_store fixture) | exact |
| `.planning/phases/73-img/73-smoke.sh` (NEW — bash smoke runner) | test/smoke | request-response | `.planning/phases/70-foundation-audit/70-smoke.sh` (80-line skeleton — exact) + `72-dub/72-smoke.sh` (Phase 72 sibling) | exact |

## Pattern Assignments

### `plugins/kais_aigc/dreamina_manager.py` (service/orchestrator, batch + event-driven — NEW)

**Primary analog:** `templates/dreamina_gen_image.py` (199 lines — RESEARCH-confirmed base for the CLI subprocess path)
**Secondary analog:** `plugins/kais_aigc/jimeng.py:212-220, 230-317` (degrade envelope + `_request_with_retry` pattern)

**Imports pattern** (dreamina_gen_image.py:21-28 — current CLI subprocess base):
```python
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
```
**Plan A evolves this to async** (add asyncio + tenacity + httpx):
```python
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, TypedDict

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)
```

**dreamina CLI submit/poll pattern** (dreamina_gen_image.py:36-71 — DIRECT base to mirror):
```python
def submit(prompt: str, ratio: str) -> str | None:
    code, out = run_cmd([
        "dreamina", "text2image",
        f"--prompt={prompt}",
        f"--ratio={ratio}",
        "--model_version=5.0",
        "--poll=0",           # non-blocking submit
    ], timeout=15)
    try:
        data = json.loads(out)
        sid = data.get("submit_id", "")
        if sid:
            return sid
    except json.JSONDecodeError:
        pass
    return None

def poll_until_done(submit_id: str, max_wait: int = 180) -> dict | None:
    # NOTE: query_result requires FULL UUID, NOT 8-char prefix
    #       (RESEARCH §dreamina CLI Actual Shape detail #2)
    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(5)
        code, out = run_cmd([
            "dreamina", "query_result",
            f"--submit_id={submit_id}",
        ], timeout=15)
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            continue
        status = data.get("gen_status", "unknown")  # gen_status NOT status
        if status == "success":
            return data
        if status in ("failed", "error"):
            return None
    return None
```

**Plan A wraps this in asyncio.Semaphore(10) + tenacity.AsyncRetrying** (per CONTEXT.md locked IMG-01):
```python
DEFAULT_CONCURRENCY = 10
DEFAULT_DEADLINE_SEC = 600
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
    prompts: list[dict[str, str]],
    output_dir: str,
    *,
    concurrency: int = DEFAULT_CONCURRENCY,
    deadline_sec: int = DEFAULT_DEADLINE_SEC,
    ratio: str = "16:9",
    model_version: str = "5.0",
) -> list[DreaminaTaskResult]:
    """Submit a batch — returns ONLY after all tasks resolve (IMG-02 sync queue)."""
    sem = asyncio.Semaphore(concurrency)

    async def _one(item: dict) -> DreaminaTaskResult:
        async with sem:
            return await _generate_one_with_verify(item, output_dir, ratio, model_version)

    # IMG-02: asyncio.gather blocks until ALL resolve (NOT as_completed)
    return await asyncio.wait_for(
        asyncio.gather(*[_one(item) for item in prompts]),
        timeout=deadline_sec,
    )
```

**tenacity AsyncRetrying pattern** (CONTEXT.md IMG-01 lock — exponential 1s, 2s, 4s, 8s, max 4 retries):
```python
async for attempt_info in AsyncRetrying(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(
        (TimeoutError, ConnectionError, subprocess.TimeoutExpired)
    ),
):
    with attempt_info:
        sid = await _dreamina_submit(prompt, ratio, model_version)
        raw = await _dreamina_poll(sid)
        await _download(raw["url"], output_path)
```

**httpx async download (replaces aria2c — PITFALL: aria2c broken data stream):**
```python
async def _download(url: str, output_path: str) -> None:
    # NOT aria2c (PITFALL: broken data stream per SKILL.md aria2c pitfall)
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(resp.content)
```

**Degrade envelope pattern** (mirror jimeng.py:212-220 — `_degrade()` returns dict, does NOT raise on network/5xx):
```python
def _degrade(operation: str, reason: str) -> DreaminaTaskResult:
    logger.warning("dreamina %s degraded: %s", operation, reason)
    return {"submit_id": "", "status": "failed", ...}
```

**RHD/LHD 3-attempt budget** (IMG-04 lock):
```python
async def _generate_one_with_verify(item, output_dir, ratio, model_version):
    from plugins.kais_aigc.vision_verify import verify_image_content
    for attempt in range(3):
        prompt = _escalate_prompt(item["prompt"], attempt, item.get("directional"))
        # ... submit + poll + download + tenacity ...
        vr = await verify_image_content(
            output_path, item.get("expected", ""),
            directional_check=item.get("directional"),
        )
        if vr["pass"]:
            return _ok_result(...)
        # else: retry with escalated prompt
    # Attempt 3 fallback: image2image from confirmed LHD reference
    return _degrade("vision_verify", "failed 3 attempts")
```

**Key mirroring decisions:**
1. **CLI subprocess path, NOT jimeng.py HTTP path** (CONTEXT.md locks CLI path; RESEARCH §Existing Code Paths confirms two parallel paths exist; CLI is validated production path with documented benchmark).
2. **asyncio.gather (block-on-all), NOT ThreadPoolExecutor.as_completed** (PITFALL I-3 BLOCKER — `as_completed` returns incrementally, can leak partial state to pipeline_state write).
3. **httpx.AsyncClient download, NOT aria2c** (PITFALL — aria2c multi-connection produces broken data stream on byteimg.com CDN per `batch-generation-quality-control.md:255` + SKILL.md aria2c pitfall).
4. **`gen_status` field name, NOT `status`** (verified in batch-generation-quality-control.md:204-226 — dreamina `query_result` JSON schema uses `gen_status`).
5. **FULL UUID for query_result, NOT 8-char prefix** (verified — using prefix returns `record not found`).
6. **URL signature expiry ~30min — download immediately after generation** (verified).

---

### `plugins/kais_aigc/vision_verify.py` (service, request-response — NEW)

**Analog:** `tools/vision_tools.py:950-1002` (RESEARCH-confirmed GLM-4.6V integration path)

**CRITICAL CORRECTION to RESEARCH.md §Pattern 2 example:** The actual API is `async_call_llm(task="vision", ...)`, NOT `async_call_llm(prefer_vision=True)`. Verified at `tools/vision_tools.py:967-973` and `agent/auxiliary_client.py:6006-6020` (signature has NO `prefer_vision` parameter; routing happens via `task="vision"` at auxiliary_client.py:6030).

**Imports pattern** (vision_tools.py:31, 40 + Plan A additions):
```python
from __future__ import annotations

import base64
import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from agent.auxiliary_client import async_call_llm, extract_content_or_reasoning

logger = logging.getLogger(__name__)
```

**`async_call_llm(task="vision")` exact pattern to mirror** (vision_tools.py:967-1002):
```python
call_kwargs = {
    "task": "vision",                # NOT prefer_vision=True
    "messages": messages,
    "temperature": 0.1,              # vision_tools default
    "max_tokens": 2000,
    "timeout": 120.0,                # auxiliary.vision.timeout default
}
response = await async_call_llm(**call_kwargs)
analysis = extract_content_or_reasoning(response)
```

**base64 data URL pattern for local images** (vision_tools.py:289-312 — `_image_to_base64_data_url`):
```python
def _image_to_base64_data_url(image_path: Path, mime_type: str | None = None) -> str:
    data = image_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    mime = mime_type or _detect_mime_type(image_path)
    return f"data:{mime};base64,{encoded}"
```
**Plan A vision_verify.py uses this directly** (RESEARCH §Open Question #2 — base64 is the SAFE path; do NOT rely on `file://` support).

**MIME type detection** (vision_tools.py:109-128 — `_detect_image_mime_type` by header bytes):
```python
def _detect_image_mime_type(image_path: Path) -> str | None:
    with image_path.open("rb") as f:
        header = f.read(64)
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    # ... GIF / BMP / WEBP / SVG ...
    return None
```

**Plan A `verify_image_content` signature** (per CONTEXT.md IMG-03 lock + PITFALL I-2 mitigation #4):
```python
_cache: dict[str, dict[str, Any]] = {}
_CACHE_TTL_SEC = 86400  # 24h per CONTEXT.md specifics


async def verify_image_content(
    image_path: str,
    expected_content: str,
    directional_check: str | None = None,  # "lhd" | "rhd" | None
) -> dict[str, Any]:
    """Returns {"pass": bool, "confidence": float, "description": str, "cached": bool}.

    Mandatory gate semantic (PITFALL I-2 #4):
        "pass" = vision-verify has RUN + returned high-confidence match.
        Low-confidence → pass=False for OPERATOR review (NOT auto-reject).
        Gate enforces "verify has RUN", NOT "verify has APPROVED".
    """
    # sha256 cache key (PITFALL I-1 mitigation #4)
    sha = hashlib.sha256(Path(image_path).read_bytes()).hexdigest()
    if sha in _cache:
        return {**_cache[sha], "cached": True}

    # Chinese prompt — GLM-4.6V is Chinese-native (RESEARCH §Chinese prompt support)
    question = (
        f"这张图片是否包含以下内容？请回答是或否并给出置信度(0-1)。"
        f"内容：{expected_content}"
    )
    if directional_check == "lhd":
        question += "\n另外：方向盘在左侧（左舵LHD）还是右侧（右舵RHD）？"

    data_url = _image_to_base64_data_url(Path(image_path))
    response = await async_call_llm(
        task="vision",                            # CORRECTED (not prefer_vision)
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": question},
            ],
        }],
        temperature=0.1,
        max_tokens=2000,
        timeout=120.0,
    )
    text = extract_content_or_reasoning(response)
    result = _parse_vision_response(text, expected_content, directional_check)
    _cache[sha] = result
    return {**result, "cached": False}
```

**Confidence parser** (RESEARCH §Confidence score parsing):
```python
def _parse_vision_response(text: str, expected: str, directional: str | None) -> dict[str, Any]:
    m = re.search(r"置信度.*?([0-9.]+)", text) or re.search(r"confidence.*?([0-9.]+)", text, re.I)
    confidence = float(m.group(1)) if m else 0.5  # default 0.5 = low-confidence flag
    passed = confidence >= 0.7  # high-confidence threshold
    if directional == "lhd":
        lhd_match = re.search(r"左舵|LHD|left.?hand", text, re.I)
        passed = passed and bool(lhd_match)
    return {"pass": passed, "confidence": confidence, "description": text[:200]}
```

**Key invariants:**
1. **`task="vision"` routes to GLM-4.6V via the auxiliary vision router** (NOT `prefer_vision=True` — that parameter does not exist in the API).
2. **base64 data URL for local images** (RESEARCH §Open Question #2 — safe default; vision_tools.py uses this).
3. **Batched multi-image call support** (PITFALL I-1 mitigation #1 — build content array of 4-8 images per message; GLM-4.6V supports multi-image messages).
4. **Chinese prompts** (GLM-4.6V is Chinese-native — RESEARCH §Chinese prompt support).
5. **24h cache TTL** (CONTEXT.md specifics; sha256 keyed).

---

### `plugins/kais_aigc/dreamina_stats.py` (CLI + model, request-response — NEW)

**Analog (exact twin):** `plugins/platform_metrics/cli.py` (349 lines — RESEARCH-confirmed exact template)
**Supporting analogs:** `plugins/platform_metrics/schema.py` (Pydantic v2) + `plugins/platform_metrics/queue.py` (JSONL ring buffer)

**Imports pattern** (platform_metrics/cli.py:32-41 — mirror EXACTLY):
```python
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

__all__ = ["register_dreamina_cli", "_dreamina_command"]
```

**`register_dreamina_cli` argparse pattern** (platform_metrics/cli.py:124-152 — mirror with "dreamina" namespace):
```python
def register_dreamina_cli(subparser: argparse.ArgumentParser) -> None:
    """Build the `hermes dreamina` argparse tree.

    Called once at plugin-load time by hermes_cli/main.py via
    ctx.register_cli_command(name="dreamina", setup_fn=...). Mirrors
    plugins/platform_metrics/cli.py:register_formula_cli.
    """
    subs = subparser.add_subparsers(dest="dreamina_command")

    stats_p = subs.add_parser(
        "stats",
        help=(
            "Show dreamina batch generation SLA dashboard "
            "(latency / success rate / cost per stratum)"
        ),
    )
    stats_p.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit counts-only JSON (no rich tables, no ANSI). "
            "Suitable for shell scripting / piping into jq."
        ),
    )
```

**Dispatch + emit pattern** (platform_metrics/cli.py:165-265 — mirror):
```python
def _dreamina_command(args: argparse.Namespace) -> int:
    sub = getattr(args, "dreamina_command", None)
    if not sub:
        print(_HELP_TEXT)
        return 0
    if sub == "stats":
        return _cmd_stats(args)
    print(f"unknown subcommand: {sub!r} — available: stats")
    return 2


def _cmd_stats(args: argparse.Namespace) -> int:
    hermes_home = Path(get_hermes_home())
    metrics_file = hermes_home / "metrics" / "dreamina_stats.jsonl"
    metrics = read_metrics(metrics_file, limit=1000)

    if getattr(args, "json", False):
        return _emit_json(metrics)
    return _emit_rich(metrics)
```

**Rich table pattern** (platform_metrics/cli.py:267-340 — `_emit_rich`):
```python
def _emit_rich(metrics: list[dict]) -> int:
    console = Console()
    t = Table(title="Dreamina SLA Dashboard", title_style="bold cyan")
    t.add_column("Stratum", style="cyan")
    t.add_column("Count", justify="right")
    t.add_column("p50 (ms)", justify="right")
    t.add_column("p95 (ms)", justify="right")
    t.add_column("Success %", justify="right")
    # ... aggregate by stratum (1-ref / 3-ref / 5-ref) ...
    console.print(t)
    return 0
```

**JSONL read pattern** (platform_metrics/queue.py:75-119 — `_read_jsonl` to mirror):
```python
def read_metrics(path: Path, limit: int = 1000) -> list[dict[str, Any]]:
    """Read last N metrics from JSONL (ring buffer semantic)."""
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:   # PLW1514 compliance
        for lineno, raw in enumerate(f, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                logger.warning("malformed JSON at %s:%d (%s) — skipping", path, lineno, exc)
                continue
            if isinstance(parsed, dict):
                out.append(parsed)
    return out[-limit:]
```

**JSONL write pattern** (platform_metrics/queue.py:64-72 — `_append_jsonl`):
```python
def record_metric(path: Path, metric: dict[str, Any]) -> None:
    """Append one metric record to JSONL. Sync (INFRA-04 compliant)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(metric, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
```

**Pydantic metric schema** (platform_metrics/schema.py:42, 102 — `BaseModel` + `field_validator` + `ConfigDict(extra="forbid")`):
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class DreaminaTaskMetrics(BaseModel):
    """Per-task dreamina generation metric record (IMG-05 schema)."""
    model_config = ConfigDict(extra="forbid")

    submit_id: str
    stratum: str = Field(description="1-ref | 3-ref | 5-ref | text2image")
    latency_ms: int = Field(ge=0)
    success: bool
    retries: int = Field(ge=0)
    vision_verified: bool
    vision_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    ts: str  # ISO 8601 UTC

    @field_validator("stratum")
    @classmethod
    def _stratum_values(cls, v: str) -> str:
        if v not in {"1-ref", "3-ref", "5-ref", "text2image"}:
            raise ValueError(f"invalid stratum: {v!r}")
        return v
```

**Key invariants:**
1. **Sync `@contextmanager` or plain function — NO `asyncio.gather`, NO GLM calls** (PITFALL I-5 + INFRA-04 preservation).
2. **Storage at `~/.hermes/metrics/dreamina_stats.jsonl`** (HERMES_HOME convention per CONTEXT.md specifics).
3. **Ring buffer 1000 entries** (CONTEXT.md specifics default; configurable via `dreamina_stats_buffer_size`).
4. **Rich table default + `--json` flag** (CONTEXT.md specifics — BOTH output formats).
5. **Auto-discovered at `hermes_cli/main.py:11942` via `_cli_commands`** (platform_metrics/cli.py:3-5 docstring confirms — zero main.py edits).

---

### `plugins/kais_aigc/__init__.py` (config/plugin-loader, request-response — MODIFY +CLI registration)

**Analog (exact twin):** `plugins/platform_metrics/__init__.py:33-70` (`register(ctx)` + `ctx.register_cli_command`)

**Pattern to add to kais_aigc register(ctx)** (mirror platform_metrics/__init__.py:53-70):
```python
def register(ctx) -> None:
    # ... existing tool registrations (kais_gold_team_submit, etc.) ...

    # Plan B: register `hermes dreamina` CLI subcommand (IMG-05)
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
            "cost per stratum. --json emits machine-readable output."
        ),
    )
```

**`ctx.register_cli_command` signature** (verified at hermes_cli/plugins.py:390-410 — RESEARCH §hermes CLI Command Registration):
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

---

### `plugins/kais_aigc/tests/test_dreamina_manager.py` (test, request-response — NEW)

**Analog 1:** `plugins/kais_aigc/tests/test_jimeng.py:1-118` (httpx.MockTransport + `_client(handler)` factory + captured request assertion)
**Analog 2:** `tests/test_p09_unit.py:56-63` (`_make_delegate_spy` for goal assertion — NOT needed here unless testing XCUT-02)

**Imports + factory pattern** (test_jimeng.py:13-42):
```python
from __future__ import annotations

import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock

from plugins.kais_aigc.dreamina_manager import batch_submit, DreaminaTaskResult


def _mock_dreamina_cli(submit_responses: dict[str, str], poll_responses: dict[str, dict]):
    """Patch subprocess.run to return scripted dreamina CLI outputs."""
    def _fake_run(cmd, **kw):
        if "text2image" in cmd:
            return _MockResult(0, json.dumps(submit_responses.get("submit", {"submit_id": "abc123"})))
        if "query_result" in cmd:
            return _MockResult(0, json.dumps(poll_responses.get("poll", {"gen_status": "success"})))
        return _MockResult(1, "")
    return _fake_run


class _MockResult:
    def __init__(self, code, stdout):
        self.returncode = code
        self.stdout = stdout
        self.stderr = ""
```

**Test functions** (per RESEARCH §Phase Requirements → Test Map — IMG-01/02/04):
```python
@pytest.mark.asyncio
async def test_semaphore_caps_at_10():
    # Assert asyncio.Semaphore(10) — at most 10 concurrent _dreamina_submit calls
    ...

@pytest.mark.asyncio
async def test_retry_on_timeout():
    # tenacity retries on subprocess.TimeoutExpired; assert 4 attempts then degrade
    ...

@pytest.mark.asyncio
async def test_batch_submit_returns_results():
    # All items return DreaminaTaskResult dicts
    ...

@pytest.mark.asyncio
async def test_sync_queue_blocks_until_all_resolve():
    # IMG-02 — pipeline_state write happens AFTER asyncio.gather returns
    ...

@pytest.mark.asyncio
async def test_failure_record_explicit():
    # Failed task returns status="failed" dict (NOT silently skipped)
    ...

@pytest.mark.asyncio
async def test_rhd_lhd_3_attempt_budget():
    # IMG-04 — _escalate_prompt called 3 times with increasing emphasis
    ...

@pytest.mark.asyncio
async def test_image2image_fallback_on_attempt_3():
    # IMG-04 — attempt 3 invokes dreamina image2image (not text2image)
    ...
```

**Key test invariants:**
1. **NO real subprocess / network** — patch `subprocess.run` and `async_call_llm` (test_jimeng.py:24-42 MockTransport precedent — adapt to subprocess).
2. **`pytest.mark.asyncio`** for async tests (requires `pytest-asyncio` per CLAUDE.md — already pinned).
3. **Each test < 1s** (no real dreamina CLI invocation).

---

### `plugins/kais_aigc/tests/test_vision_verify.py` (test, request-response — NEW)

**Analog:** `plugins/kais_aigc/tests/test_jimeng.py:24-42` (mock handler factory pattern — adapt to `async_call_llm`)

**Test functions** (per RESEARCH §Phase Requirements → Test Map — IMG-03):
```python
@pytest.mark.asyncio
async def test_verify_returns_confidence():
    # Mock async_call_llm returns "是，置信度0.92" → parsed confidence=0.92
    ...

@pytest.mark.asyncio
async def test_cache_hit():
    # Same image_path twice → second call returns cached=True, async_call_llm NOT called
    ...

@pytest.mark.asyncio
async def test_low_confidence_flags_not_rejects():
    # Mock returns 置信度0.4 → result["pass"]=False (flagged for review, not auto-reject)
    ...

@pytest.mark.asyncio
async def test_directional_check_lhd():
    # directional_check="lhd" → prompt includes "方向盘在左侧" question
    ...

@pytest.mark.asyncio
async def test_chinese_prompt_used():
    # Assert prompt contains "这张图片是否包含" (Chinese-native per RESEARCH §Chinese prompt support)
    ...
```

**Mock async_call_llm pattern:**
```python
@pytest.mark.asyncio
async def test_verify_returns_confidence(monkeypatch):
    async def _fake_call(**kwargs):
        return {"choices": [{"message": {"content": "是，置信度0.92"}}]}
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.async_call_llm",
        _fake_call,
    )
    result = await verify_image_content("/fake.png", "baby in car seat")
    assert result["confidence"] == 0.92
    assert result["pass"] is True
```

---

### `pipeline/phases/p07_scene_generation.py` (service/orchestration, event-driven — +`_VISION_VERIFY_INSTRUCTION` XCUT-02)

**Analog 1 (constant definition):** `pipeline/phases/p09_shot_breakdown.py:51-70` (`_CROSS_CUTTING_INSTRUCTION`) + `:80-89` (`_FORM_FACTOR_INSTRUCTION` — Phase 71 precedent)
**Analog 2 (DUB sibling):** `pipeline/phases/p10_voice.py` (Phase 72 — `_TTS_ENGINE_INSTRUCTION`)
**Analog 3 (alternative multi-constant style):** `pipeline/phases/p04_character_design.py:48-70` (3 sibling constants)

**Current p07 state** (read in full, first 180 lines):
- Lines 36-45: imports + logger
- Line 47: `PHASE_ID = "p07_scene_generation"`
- Lines 56-63: `run()` signature with 6 Callable args (episode_id, asset_bus_read, asset_bus_write, delegate_task, trigger_gate, sync_canvas)
- Lines 86-148: GoalBuilder chain with `.role(...)`, `.context(...)`, `.task(steps=[5 items at 96-102])`, `.execution_hint(...)`, `.schema(shape={...} at 130-134)`, `.constraints([4 items at 135-140])`, `.quality([4 items at 141-145])`
- **No `_INSTRUCTION` constants currently defined** — Phase 73 is the first to add them to p07

**Plan B adds `_VISION_VERIFY_INSTRUCTION` near module top** (mirror `p09:80` placement + Phase 71/72 XCUT-02 precedent):
```python
# ―― Vision-verify mandatory gate (v14.0 IMG-03 / XCUT-02 / META-RULE X-2) ――
# Subagents see ONLY the goal string; they do NOT read SKILL.md at runtime.
# Therefore the vision-verify rule MUST be encoded as a constant and injected
# into .task(steps=[...]) AND .constraints([...]) — both injection sites are
# required for the rule to be enforceable rather than advisory.
_VISION_VERIFY_INSTRUCTION = (
    "VISION-VERIFY MANDATORY GATE (v14.0 IMG-03 — MUST run vision-verify on "
    "every generated image BEFORE ComfyUI upload):\n"
    "1. After dreamina batch submission completes, invoke "
    "plugins.kais_aigc.vision_verify.verify_image_content(image_path, expected_content, "
    "directional_check) for EACH generated image.\n"
    "2. The gate enforces 'verify has RUN', NOT 'verify has APPROVED' (PITFALL I-2). "
    "Low-confidence results (< 0.7) surface to operator for review — do NOT auto-reject.\n"
    "3. RHD/LHD 3-attempt budget (IMG-04): if directional_check fails, retry with escalated "
    "prompt (LHD emphasis → negative RHD prompt → image2image fallback from confirmed LHD ref).\n"
    "4. Pipeline state write happens ONLY after asyncio.gather resolves ALL images "
    "(IMG-02 sync-queue semantic — prevents P11 render on missing refs)."
)
```

**Plan B injects into `.task(steps=[...])`** at line 96-102:
```python
.task(steps=[
    "Load all four experts via skill_view",
    "style_genome constructs 5D style vector ...",
    "visual_executor generates 5-view scene image set per scene ...",
    "prompt_injector enforces character anchor + style consistency ...",
    "colorist designs CxSxZ color intent + LUT plan",
    f"{_VISION_VERIFY_INSTRUCTION}",   # NEW Plan B XCUT-02
])
```

**Plan B adds a MUST constraint** at lines 135-140:
```python
.constraints([
    "MUST generate ≥5 views per scene for multi-angle reference",
    "MUST enforce character anchor consistency in every prompt (prompt_injector)",
    "MUST produce CxSxZ color combination, not ad-hoc colors (colorist)",
    "MUST keep scene images bright enough (avg brightness > 60) — avoid dark/underexposed output",
    "MUST vision-verify every image before ComfyUI upload (IMG-03 mandatory gate)",  # NEW
])
```

**MAX_CONSTRAINTS=7 budget** — current p07 has 4 constraints; adding 1 brings it to 5. Within budget.

**Plan B updates execution_hint** (lines 103-129): swap `--workers 4` → reference `dreamina_manager.batch_submit()` with 10-parallel + vision-verify gate (mirror the bash invocation block at lines 107-123, updated for the new orchestrator).

---

### `skills/kais-movie-pipeline/SKILL.md:564` (documentation, request-response — pitfall escalation)

**Analog:** same file's authoritative-source rule (line 433) + Phase 72 `SKILL.md:457` edit pattern (IndexTTS2 → DEPRECATED demotion)

**Current text** (line 564, verified per RESEARCH §SKILL.md Pitfall Content):
```markdown
Reference images SHOULD be vision-verified before upload to ComfyUI
```
**Plan B edit direction** (escalate from advisory SHOULD to mandatory MUST):
```markdown
<!-- AFTER (v14.0 IMG-03) -->
Reference images MUST be vision-verified before upload to ComfyUI.
The gate is enforced by `plugins/kais_aigc/dreamina_manager.batch_submit()` which
calls `plugins.kais_aigc.vision_verify.verify_image_content()` on every generated
image. The gate enforces "verify has RUN", NOT "verify has APPROVED" (PITFALL I-2) —
low-confidence results surface to operator for review, NOT auto-reject.
```

**RHD/LHD line 573 edit** (Volvo V2 lesson — escalate from advisory pitfall to systematic mitigation reference):
```markdown
<!-- AFTER (v14.0 IMG-04) -->
Dreamina generates RHD even when prompted for LHD (Volvo V2 lesson).
**Systematic mitigation:** `dreamina_manager._generate_one_with_verify()` implements
a 3-attempt budget: (1) LHD emphasis prompt, (2) stronger LHD + negative RHD prompt,
(3) image2image fallback from confirmed LHD reference. Target ≥95% LHD success after
3 attempts (vs ~80% single-attempt). See `references/image2image-stratification.md`
for per-stratum retry budgets.
```

**Frontmatter freeze (FOUND-08):** edit body only; do NOT mutate YAML frontmatter (`name`, `description`, `tags`, `related_skills`, `expert_id`, `metrics`).

---

### `skills/kais-creative/kais-jimeng-cli/SKILL.md` (documentation, request-response — +dreamina_manager cross-reference)

**Analog:** same file (471 lines — existing dreamina pitfalls at 343-460; append cross-reference section)

**Plan B adds a new H2 section** (at end of body, after existing pitfalls):
```markdown
## Production Orchestrator (v14.0 IMG-01..05)

For pipeline-internal batch generation, use `plugins.kais_aigc.dreamina_manager.batch_submit()`
(NOT this skill's standalone CLI scripts). The orchestrator provides:
- asyncio.Semaphore(10) concurrency cap (validated 10-parallel sweet spot)
- tenacity retry (1s, 2s, 4s, 8s exponential backoff, max 4 retries)
- GLM-4.6V vision-verify mandatory gate before ComfyUI upload (IMG-03)
- RHD/LHD 3-attempt budget (IMG-04)
- `hermes dreamina stats` SLA dashboard (IMG-05)

See `references/image2image-stratification.md` for 1/3/5-ref strength + retry budgets.
```

---

### `references/image2image-stratification.md` (reference-doc, file-I/O — NEW)

**Analog 1 (structural twin):** `references/batch-generation-quality-control.md` (263 lines — Chinese-primary ref with workflow + Python template + validation)
**Analog 2 (header block):** `cinematographer/references/vertical-screen-framing.md:1-6` (Source / Copyright / Last-verified block)

**Header block to mirror** (batch-generation-quality-control.md:1-3 + vertical-screen-framing.md:1-6):
```markdown
# image2image 分层策略 — 1-ref / 3-ref / 5-ref 参数 + 重试预算

**Source:** CONTEXT.md IMG-06 locked decision + STACK.md IMG recommendation
**Copyright:** Fair Use — parameter tables derived from dreamina CLI `--help` + operator validation.
**Last-verified:** 2026-07-09
verified_date: 2026-07
```

**Content structure** (per CONTEXT.md IMG-06 lock + RESEARCH §image2image Stratification):
```markdown
## 分层参数表 (Stratification Table)

| 分层 (Stratum) | 参考图数量 | Strength (prompt 强度) | 重试预算 | 适用场景 |
|---------------|-----------|----------------------|---------|---------|
| 高保真 (High-fidelity) | 1-ref | 0.75 (强 prompt 遵循) | 3 | 模板权威,最小创造性偏差(如:角色 turnaround 单参考) |
| 均衡 (Balanced) | 3-ref | 0.65 (中度混合) | 4 | 角色+场景+服装;保真与创意平衡 |
| 创意 (Creative) | 5-ref | 0.55 (宽松遵循) | 5 | 多角度场景;创造性偏差预期;失败率随 ref 数非线性增长 |

## dreamina CLI image2image 调用 (verified)
```bash
dreamina image2image \
  --images=ref1.png,ref2.png,ref3.png \
  --prompt="<prompt with strength wording>" \
  --ratio=16:9 \
  --model_version=5.0 \
  --resolution_type=2k \
  --poll=120
```
(注:CLI 无 `--strength` 参数;strength 是 prompt-engineering 概念,通过措辞强度实现)

## 每层 prompt 模板
...

## 每层重试策略
...

## MetricsBuffer 每层成功率追踪 (IMG-05)
...
```

---

### `skills/kais-movie-pipeline/tests/test_img_integration.py` (test, event-driven — NEW)

**Analog 1 (XCUT-02 goal assertion):** `tests/test_p09_unit.py:56-63, 159-184` (`_make_delegate_spy` + captured["goal"])
**Analog 2 (PipelineState fixture):** `tests/conftest.py:104-111` (`tmp_state_store`)

**XCUT-02 test pattern** (mirror test_p09_unit.py:56-63):
```python
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p07_scene_generation as p07


def _make_delegate_spy(captured: dict):
    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": "...ok..."}
    return _mock


def test_p07_goal_includes_vision_verify_instruction():
    captured: dict = {}
    p07.run(
        episode_id="ep-img",
        asset_bus_read=lambda slot: {} if slot == "spatio-temporal-script" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "VISION-VERIFY MANDATORY GATE" in captured["goal"]
    assert "MUST vision-verify" in captured["goal"]
    assert "vision_verify.verify_image_content" in captured["goal"]
```

**End-to-end orchestrator integration test** (mock subprocess + mock async_call_llm):
```python
@pytest.mark.asyncio
async def test_end_to_end_orchestrator(monkeypatch, tmp_path):
    # Patch dreamina CLI subprocess + async_call_llm + record_metric
    # Verify: dreamina_manager → vision_verify → MetricsBuffer write chain
    ...
```

---

### `.planning/phases/73-img/73-smoke.sh` (test/smoke, request-response — NEW bash runner)

**Analog (exact skeleton):** `.planning/phases/70-foundation-audit/70-smoke.sh` (80 lines) + Phase 72 `72-smoke.sh` sibling

**Smoke script skeleton to mirror** (70-smoke.sh:1-18):
```bash
#!/usr/bin/env bash
# Phase 73 IMG smoke runner — N assertions. Usage: bash .planning/phases/73-img/73-smoke.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 73 IMG smoke — N assertions"
echo "Repo root: $REPO_ROOT"
echo "KHS root: $KHS_ROOT"
echo ""
```

**Per-assertion block pattern** (70-smoke.sh:20-25):
```bash
# IMG-XXa: <description>
if [ ! -f "$TARGET_FILE" ]; then
    echo "FAIL: IMG-XXa — <reason>"
    exit 1
fi
echo "OK: IMG-XXa — <success>"
```

**Grep-count assertion pattern** (70-smoke.sh:28-33):
```bash
COUNT=$(grep -c 'pattern' "$FILE" || true)
if [ "$COUNT" -lt N ]; then
    echo "FAIL: IMG-XXb — expected >=N, got $COUNT"
    exit 1
fi
echo "OK: IMG-XXb — $COUNT entries (>= N)"
```

**Phase 73 smoke assertions to draft** (per RESEARCH §Phase Requirements → Test Map):
- IMG-01a: `test -f $KHS_ROOT/plugins/kais_aigc/dreamina_manager.py`
- IMG-01b: `grep -c "asyncio.Semaphore" $KHS_ROOT/plugins/kais_aigc/dreamina_manager.py` returns `>= 1`
- IMG-01c: `grep -c "tenacity\|AsyncRetrying" $KHS_ROOT/plugins/kais_aigc/dreamina_manager.py` returns `>= 1`
- IMG-02a: `grep -c "asyncio.gather" $KHS_ROOT/plugins/kais_aigc/dreamina_manager.py` returns `>= 1`
- IMG-03a: `test -f $KHS_ROOT/plugins/kais_aigc/vision_verify.py`
- IMG-03b: `grep -c 'task="vision"' $KHS_ROOT/plugins/kais_aigc/vision_verify.py` returns `>= 1`
- IMG-03c: `grep -c "async_call_llm" $KHS_ROOT/plugins/kais_aigc/vision_verify.py` returns `>= 1`
- IMG-04a: `grep -c "image2image\|_escalate_prompt" $KHS_ROOT/plugins/kais_aigc/dreamina_manager.py` returns `>= 1`
- IMG-05a: `test -f $KHS_ROOT/plugins/kais_aigc/dreamina_stats.py`
- IMG-05b: `grep -c "register_cli_command" $KHS_ROOT/plugins/kais_aigc/__init__.py` returns `>= 1`
- IMG-05c: `grep -c "dreamina_stats.jsonl" $KHS_ROOT/plugins/kais_aigc/dreamina_stats.py` returns `>= 1`
- IMG-06a: `test -f $KHS_ROOT/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md`
- IMG-06b: `grep -c "1-ref\|3-ref\|5-ref" $KHS_ROOT/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md` returns `>= 3`
- XCUT-02a: `grep -c "_VISION_VERIFY_INSTRUCTION" $KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py` returns `>= 1`
- XCUT-02b: `grep -c "MUST vision-verify" $KHS_ROOT/skills/kais-movie-pipeline/SKILL.md` returns `>= 1`

Plus a final line: `echo "Phase 73 smoke status: ALL N ASSERTIONS PASSED"`.

**Note:** the bash smoke runner does NOT invoke live dreamina CLI / GLM-4.6V / ComfyUI (those are operator-action handoff). Live integration tests live in `test_img_integration.py` (mocked); live production probes are documented in `image2image-stratification.md` for operator pre-flight use.

---

## Shared Patterns

### XCUT-02 `_INSTRUCTION` Constant Injection (META-RULE X-2)
**Source:** `p09_shot_breakdown.py:51-70, 80-89` (`_CROSS_CUTTING_INSTRUCTION` + `_FORM_FACTOR_INSTRUCTION`) + Phase 72 `p10_voice.py` (`_TTS_ENGINE_INSTRUCTION`)
**Apply to:** `_VISION_VERIFY_INSTRUCTION` in p07_scene_generation.py
**Core invariant (3-site injection):**
1. Define `_SOME_INSTRUCTION = "..."` constant with MUST/MANDATORY keyword at module top
2. Inject via `.task(steps=[f"{_SOME_INSTRUCTION}", ...])` AND a parallel `.constraints(["MUST ..."])` line
3. Assert via `test_*_unit.py` captured["goal"] goal-content test
Without all three sites, the rule is invisible to the subagent at runtime (subagents see ONLY the goal string, NOT SKILL.md).
**Budget rule:** MAX_CONSTRAINTS=7 per goal; current p07 has 4 constraints, adding 1 → 5 (within budget).

### asyncio.Semaphore + tenacity + sync-queue (IMG-01 + IMG-02)
**Source:** `templates/dreamina_gen_image.py:123-160` (existing ThreadPoolExecutor base) + CONTEXT.md IMG-01 lock
**Apply to:** `dreamina_manager.batch_submit()` orchestrator
**Core invariant:**
- `asyncio.Semaphore(10)` caps concurrency (NOT auto-scaling — IMG-07 deferred)
- `tenacity.AsyncRetrying(stop=stop_after_attempt(4), wait=wait_exponential(1,1,8), retry=retry_if_exception_type(...))` for transient failures
- `asyncio.gather(*tasks)` blocks until ALL resolve (NOT `as_completed` — PITFALL I-3 BLOCKER)
- Pipeline state write happens AFTER gather returns; failure records are explicit

### GLM-4.6V Vision Call via auxiliary_client (IMG-03)
**Source:** `tools/vision_tools.py:967-1002` (RESEARCH-verified pattern)
**Apply to:** `vision_verify.verify_image_content()`
**Core invariant:**
```python
response = await async_call_llm(
    task="vision",               # CORRECTED: NOT prefer_vision=True
    messages=[{...image_url + text...}],
    temperature=0.1,
    max_tokens=2000,
    timeout=120.0,
)
text = extract_content_or_reasoning(response)
```
**CRITICAL CORRECTION:** RESEARCH.md §Pattern 2 + §GLM-4.6V API Integration both state `prefer_vision=True`. This parameter DOES NOT EXIST in `async_call_llm` (verified at auxiliary_client.py:6006-6020 signature). The correct routing mechanism is `task="vision"` (verified at auxiliary_client.py:6030 + vision_tools.py:968). Plan A MUST use `task="vision"`.
Plus: local images MUST be base64-encoded as `data:{mime};base64,...` (RESEARCH §Open Question #2 — safe default; vision_tools.py `_image_to_base64_data_url` at :289-312).

### MetricsBuffer JSONL Ring Buffer (IMG-05, INFRA-04 compliant)
**Source:** `plugins/platform_metrics/cli.py` + `plugins/platform_metrics/queue.py:64-119` + `plugins/platform_metrics/schema.py:42, 102`
**Apply to:** `dreamina_stats.py` (CLI + read/record functions + Pydantic schema)
**Core invariant:**
- Sync I/O (NO `asyncio.gather`, NO GLM calls per metric — INFRA-04 preservation)
- `_append_jsonl` / `_read_jsonl` mirror queue.py:64-119 EXACTLY (including `encoding="utf-8"` PLW1514 compliance + malformed-line skip-and-log)
- Pydantic v2 schema with `model_config = ConfigDict(extra="forbid")` + `field_validator` (mirror schema.py:42, 102)
- Rich table default + `--json` flag (mirror cli.py:244-340)
- Auto-discovered at `hermes_cli/main.py:11942` via `_cli_commands` (zero main.py edits)

### ctx.register_cli_command (Hermes plugin CLI hook)
**Source:** `plugins/platform_metrics/__init__.py:33-70` + `hermes_cli/plugins.py:390-410`
**Apply to:** `plugins/kais_aigc/__init__.py` register(ctx) — add `hermes dreamina stats` CLI
**Core invariant:**
```python
ctx.register_cli_command(
    name="dreamina",
    help="...",
    setup_fn=register_dreamina_cli,    # builds argparse subparser
    handler_fn=_dreamina_command,      # dispatches subcommand
    description="...",
)
```
Auto-discovered at `hermes_cli/main.py:11942`. Zero edits to `hermes_cli/main.py`.

### SKILL.md Body Edit (FOUND-08 frontmatter freeze)
**Source:** `_shared/SKILL-LAYOUT.md` + CLAUDE.md §Skill File Conventions + Phase 71/72 precedent
**Apply to:** `kais-movie-pipeline/SKILL.md:564, 573` (pitfall escalation) + `kais-jimeng-cli/SKILL.md` (cross-reference append)
**Core invariant:** YAML frontmatter (`name`/`description`/`tags`/`related_skills`/`expert_id`/`metrics`) is FROZEN byte-identical. Edit body prose only. Insert inline near the relevant pitfall; do not restructure H2 headings.

### Goal-Content Test Assertion
**Source:** `tests/test_p09_unit.py:56-63, 159-184` + Phase 71 `test_form_factor.py` + Phase 72 `test_dub_division.py`
**Apply to:** `test_img_integration.py::test_p07_goal_includes_vision_verify_instruction`
**Core invariant:**
```python
captured: dict = {}
p07.run(..., delegate_task=_make_delegate_spy(captured), ...)
assert "VISION-VERIFY MANDATORY GATE" in captured["goal"]
assert "MUST vision-verify" in captured["goal"]
```
One test function per MUST keyword; all run under 2s; no Docker, no network.

### Smoke Script grep/file Assertions
**Source:** `.planning/phases/70-foundation-audit/70-smoke.sh` (80 lines) + `.planning/phases/72-dub/72-smoke.sh`
**Apply to:** `.planning/phases/73-img/73-smoke.sh`
**Core invariant:** `set -euo pipefail` + `SCRIPT_DIR`/`REPO_ROOT`/`KHS_ROOT` resolution via `BASH_SOURCE` + per-assertion block (grep-count OR file-existence OR python-import check) + final `echo "ALL N ASSERTIONS PASSED"`. Exits non-zero on first failure. Does NOT invoke live dreamina CLI / GLM-4.6V / ComfyUI (those are operator-action probes).

### dreamina CLI Contract (subprocess invocation invariants)
**Source:** `templates/dreamina_gen_image.py:36-71` + `batch-generation-quality-control.md:204-226, 254`
**Apply to:** `dreamina_manager._dreamina_submit()` + `_dreamina_poll()`
**Core invariants (all PITFALLS):**
1. `text2image --poll=0` = non-blocking submit, returns `submit_id` (8-char prefix)
2. `query_result --submit_id=<UUID>` requires FULL UUID (NOT 8-char prefix — returns `record not found`)
3. Response JSON uses `gen_status` field (NOT `status`)
4. `result_json.images[0].image_url` is the download URL
5. URL signature expires ~30min — download IMMEDIATELY after generation
6. `list_task` status is cached/lazy — always poll via `query_result`
7. `image2image` accepts 1-10 images via `--images=path1,path2,...`; NO `--strength` flag (strength is prompt-engineering)
8. `subprocess.run([list, ...])` form (NOT `shell=True`) — no shell injection surface
9. `httpx.AsyncClient` download (NOT aria2c — broken data stream on byteimg.com CDN)

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `references/image2image-stratification.md` (1/3/5-ref strength + retry table content) | reference-doc | file-I/O | Structural twin (`batch-generation-quality-control.md`) IS the analog for structure, but the 1/3/5-ref strength/retry stratification table content is greenfield — no existing ref documents per-stratum parameters. Planner uses CONTEXT.md IMG-06 locked table + RESEARCH §Stratification Table directly. |
| GLM-4.6V confidence parser (`_parse_vision_response` regex) | utility | transform | Greenfield — no existing code parses GLM-4.6V confidence scores. RESEARCH §Confidence score parsing documents the regex (`置信度.*?([0-9.]+)` / `confidence.*?([0-9.]+)`); default 0.5 flags as low-confidence. |

## Metadata

**Analog search scope:**
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/dreamina_gen_image.py` (full read, 199 lines — CLI subprocess base for dreamina_manager)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/jimeng.py` (full read, 393 lines — degrade envelope + retry pattern)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/plugin.yaml` (full read, 12 lines — manifest pattern)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/tools.py` (full read, 355 lines — tool dispatch pattern)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_jimeng.py` (targeted read, lines 1-120 — httpx.MockTransport test pattern)
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/__init__.py` (full read, 71 lines — ctx.register_cli_command exact twin)
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/cli.py` (full read, 349 lines — Rich table + argparse + JSON output twin for dreamina_stats)
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/queue.py` (full read, 311 lines — JSONL ring buffer + atomic rewrite)
- `/data/workspace/kais-hermes-skills/plugins/platform_metrics/schema.py` (targeted read, lines 1-120 — Pydantic v2 BaseModel + field_validator pattern)
- `/data/workspace/hermes-agent/tools/vision_tools.py` (targeted reads: lines 1-200, 200-350, 400-520, 950-1030 — async_call_llm(task="vision") pattern + base64 data URL + MIME detection)
- `/data/workspace/hermes-agent/agent/auxiliary_client.py` (targeted read, lines 6000-6120 — async_call_llm signature verification, CRITICAL CORRECTION: no prefer_vision parameter)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py` (full read first 180 lines — XCUT-02 injection target)
- `/data/workspace/kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/references/batch-generation-quality-control.md` (targeted read, lines 1-80 — ref-authoring pattern + dreamina CLI subprocess.Popen template)
- `/data/workspace/hermes-agent/.planning/phases/70-foundation-audit/70-smoke.sh` (full read, 80 lines — smoke skeleton)
- `/data/workspace/hermes-agent/.planning/phases/72-dub/72-PATTERNS.md` (full read — XCUT-02 _INSTRUCTION precedent + smoke assertion drafting pattern)
- `/data/workspace/hermes-agent/.planning/phases/71-form/71-PATTERNS.md` (full read — XCUT-02 _INSTRUCTION precedent + goal-content assertion pattern)
- `grep -n "async_call_llm\|prefer_vision\|task=\"vision\"" tools/vision_tools.py + agent/auxiliary_client.py` (CRITICAL CORRECTION verification — prefer_vision does not exist; task="vision" is the routing mechanism)

**Files scanned:** 15 primary reads + 2 grep verification probes
**Pattern extraction date:** 2026-07-09
