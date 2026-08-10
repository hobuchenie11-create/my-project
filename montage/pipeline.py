#!/usr/bin/env python3
"""automontage — raw video in, edited video out.

Wires OpenMontage's tool layer to Remotion in one deterministic pipeline:

    probe -> analyze -> transcribe -> select -> cut -> stitch -> finish

OpenMontage ships the analysis/cutting tools and the Remotion bridge; Remotion
(vendored under engine/OpenMontage/remotion-composer) renders the animated
captions and title overlays. This module is the glue that makes the two run
end to end without a human in the loop.

Selection ("what stays in the cut") has two backends:

  auto  heuristic over speech segments — no network, no API key, always works.
  llm   Claude reads the transcript and picks the beats. Needs ANTHROPIC_API_KEY.

Captions are optional: they need a Whisper model, which is downloaded on first
run. Everything else works offline.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    PROJECT_ROOT, Stage, library_path, log, prepare_remotion_env, probe_media,
    require_binaries, require_engine, write_manifest,
)

require_engine()


def mean_volume_db(path: Path, start: float, end: float) -> float:
    """Mean loudness of one span, in dBFS. Used to rank segments by energy.

    Decodes audio only, so this stays cheap even on long sources. Silence and
    decode failures both fall back to a very low value so those spans sort last.
    """
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-nostats",
         "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(path),
         "-vn", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", proc.stderr)
    return float(match.group(1)) if match else -91.0


# --------------------------------------------------------------------------- #
#  Segment model
# --------------------------------------------------------------------------- #

@dataclass
class Segment:
    """A candidate span of the source video, in source-timeline seconds."""
    start: float
    end: float
    text: str = ""
    energy_db: float = -91.0
    score: float = 0.0

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Timeline:
    """Selected segments plus the mapping back onto the edited timeline.

    `offsets[i]` is where segment i begins in the *output* video. With a
    crossfade the clips overlap, so each successive clip starts
    `transition_duration` earlier than a naive sum would suggest — captions
    would drift without this correction.
    """
    segments: list[Segment]
    transition: str
    transition_duration: float
    offsets: list[float] = field(default_factory=list)

    def compute_offsets(self) -> None:
        overlap = self.transition_duration if self.transition != "cut" else 0.0
        self.offsets = []
        cursor = 0.0
        for i, seg in enumerate(self.segments):
            self.offsets.append(max(0.0, cursor - i * overlap))
            cursor += seg.duration

    @property
    def output_duration(self) -> float:
        if not self.segments:
            return 0.0
        overlap = self.transition_duration if self.transition != "cut" else 0.0
        total = sum(s.duration for s in self.segments)
        return max(0.0, total - overlap * (len(self.segments) - 1))

    def map_time(self, t: float) -> float | None:
        """Map a source-timeline instant onto the edited timeline.

        Returns None when the instant falls in material that was cut.
        """
        for seg, offset in zip(self.segments, self.offsets):
            if seg.start <= t <= seg.end:
                return offset + (t - seg.start)
        return None


# --------------------------------------------------------------------------- #
#  Stage 2 — find the speech
# --------------------------------------------------------------------------- #

def find_speech_segments(
    src: Path, duration: float, work: Path,
    threshold_db: float, min_silence: float, padding: float,
) -> list[Segment]:
    """Use OpenMontage's SilenceCutter in 'mark' mode to locate speech spans."""
    from tools.video.silence_cutter import SilenceCutter

    result = SilenceCutter().execute({
        "input_path": str(src),
        "output_path": str(work / "silence.json"),
        "mode": "mark",
        "silence_threshold_db": threshold_db,
        "min_silence_duration": min_silence,
        "padding_seconds": padding,
    })

    if not result.success:
        log(f"silence detection failed ({result.error}); treating whole file as one take")
        return [Segment(0.0, duration)]

    # In 'mark' mode the tool's `data` carries only counts; the actual spans are
    # written to the JSON artifact it reports under `output`. When no silence at
    # all is detected the tool returns early without writing that file.
    report = result.data.get("output")
    spans: list[dict] = []
    if report and Path(report).exists():
        spans = json.loads(Path(report).read_text(encoding="utf-8")).get("speech_segments", [])

    if not spans:
        log("no silence found; treating whole file as one take")
        return [Segment(0.0, duration)]

    return [Segment(float(s["start"]), float(s["end"])) for s in spans]


