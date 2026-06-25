# Phase 36: Memory Ingestion (USER.md + 124 .md → mem0) - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure-phase classification)
**Source file count correction:** ROADMAP/STATE.md said "133 .md files" but actual count is **124** (verified via `find ~/.openclaw/workspace/memory -name "*.md" | wc -l`). Plan must use 124, not 133.

<domain>
## Phase Boundary

Migrate USER.md and batch-ingest 124 openclaw memory .md files (~817KB total) into hermes-agent's mem0 backend, with idempotent re-ingest. Plus 5-query spot-check.

**Source files (read-only inputs):**
- `~/.openclaw/workspace/USER.md` — Kai's personal identity profile (~2KB)
- `~/.openclaw/workspace/memory/*.md` — 124 daily-notes/memory files (~817KB total, dates ranging from 2025-06 to 2026-06)

**Target outputs:**
- `~/.hermes/memories/USER.md` (operator-state, new — migrated with openclaw-origin frontmatter)
- mem0 backend entries for all 124 memory files (operator-state, cloud)
- `plugins/memory/mem0/scripts/batch_ingest.py` (repo-commit, new — idempotent ingestion tool)
- `plugins/memory/mem0/scripts/spot_check.py` (repo-commit, new — 5-query verification tool)
- `.planning/phases/36-memory-ingestion-user-md-133-md-mem0/36-01-INGESTION-NOTE.md` (repo-commit, audit trail)

**Critical operator-config dependency:** `MEM0_API_KEY` is NOT currently set in `~/.hermes/.env` and `~/.hermes/mem0.json` does not exist. Cloud mem0 backend is unconfigured. The plan MUST:
- Build complete tooling (batch_ingest.py + spot_check.py)
- Run the parts that don't need the API (USER.md migration, file inventory)
- Defer actual ingestion to operator (run `batch_ingest.py` after configuring MEM0_API_KEY)
- Document this clearly in INGESTION-NOTE.md so Phase 37 validation + Kai know the dependency

</domain>

<decisions>
## Implementation Decisions

### Smart Discuss Auto-Accept (Infrastructure Classification)

Phase 36 was classified as **infrastructure** (migration keywords, technical SCs, batch tooling). All implementation at Claude's discretion within ROADMAP SC constraints.

### Key Design Decisions

1. **USER.md migration (MEM-01):**
   - Target: `~/.hermes/memories/USER.md` (create `~/.hermes/memories/` dir if missing)
   - Add frontmatter: `openclaw-origin: true`, `migrated-at: 2026-06-25`, `source-path: ~/.openclaw/workspace/USER.md`
   - Preserve body byte-for-byte from openclaw source

2. **Batch ingestion tooling (MEM-02):**
   - New file: `plugins/memory/mem0/scripts/batch_ingest.py` (or under `scripts/` flat — match existing repo style)
   - Iterate over `~/.openclaw/workspace/memory/*.md` (124 files)
   - For each file:
     - Compute SHA-256 content hash
     - Check mem0 backend for existing entry with matching `metadata.content_hash` (idempotency key)
     - If absent: call `MemoryClient.add(messages=[{"role": "user", "content": file_contents}], filters={user_id, agent_id}, metadata={"content_hash": ..., "source_path": ..., "migrated_at": "2026-06-25"})`
     - If present: skip (no duplicate)
   - Print summary: N ingested / M skipped / total
   - Exit code 0 on success, non-zero on partial failure
   - Circuit-breaker aware: respect existing plugin's breaker pattern

3. **Idempotency mechanism (MEM-04):**
   - Keyed on SHA-256 content hash + source_path stored in mem0 metadata
   - Re-running batch_ingest.py produces zero new entries if all files unchanged
   - Detection via mem0 search with metadata filter (if supported) or via get_all + filter locally

