# GAP-REPORT: voicer

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected by scanner (CosyVoice model name is in `_shared/known-external-models.yaml` allowlist).

**Manual review note:** SKILL.md hardcodes `CosyVoice-300M (preview)` / `CosyVoice-300M-SFT` which are v1-era model IDs from 2024. Research SUMMARY §"What NOT to use": "CosyVoice-300M (preview) / CosyVoice-300M-SFT — v1 model IDs from 2024; latest is CosyVoice 3.0." These are not phantoms (CosyVoice is a real model family) but the version is STALE. Rewrite in Phase 5 to reference CosyVoice 3.0 (current SOTA) and MiniMax / ElevenLabs as Hermes-native alternatives.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Hermes-native TTS alternatives.** Research SUMMARY: Hermes ships MiniMax, ElevenLabs, Mistral Voxtral, Gemini, Edge, NeuTTS. SKILL.md only covers CosyVoice (user-deployed external). No Hermes-native TTS selection guidance.
2. **CosyVoice deployment path.** CosyVoice 3.0 requires local deployment outside Hermes. No deployment doc reference (research SUMMARY: "document in voicer/references/cosyvoice-deployment.md").
3. **CN 短剧 voice acting conventions.** 短剧 voice acting is heightened / dramatized compared to naturalistic film. No 短剧-specific emotion_strength calibration.
4. **Multi-character voice consistency across episodes.** 短剧 spans 10-80 episodes; character voice must remain stable. No multi-episode voice profile persistence protocol.
5. **Dialect / regional accent support.** CN 短剧 often uses regional dialects (东北话, 四川话, 粤语). No dialect handling guidance.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Voice is character"** — principle, not checkable.
2. **`voice_naturalness: >= 0.90`** — high threshold, no measurement protocol (MOS? human-judged? neural MOS predictor?).
3. **`emotion_match: >= 0.85`** — match vs screenplay.emotion_curve? Undefined.
4. **`character_distinctiveness: >= 0.80`** — distinctiveness measured across how many characters? Undefined baseline.
5. **`speaker_embedding: character-specific vector (3-5 reference samples)`** — no guidance on optimal sample selection (emotion diversity, recording quality, duration distribution).

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `voice_naturalness` — >= 0.90. No measurement protocol.
- `emotion_match` — >= 0.85. No measurement protocol.
- `character_distinctiveness` — >= 0.80. No measurement protocol.
- `prosody_naturalness` — >= 0.85. No measurement protocol (note: this metric is in Quality Thresholds table but NOT in frontmatter `metrics:` list — inconsistency).

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/cosyvoice-deployment.md` — CosyVoice 3.0 local deployment guide, API surface, GPU requirements, Docker setup.
2. `references/hermes-tts-selection-matrix.md` — MiniMax vs ElevenLabs vs CosyVoice vs Voxtral vs Gemini vs Edge vs NeuTTS selection by use case (CN emotion, voice cloning, multilingual).
3. `references/cn-shortdrama-voice-conventions.md` — 短剧 voice acting intensity conventions, emotion_strength calibration by genre.
4. `references/dialect-and-accent-support.md` — CN regional dialect TTS capability matrix per provider.