# --------------------------------------------------------------------------- #
#  Stage 3 — transcribe (optional)
# --------------------------------------------------------------------------- #

def transcribe(src: Path, work: Path, model_size: str, language: str | None) -> list[dict]:
    """Word-level transcript via OpenMontage's faster-whisper wrapper.

    Returns [] and explains itself on failure — the montage still renders, just
    without captions, so a missing model must not kill the run.
    """
    from tools.analysis.transcriber import Transcriber

    inputs = {
        "input_path": str(src),
        "model_size": model_size,
        "output_dir": str(work / "transcript"),
    }
    if language:
        inputs["language"] = language

    try:
        result = Transcriber().execute(inputs)
    except Exception as exc:  # model download / backend failures
        log(f"transcription unavailable: {type(exc).__name__}: {exc}")
        return []

    if not result.success:
        log(f"transcription failed: {result.error}")
        return []

    segments = result.data.get("segments") or []
    words = sum(len(s.get("words") or []) for s in segments)
    log(f"transcribed {len(segments)} segments / {words} words")
    return segments


def attach_transcript(segments: list[Segment], transcript: list[dict]) -> None:
    """Give each candidate segment the transcript text that overlaps it."""
    for seg in segments:
        parts = [
            (t.get("text") or "").strip()
            for t in transcript
            if float(t.get("end", 0)) > seg.start and float(t.get("start", 0)) < seg.end
        ]
        seg.text = " ".join(p for p in parts if p)


# --------------------------------------------------------------------------- #
#  Stage 4 — selection
# --------------------------------------------------------------------------- #

def select_auto(segments: list[Segment], src: Path, target: float | None) -> list[Segment]:
    """Rank segments by loudness and length, keep the best until target is hit.

    The intuition: a segment that is both sustained and well-articulated is
    usually the part worth keeping, while short quiet fragments are throat-
    clearing between takes.
    """
    for seg in segments:
        seg.energy_db = mean_volume_db(src, seg.start, seg.end)

    loudest = max((s.energy_db for s in segments), default=-91.0)
    for seg in segments:
        # Loudness relative to the loudest moment, squashed into roughly 0..1.
        rel = max(0.0, 1.0 + (seg.energy_db - loudest) / 30.0)
        length = min(seg.duration / 6.0, 1.0)
        seg.score = 0.6 * length + 0.4 * rel

    if target is None:
        return sorted(segments, key=lambda s: s.start)

    kept: list[Segment] = []
    total = 0.0
    for seg in sorted(segments, key=lambda s: s.score, reverse=True):
        if total >= target:
            break
        kept.append(seg)
        total += seg.duration

    if not kept:
        kept = [max(segments, key=lambda s: s.duration)]

    return sorted(kept, key=lambda s: s.start)


def select_llm(
    segments: list[Segment], target: float | None, brief: str, model: str,
) -> tuple[list[Segment], str]:
    """Let Claude act as the editor: it reads the transcript and picks beats.

    Returns the kept segments and a suggested on-screen title.

    Falls back to the caller on any failure — an unavailable API key should
    degrade to the heuristic, never abort the montage.
    """
    import anthropic

    catalogue = [
        {"index": i, "start": round(s.start, 2), "end": round(s.end, 2),
         "duration": round(s.duration, 2), "text": s.text or "(no speech detected)"}
        for i, s in enumerate(segments)
    ]

    goal = (
        f"The finished cut should run about {target:.0f} seconds."
        if target else
        "Keep everything that earns its place; drop filler, false starts and rambling."
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=8000,
        system=(
            "You are a video editor choosing which segments of a raw recording "
            "survive into the final cut. Keep the strongest, clearest moments and "
            "preserve a coherent narrative order. Never reorder segments."
        ),
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "keep": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Indices of segments to keep, ascending.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Short on-screen title for the finished video.",
                        },
                        "reasoning": {"type": "string"},
                    },
                    "required": ["keep", "title", "reasoning"],
                    "additionalProperties": False,
                },
            }
        },
        messages=[{
            "role": "user",
            "content": (
                f"Brief: {brief or 'general-purpose edit'}\n{goal}\n\n"
                f"Segments:\n{json.dumps(catalogue, indent=2)}"
            ),
        }],
    )

    text = next(b.text for b in response.content if b.type == "text")
    verdict = json.loads(text)

    keep = [i for i in verdict["keep"] if 0 <= i < len(segments)]
    if not keep:
        raise ValueError("model returned no usable segment indices")

    log(f"editor's note: {verdict['reasoning'][:200]}")
    return [segments[i] for i in sorted(set(keep))], verdict.get("title", "")


