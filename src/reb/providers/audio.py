"""Interview audio -> transcript (optional `faster-whisper`; handles Arabic and Turkish).

Transcripts are testimony. Speaker diarization is not performed in v0.
"""

from __future__ import annotations

from pathlib import Path

from . import Extraction, FactDraft


def extract(path: Path, language: str | None = None) -> Extraction:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return Extraction(
            provider="whisper",
            limitations=[
                "Audio not transcribed: install the 'audio' extra (pip install reb-agents[audio]) "
                "or ingest a .txt transcript instead."
            ],
            facts=[FactDraft(fact="Interview audio (not transcribed).", operation="inventory_audio")],
        )
    model = WhisperModel("small", device="auto", compute_type="int8")
    segments, info = model.transcribe(str(path), language=language)
    lines = []
    for seg in segments:
        m, s = divmod(int(seg.start), 60)
        lines.append(f"[{m:02d}:{s:02d}] {seg.text.strip()}")
    text = "\n".join(lines)
    limitations = [
        "Machine transcript: names, numbers and dialect terms may be misheard; check against audio.",
        "No speaker diarization.",
    ]
    return Extraction(
        provider="whisper",
        text=text,
        limitations=limitations,
        facts=[
            FactDraft(
                fact=f"Interview transcribed ({info.language}, {info.duration:.0f}s, {len(lines)} segments).",
                operation="transcribe_audio",
                normalized={"language": info.language, "duration_s": info.duration, "segments": len(lines)},
                limitations=limitations,
            )
        ],
    )
