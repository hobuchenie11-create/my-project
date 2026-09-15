"""Shared plumbing for the video and photo pipelines.

Holds the bits both entry points need: where things live, how a run is logged,
ffprobe wrappers, Remotion's browser resolution, and the output library.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT / "engine" / "OpenMontage"
REMOTION_ROOT = ENGINE_ROOT / "remotion-composer"

# Every finished render is collected here, one file per run, never overwritten.
LIBRARY = PROJECT_ROOT / "output"


def require_engine() -> None:
    if not (ENGINE_ROOT / "tools").is_dir():
        sys.exit(
            f"OpenMontage engine not found at {ENGINE_ROOT}\n"
            f"Run: {PROJECT_ROOT / 'setup.sh'}"
        )
    if str(ENGINE_ROOT) not in sys.path:
        sys.path.insert(0, str(ENGINE_ROOT))


def require_binaries(*extra: str) -> None:
    needed = ["ffmpeg", "ffprobe", "npx", *extra]
    missing = [b for b in needed if not shutil.which(b)]
    if missing:
        sys.exit(f"Missing required binaries: {', '.join(missing)}\n"
                 f"Run: {PROJECT_ROOT / 'setup.sh'}")


# --------------------------------------------------------------------------- #
#  Progress reporting
# --------------------------------------------------------------------------- #

class Stage:
    """Prints a numbered stage banner so a run is auditable as it goes."""

    def __init__(self, total: int) -> None:
        self.n = 0
        self.total = total

    def __call__(self, title: str) -> None:
        self.n += 1
        print(f"\n[{self.n}/{self.total}] {title}", flush=True)


def log(msg: str) -> None:
    print(f"      {msg}", flush=True)


# --------------------------------------------------------------------------- #
#  Media inspection
# --------------------------------------------------------------------------- #

def ffprobe_json(path: Path) -> dict[str, Any]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def probe_media(path: Path) -> dict[str, Any]:
    """Duration / resolution / fps / audio presence."""
    info = ffprobe_json(path)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if video is None:
        raise SystemExit(f"No video stream in {path}")

    fps = 30.0
    raw_fps = video.get("avg_frame_rate") or video.get("r_frame_rate") or "30/1"
    if "/" in raw_fps:
        num, den = raw_fps.split("/")
        if float(den) != 0:
            fps = float(num) / float(den)

    return {
        "duration": float(info["format"]["duration"]),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": round(fps, 3),
        "has_audio": audio is not None,
    }


def media_duration(path: Path) -> float:
    return float(ffprobe_json(path)["format"]["duration"])


def resolve_executable(cmd: list[str]) -> list[str]:
    """Expand a bare command name to a full path on Windows.

    `npx` and `npm` are .cmd shims there, and CreateProcess will not find them
    from a bare name the way a POSIX shell does.
    """
    if os.name == "nt" and cmd:
        found = shutil.which(cmd[0])
        if found:
            return [found, *cmd[1:]]
    return cmd


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None):
    """Run a command, surfacing stderr on failure instead of swallowing it."""
    proc = subprocess.run(
        resolve_executable(cmd),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd) if cwd else None, timeout=timeout,
    )
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise SystemExit(f"Command failed: {' '.join(cmd[:4])} …\n{tail}")
    return proc


# --------------------------------------------------------------------------- #
#  Output library
# --------------------------------------------------------------------------- #

def slugify(text: str, fallback: str = "montage") -> str:
    keep = [c if (c.isalnum() or c in "-_") else "-" for c in text.strip().lower()]
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:60] or fallback


def library_path(label: str, suffix: str = ".mp4") -> Path:
    """A fresh, non-clobbering path inside the output library.

    Named `<date>_<time>_<label>` so the folder sorts chronologically and a new
    render never destroys yesterday's. If two runs land in the same second, a
    counter keeps them apart.
    """
    LIBRARY.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    base = f"{stamp}_{slugify(label)}"

    candidate = LIBRARY / f"{base}{suffix}"
    n = 2
    while candidate.exists():
        candidate = LIBRARY / f"{base}-{n}{suffix}"
        n += 1
    return candidate


def write_manifest(video: Path, data: dict[str, Any]) -> Path:
    """Drop a sidecar JSON next to a render recording how it was made.

    An archive folder is only useful if you can tell later why one cut looks the
    way it does — this is that record.
    """
    manifest = video.with_suffix(".json")
    payload = {"rendered_at": datetime.now().isoformat(timespec="seconds"),
               "output": video.name, **data}
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


# --------------------------------------------------------------------------- #
#  Remotion
# --------------------------------------------------------------------------- #

def prepare_remotion_env() -> None:
    """Point Remotion at a local Chromium when it can't download its own.

    Sandboxes and CI images often block Remotion's Chrome Headless Shell
    download but ship a Chromium already. If none is found we leave the
    environment alone and Remotion downloads as usual.
    """
    if os.environ.get("REMOTION_BROWSER_EXECUTABLE"):
        return

    candidates = [
        *Path("/opt/pw-browsers").glob("chromium_headless_shell-*/chrome-linux/headless_shell"),
        *Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"),
    ]
    for name in ("chromium", "chromium-browser", "google-chrome", "headless_shell"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    for candidate in candidates:
        if candidate.exists():
            os.environ["REMOTION_BROWSER_EXECUTABLE"] = str(candidate)
            os.environ.setdefault("REMOTION_IGNORE_CERT_ERRORS", "1")
            return


def remotion_public(subdir: str) -> Path:
    """A scratch directory under the composer's public/ folder.

    Remotion serves public/ over http during a render; absolute file:// paths
    are blocked by the browser, so assets have to be staged here.
    """
    target = REMOTION_ROOT / "public" / "automontage" / subdir
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    return target


def word_captions(segments: list[dict]) -> list[dict]:
    """Flatten transcriber segments into the WordCaption shape Remotion wants."""
    caps: list[dict] = []
    for seg in segments:
        for w in seg.get("words") or []:
            text = str(w.get("word", "")).strip()
            if not text:
                continue
            caps.append({
                "word": text,
                "startMs": round(float(w["start"]) * 1000),
                "endMs": round(float(w["end"]) * 1000),
            })
    return caps


def render_talking_head(
    video: Path, out_path: Path, *,
    captions: list[dict] | None = None,
    overlays: list[dict] | None = None,
    font_size: int = 52,
    highlight: str = "#22D3EE",
    words_per_page: int = 4,
) -> bool:
    """Draw captions and overlays over a video with Remotion's TalkingHead.

    OpenMontage ships a bridge for exactly this, but it hands the composition a
    `public/`-prefixed asset path that Remotion's own `staticFile()` refuses,
    so the call fails outright on current checkouts. Driving the CLI ourselves
    keeps the path correct and leaves us independent of that bug.

    Returns False instead of raising: a failed title is never a good reason to
    lose an otherwise finished cut.
    """
    captions = captions or []
    overlays = overlays or []
    if not captions and not overlays:
        return False

    meta = probe_media(video)
    fps = 30                                  # the composition is registered at 30
    frames = max(1, math.ceil(meta["duration"] * fps))

    staged = remotion_public("render")
    shutil.copy2(video, staged / video.name)

    props = {
        # No `public/` prefix — staticFile() rejects it.
        "videoSrc": f"automontage/render/{video.name}",
        "captions": captions,
        "overlays": overlays,
        "wordsPerPage": words_per_page,
        "fontSize": font_size,
        "highlightColor": highlight,
        # Each word sits in its own inline-block span, and CSS drops a trailing
        # ordinary space at the edge of one — words would run together. A
        # non-breaking space survives.
        "captionWordSeparator": " ",
    }
    props_file = REMOTION_ROOT / "public" / "demo-props" / "automontage-overlay.json"
    props_file.parent.mkdir(parents=True, exist_ok=True)
    props_file.write_text(json.dumps(props, indent=2), encoding="utf-8")

    try:
        run([
            "npx", "remotion", "render", "src/index.tsx", "TalkingHead",
            f"--props={props_file.relative_to(REMOTION_ROOT).as_posix()}",
            f"--width={meta['width']}", f"--height={meta['height']}", f"--fps={fps}",
            f"--frames=0-{frames - 1}",
            "--codec=h264", "--crf=18",
            f"--output={out_path.resolve()}",
        ], cwd=REMOTION_ROOT, timeout=7200)
    except SystemExit as exc:
        log(f"overlay render failed: {str(exc).splitlines()[-1][:160]}")
        return False

    return out_path.exists()


def make_portable(video: Path, out_path: Path) -> Path:
    """Write the finished file in a form stock players will actually open.

    Encoders upstream can emit full-range `yuvj420p`; Windows' built-in player
    refuses those outright, and other players show washed-out colour. Convert
    only when the file is actually non-conforming — otherwise just move the
    moov atom to the front, which costs nothing and makes playback start
    immediately.
    """
    info = ffprobe_json(video)
    stream = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    non_conforming = (
        stream.get("codec_name") != "h264"
        or stream.get("pix_fmt") != "yuv420p"
        or stream.get("color_range") == "pc"
    )

    if non_conforming:
        run([
            "ffmpeg", "-v", "error", "-i", str(video),
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out_path), "-y",
        ])
    else:
        run([
            "ffmpeg", "-v", "error", "-i", str(video), "-c", "copy",
            "-movflags", "+faststart", str(out_path), "-y",
        ])
    return out_path


def add_title_overlays(
    video: Path, out_path: Path, title: str, outro: str, *, font_size: int = 64,
) -> Path:
    """Render title / end-tag overlays onto a finished cut.

    Falls back to the untouched cut if the render fails, so a title is never
    the reason a montage is lost.
    """
    duration = media_duration(video)
    overlays: list[dict] = []
    if title:
        overlays.append({
            "type": "hero_title", "in_seconds": 0.0,
            "out_seconds": min(3.5, duration), "position": "full_overlay",
            "text": title, "title": title,
        })
    if outro and duration > 4.0:
        overlays.append({
            "type": "text_card", "in_seconds": max(0.0, duration - 3.0),
            "out_seconds": duration, "position": "lower_third", "text": outro,
        })

    if not overlays or not render_talking_head(
        video, out_path, overlays=overlays, font_size=font_size,
    ):
        shutil.copy(video, out_path)
    return out_path