# --------------------------------------------------------------------------- #
#  Stages 5 & 6 — cut and stitch
# --------------------------------------------------------------------------- #

def cut_segments(src: Path, timeline: Timeline, work: Path) -> list[Path]:
    """Extract each kept segment with OpenMontage's VideoTrimmer."""
    from tools.video.video_trimmer import VideoTrimmer

    clips_dir = work / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    trimmer = VideoTrimmer()
    paths: list[Path] = []

    for i, seg in enumerate(timeline.segments):
        out = clips_dir / f"clip_{i:03d}.mp4"
        result = trimmer.execute({
            "operation": "cut",
            "input_path": str(src),
            "output_path": str(out),
            "start_seconds": seg.start,
            "end_seconds": seg.end,
            # Re-encode rather than stream-copy: copy snaps cuts to keyframes,
            # which would desync every caption downstream.
            "codec": "libx264",
        })
        if not result.success or not out.exists():
            raise SystemExit(f"Failed to cut segment {i}: {result.error}")
        paths.append(out)
        log(f"clip {i + 1}/{len(timeline.segments)}  "
            f"{seg.start:7.2f}s → {seg.end:7.2f}s  ({seg.duration:.2f}s)")

    return paths


def stitch(clips: list[Path], timeline: Timeline, work: Path, meta: dict) -> Path:
    """Concatenate the clips, applying the chosen transition."""
    from tools.video.video_stitch import VideoStitch

    out = work / "stitched.mp4"

    if len(clips) == 1:
        shutil.copy(clips[0], out)
        return out

    result = VideoStitch().execute({
        "operation": "stitch",
        "clips": [str(c) for c in clips],
        "output_path": str(out),
        "transition": timeline.transition,
        "transition_duration": timeline.transition_duration,
        "auto_normalize": True,
        "target_resolution": f"{meta['width']}x{meta['height']}",
        "target_fps": int(round(meta["fps"])),
    })
    if not result.success or not out.exists():
        raise SystemExit(f"Stitch failed: {result.error}")
    return out


# --------------------------------------------------------------------------- #
#  Stage 7 — captions and titles via Remotion
# --------------------------------------------------------------------------- #

def remap_transcript(transcript: list[dict], timeline: Timeline) -> list[dict]:
    """Rewrite word timings from the source timeline onto the edited one.

    Words whose source instant landed in cut material are dropped, so captions
    stay locked to the audio that actually survived.
    """
    remapped: list[dict] = []

    for entry in transcript:
        words = []
        for word in entry.get("words") or []:
            start = timeline.map_time(float(word["start"]))
            end = timeline.map_time(float(word["end"]))
            if start is None or end is None or end <= start:
                continue
            words.append({"word": word["word"], "start": start, "end": end})
        if words:
            remapped.append({
                "start": words[0]["start"],
                "end": words[-1]["end"],
                "text": " ".join(w["word"] for w in words),
                "words": words,
            })

    return remapped


def build_overlays(title: str, outro: str, duration: float) -> list[dict]:
    """Title card in, end tag out — rendered as Remotion components."""
    overlays: list[dict] = []
    if title:
        overlays.append({
            "type": "hero_title",
            "in_seconds": 0.0,
            "out_seconds": min(3.5, duration),
            "position": "full_overlay",
            "text": title,
            "title": title,
        })
    if outro and duration > 4.0:
        overlays.append({
            "type": "text_card",
            "in_seconds": max(0.0, duration - 3.0),
            "out_seconds": duration,
            "position": "lower_third",
            "text": outro,
        })
    return overlays


