"""Shared plumbing for the video and photo pipelines.

Holds the bits both entry points need: where things live, how a run is logged,
ffprobe wrappers, Remotion's browser resolution, and the output library.
"""

from __future__ import annotations

import json
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


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None):
    """Run a command, surfacing stderr on failure instead of swallowing it."""
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
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


def add_title_overlays(
    video: Path, out_path: Path, title: str, outro: str, *, font_size: int = 64,
) -> Path:
    """Render title / end-tag overlays onto a finished cut with Remotion.

    Reuses OpenMontage's caption-burn bridge, which also accepts overlays with
    no captions. Falls back to the untouched cut if the render fails, so a
    title is never the reason a montage is lost.
    """
    from tools.video.remotion_caption_burn import RemotionCaptionBurn

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

    if not overlays:
        shutil.copy(video, out_path)
        return out_path

    tool = RemotionCaptionBurn()
    if not hasattr(tool, "_render_remotion"):
        shutil.copy(video, out_path)
        log("caption tool cannot render overlays alone; keeping the clean cut")
        return out_path

    result = tool._render_remotion(
        input_path=str(video), output_path=str(out_path), captions=[],
        words_per_page=4, font_size=font_size, highlight_color="#22D3EE",
        overlays=overlays,
    )
    if not result.success or not out_path.exists():
        log(f"title render failed ({result.error}); keeping the clean cut")
        shutil.copy(video, out_path)
    return out_path
