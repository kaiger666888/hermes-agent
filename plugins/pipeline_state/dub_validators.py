"""dub_validators.py — DUB-03 voice clone reference wav validation helpers.

Phase 72-01 module providing ``validate_voice_clone_ref(path)`` for the DUB-03
contract: CosyVoice clone mode requires a 3-10s clean wav at >=16kHz sample
rate. This helper enforces the rule at fail-fast time (called from
``tts_batch.generate_tts`` before submitting to ComfyUI AIIA_CosyVoice_TTS).

Design decisions:
- Sibling module to ``store.py`` (kept separate so store.py stays focused on
  state I/O per RESEARCH assumption A7).
- Uses stdlib ``wave`` module only (no pydub / librosa — CLAUDE.md "no new deps").
- Per CLAUDE.md Code Style: ``from __future__ import annotations`` + PEP 604
  unions (``str | Path``) + Ruff PLW1514 compliant (explicit encoding on open
  not needed — stdlib wave manages file handles internally).
"""

from __future__ import annotations

import contextlib
import wave
from pathlib import Path


def validate_voice_clone_ref(path: str | Path) -> tuple[float, int]:
    """Validate a ``voice_clone_reference_wav`` file meets DUB-03 requirements.

    Acceptance rules:
      - File exists at the given path.
      - Format is wav (readable by stdlib ``wave`` — non-wav raises ``wave.Error``).
      - Mono channel (nchannels == 1) — CosyVoice reference_audio expects mono;
        stereo wavs may produce unexpected results (per p04:76 "mono, >=16kHz").
      - Duration in [3.0, 10.0] seconds.
      - Sample rate >= 16000 Hz.

    Args:
        path: Absolute or relative path to the wav file. Typically resolves to
            ``assets/voice_refs/<character>.wav`` (operator-sourced).

    Returns:
        ``(duration_sec, sample_rate_hz)`` tuple on success.

    Raises:
        FileNotFoundError: path does not exist. Message includes the
            "Operator action" suffix per DUB-03 operator-actionable contract
            (CONTEXT.md locked decision — no silent fallback to generic voice).
        ValueError: format not wav, not mono, duration outside 3-10s, or
            sample_rate < 16kHz. Messages include the specific rule violated
            with a "(DUB-03 — ...)" suffix for grep-auditable traceability.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"voice_clone_reference_wav missing for path={path}. "
            f"Operator action: provide 3-10s clean sample at <path>. "
            f"See DUB phase operator-action checklist. (DUB-03)"
        )

    try:
        with contextlib.closing(wave.open(str(p), "rb")) as wf:
            n_frames = wf.getnframes()
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
    except wave.Error as exc:
        raise ValueError(
            f"voice_clone_reference_wav at {path} is not a valid wav format "
            f"(wave.Error: {exc}). (DUB-03 — non-wav format rejected)"
        ) from exc

    if sample_rate <= 0:
        raise ValueError(
            f"voice_clone_reference_wav at {path} has invalid sample_rate="
            f"{sample_rate}Hz. (DUB-03 — non-wav format rejected)"
        )

    if n_channels != 1:
        raise ValueError(
            f"voice_clone_reference_wav at {path} must be mono (1 channel), "
            f"got {n_channels} channels. "
            f"(DUB-03 — CosyVoice reference_audio expects mono per p04:76)"
        )

    duration = n_frames / sample_rate

    if not (3.0 <= duration <= 10.0):
        raise ValueError(
            f"voice_clone_reference_wav duration must be 3-10s, got "
            f"{duration:.2f}s. (DUB-03 — 3-10s clean wav at >=16kHz required)"
        )

    if sample_rate < 16000:
        raise ValueError(
            f"voice_clone_reference_wav sample_rate must be in [16kHz, 48kHz], "
            f"got {sample_rate}Hz (below 16kHz floor). "
            f"(DUB-03 — 3-10s clean mono wav at 16-48kHz required)"
        )

    if sample_rate > 48000:
        # WR-06: upper bound. A 10s@192kHz wav is ~7.6MB and likely a poorly-
        # downsampled reference; CosyVoice resamples internally anyway. Reject
        # so the operator gets an actionable error rather than a slow upload.
        raise ValueError(
            f"voice_clone_reference_wav sample_rate must be in [16kHz, 48kHz], "
            f"got {sample_rate}Hz (above 48kHz ceiling). "
            f"(DUB-03 — downsample to <=48kHz before submitting; "
            f"CosyVoice resamples internally anyway)"
        )

    return duration, sample_rate