def finish(
    stitched: Path, out_path: Path, transcript: list[dict], overlays: list[dict],
    font_size: int, highlight: str,
) -> Path:
    """Burn animated captions + overlays with OpenMontage's Remotion bridge.

    The bridge falls back to FFmpeg subtitle burn if Remotion can't run, so this
    stage degrades instead of failing.
    """
    from tools.video.remotion_caption_burn import RemotionCaptionBurn

    if not transcript and not overlays:
        shutil.copy(stitched, out_path)
        log("nothing to overlay; using the stitched cut as-is")
        return out_path

    tool = RemotionCaptionBurn()

    if transcript:
        result = tool.execute({
            "input_path": str(stitched),
            "output_path": str(out_path),
            "segments": transcript,
            "overlays": overlays,
            "font_size": font_size,
            "highlight_color": highlight,
            "words_per_page": 4,
        })
    else:
        # execute() rejects a call with no captions, but titles alone are a
        # legitimate edit. The renderer underneath handles an empty caption
        # list fine, so drive it directly — guarded, in case upstream renames it.
        if not hasattr(tool, "_render_remotion"):
            shutil.copy(stitched, out_path)
            log("caption tool cannot render overlays alone; using the clean cut")
            return out_path
        result = tool._render_remotion(
            input_path=str(stitched),
            output_path=str(out_path),
            captions=[],
            words_per_page=4,
            font_size=font_size,
            highlight_color=highlight,
            overlays=overlays,
        )

    if not result.success or not out_path.exists():
        log(f"overlay render failed ({result.error}); falling back to the clean cut")
        shutil.copy(stitched, out_path)
        return out_path

    log(f"rendered via {result.data.get('method', 'remotion')}")
    return out_path