4. **Spot-check tooling (MEM-03):**
   - New file: `plugins/memory/mem0/scripts/spot_check.py`
   - 5 hardcoded sample queries covering: AIGC deployment, ComfyUI, Trellis, ACE-Step, CosyVoice
   - Each query: call `MemoryClient.search(query=..., filters={user_id}, rerank=True, top_k=3)`
   - Print query + top-3 results + relevance assessment
   - Operator runs this manually after batch_ingest succeeds

5. **Operator-action-required documentation:**
   - `.planning/phases/36-memory-ingestion-user-md-133-md-mem0/36-01-INGESTION-NOTE.md` documents:
     - The 124-file inventory (with file list + total bytes)
     - The MEM0_API_KEY configuration step operator must complete
     - The exact command to run: `python3 plugins/memory/mem0/scripts/batch_ingest.py`
     - The spot-check command: `python3 plugins/memory/mem0/scripts/spot_check.py`
     - Expected outcomes for SC verification

### Claude's Discretion

- Exact script argument interface (--dry-run, --limit N for testing)
- Whether to add `pip install mem0ai` to setup script or document as prerequisite
- Whether to add a pytest smoke test for the script's helpers (hash, filter logic)
- Error handling granularity (skip-and-continue vs fail-fast)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `plugins/memory/mem0/__init__.py` — Mem0Provider class with `_get_client()`, `_load_config()`, `_read_filters()`, `_write_filters()`, circuit-breaker pattern. Batch scripts should reuse this (import the provider) rather than duplicate config logic.
- `agent/memory_provider.py` — MemoryProvider ABC defines the interface contract
- `~/.openclaw/workspace/USER.md` — source for USER.md migration
- `~/.openclaw/workspace/memory/*.md` — 124 source files (~817KB total)

### Established Patterns

- Hermes plugins may include `scripts/` subdir (saw similar pattern in skills/openclaw-skills-tmux-agents/scripts/ during Phase 34)
- Operator-state files (under `~/.hermes/`) are NOT repo-tracked — only tooling under `plugins/` and notes under `.planning/` get committed
- Python scripts use `from __future__ import annotations` + explicit `encoding="utf-8"` on open() per CLAUDE.md

### Integration Points

- `mem0ai` package must be installed for the scripts to run (currently NOT installed per import test)
- Scripts use `MemoryClient` from mem0ai directly (not the provider wrapper) for batch operations — simpler than going through the plugin's per-turn lifecycle
- Scripts read MEM0_API_KEY via env var OR `~/.hermes/mem0.json` (same precedence as plugin)

</code_context>

<specifics>
## Specific Ideas

- **FILE COUNT CORRECTION:** ROADMAP.md SC #2 says "133 openclaw workspace/memory/*.md files" — actual count is **124**. INGESTION-NOTE.md must explicitly call out this correction; SC #2 effectively becomes "124 files" (or operator-configured subset if partial-ingest decision is made and documented).
- **TOTAL BYTES:** 817KB, not 1.3MB as ROADMAP stated. (~37% smaller than estimated.)
- **Sample queries for MEM-03 spot-check** (5 topics named in SC):
  1. AIGC deployment (e.g., "ComfyUI systemd 配置" or "RTX 3090 GPU 部署")
  2. ComfyUI (e.g., "ComfyUI 工作流参数" or "ComfyUI CUDA_VISIBLE_DEVICES")
  3. Trellis (e.g., "Trellis 项目结构" or "Trellis 测试")
  4. ACE-Step (e.g., "ACE-Step 音频生成")
  5. CosyVoice (e.g., "CosyVoice TTS 模型")

</specifics>

<deferred>
## Deferred Ideas

- mem0ai package auto-installation via setup script — deferred (operator pip install mem0ai explicitly)
- Vector embedding local fallback (no cloud dependency) — deferred; cloud mem0 is the v7.0 choice
- Memory curation/deduplication beyond content-hash — deferred (mem0 platform does server-side dedup)
- Multi-user memory scoping — deferred (single-user for v7.0)
- ACP/auth-profiles memory migration — explicitly OUT of v7.0 scope per ROADMAP

</deferred>