# --------------------------------------------------------------------------- #
#  Environment
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="automontage",
        description="Turn a raw video file into an edited, captioned cut.",
    )
    parser.add_argument("input", type=Path, help="source video file")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="exact output path; default lands in output/")
    parser.add_argument("--label", default="", help="name for the file in output/")
    parser.add_argument("--target", type=float, default=None,
                        help="approximate length of the finished cut, in seconds")
    parser.add_argument("--select", choices=["auto", "llm", "all"], default="auto",
                        help="auto=heuristic (default), llm=Claude picks, all=only drop silence")
    parser.add_argument("--brief", default="",
                        help="creative direction for --select llm")
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("--title", default="", help="opening title card text")
    parser.add_argument("--outro", default="", help="closing lower-third text")
    parser.add_argument("--captions", choices=["auto", "off"], default="auto")
    parser.add_argument("--transcript", type=Path, default=None,
                        help="use this transcript JSON instead of running Whisper; "
                             "either a list of segments or {\"segments\": [...]}, each with "
                             "word-level {word,start,end} entries in source-video seconds")
    parser.add_argument("--whisper-model", default="base",
                        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"])
    parser.add_argument("--language", default=None, help="ISO 639-1 code; omit to auto-detect")
    parser.add_argument("--transition", choices=["cut", "crossfade", "fade"], default="crossfade")
    parser.add_argument("--transition-duration", type=float, default=0.4)
    parser.add_argument("--silence-threshold", type=float, default=-35.0)
    parser.add_argument("--min-silence", type=float, default=0.6)
    parser.add_argument("--padding", type=float, default=0.12)
    parser.add_argument("--font-size", type=int, default=52)
    parser.add_argument("--highlight", default="#22D3EE")
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--keep-work", action="store_true",
                        help="keep intermediate clips for inspection")
    args = parser.parse_args()

    src = args.input.expanduser().resolve()
    if not src.exists():
        sys.exit(f"Input not found: {src}")

    require_binaries()
    prepare_remotion_env()

    label = args.label or args.title or src.stem
    out_path = (args.output.expanduser().resolve() if args.output
                else library_path(label))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work = (args.work_dir or PROJECT_ROOT / ".montage-work" / str(int(time.time()))).resolve()
    work.mkdir(parents=True, exist_ok=True)

    started = time.time()
    stage = Stage(7)

    # 1 — probe --------------------------------------------------------------
    stage("Probing source")
    meta = probe_media(src)
    log(f"{meta['width']}x{meta['height']} @ {meta['fps']}fps, "
        f"{meta['duration']:.2f}s, audio={'yes' if meta['has_audio'] else 'no'}")

    # 2 — analyse ------------------------------------------------------------
    stage("Detecting speech")
    if meta["has_audio"]:
        segments = find_speech_segments(
            src, meta["duration"], work,
            args.silence_threshold, args.min_silence, args.padding,
        )
    else:
        log("no audio track; keeping the whole file as one segment")
        segments = [Segment(0.0, meta["duration"])]
    speech_total = sum(s.duration for s in segments)
    log(f"{len(segments)} speech segments, {speech_total:.2f}s of {meta['duration']:.2f}s")

    # 3 — transcribe ---------------------------------------------------------
    stage("Transcribing")
    transcript: list[dict] = []
    if args.captions == "off" or not meta["has_audio"]:
        log("captions disabled")
    elif args.transcript:
        raw = json.loads(args.transcript.read_text(encoding="utf-8"))
        transcript = raw.get("segments", []) if isinstance(raw, dict) else raw
        log(f"loaded {len(transcript)} segments from {args.transcript}")
        attach_transcript(segments, transcript)
    else:
        transcript = transcribe(src, work, args.whisper_model, args.language)
        if transcript:
            attach_transcript(segments, transcript)

    # 4 — select -------------------------------------------------------------
    stage("Choosing the cut")
    title = args.title

    if args.select == "all":
        chosen = sorted(segments, key=lambda s: s.start)
        log(f"keeping all {len(chosen)} speech segments")
    elif args.select == "llm":
        try:
            chosen, suggested = select_llm(segments, args.target, args.brief, args.model)
            title = title or suggested
            log(f"Claude kept {len(chosen)} of {len(segments)} segments")
        except Exception as exc:
            log(f"LLM selection unavailable ({type(exc).__name__}: {exc})")
            log("falling back to the heuristic selector")
            chosen = select_auto(segments, src, args.target)
    else:
        chosen = select_auto(segments, src, args.target)
        log(f"kept {len(chosen)} of {len(segments)} segments")

    timeline = Timeline(chosen, args.transition, args.transition_duration)
    timeline.compute_offsets()
    log(f"edited length ≈ {timeline.output_duration:.2f}s")

    # 5 — cut ----------------------------------------------------------------
    stage("Cutting clips")
    clips = cut_segments(src, timeline, work)

    # 6 — stitch -------------------------------------------------------------
    stage(f"Stitching ({timeline.transition})")
    stitched = stitch(clips, timeline, work, meta)
    log(f"{probe_media(stitched)['duration']:.2f}s")

    # 7 — captions + titles --------------------------------------------------
    stage("Rendering captions and titles")
    edited_transcript = remap_transcript(transcript, timeline) if transcript else []
    if transcript and not edited_transcript:
        log("no transcript words survived the cut; skipping captions")
    overlays = build_overlays(title, args.outro, probe_media(stitched)["duration"])
    finish(stitched, out_path, edited_transcript, overlays, args.font_size, args.highlight)

    final = probe_media(out_path)
    write_manifest(out_path, {
        "source": str(src),
        "source_duration_seconds": round(meta["duration"], 2),
        "select_mode": args.select,
        "target_seconds": args.target,
        "segments_kept": len(timeline.segments),
        "segments_found": len(segments),
        "cuts": [{"start": round(s.start, 2), "end": round(s.end, 2)}
                 for s in timeline.segments],
        "transition": f"{timeline.transition} {timeline.transition_duration}s",
        "caption_lines": len(edited_transcript),
        "title": title or None,
        "resolution": f"{final['width']}x{final['height']}",
        "duration_seconds": round(final["duration"], 2),
    })

    print(
        f"\n✅ {out_path}\n"
        f"   {final['width']}x{final['height']} @ {final['fps']}fps · "
        f"{final['duration']:.2f}s "
        f"(from {meta['duration']:.2f}s) · {out_path.stat().st_size / 1e6:.1f} MB\n"
        f"   {len(timeline.segments)} segments · "
        f"{len(edited_transcript)} caption lines · {time.time() - started:.0f}s elapsed"
    )

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"   intermediates: {work}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
