#!/usr/bin/env python3
"""autophotos — a folder of photos in, a video out.

Two styles, because the two jobs are genuinely different:

  slideshow  One photo at a time, each given a slow Ken Burns move, joined by
             crossfades. Calm and readable — for a personal archive.

  collage    Photos fly in as tilted cards over an ambient background and
             accumulate on screen. Vertical 1080x1920, cut for social.

Both share the tail of the video pipeline: optional music, Remotion titles, and
the same output library.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    LIBRARY, REMOTION_ROOT, Stage, add_title_overlays, library_path, log,
    media_duration, prepare_remotion_env, probe_media, remotion_public,
    require_binaries, require_engine, run, write_manifest,
)

PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic"}

SIZES = {
    "landscape": (1920, 1080),
    "vertical": (1080, 1920),
    "square": (1080, 1080),
}

# The collage composition opens with a hardcoded demo caption that is not
# exposed through its props and fades out at 2.6s. Rendering from just after
# that keeps the curtain reveal while leaving the stray text off our video.
COLLAGE_TEXT_CLEAR_S = 2.7


# --------------------------------------------------------------------------- #
#  Gathering and ordering
# --------------------------------------------------------------------------- #

def collect_photos(inputs: list[Path]) -> list[Path]:
    found: list[Path] = []
    for item in inputs:
        item = item.expanduser()
        if item.is_dir():
            found += [p for p in item.iterdir()
                      if p.is_file() and p.suffix.lower() in PHOTO_SUFFIXES]
        elif item.is_file() and item.suffix.lower() in PHOTO_SUFFIXES:
            found.append(item)
        elif item.is_file():
            log(f"skipping {item.name} — not a supported image")
    return found


def exif_taken_at(path: Path) -> float | None:
    """When the photo was taken, from EXIF. None when it isn't recorded."""
    try:
        from PIL import Image

        exif = Image.open(path).getexif()
        raw = exif.get_ifd(0x8769).get(0x9003) or exif.get(0x0132)  # Original, then DateTime
        if not raw:
            return None
        return time.mktime(time.strptime(str(raw), "%Y:%m:%d %H:%M:%S"))
    except Exception:
        return None


def order_photos(photos: list[Path], how: str, seed: int) -> list[Path]:
    if how == "shuffle":
        shuffled = list(photos)
        random.Random(seed).shuffle(shuffled)
        return shuffled

    if how == "date":
        dated = [(exif_taken_at(p), p) for p in photos]
        missing = [p.name for stamp, p in dated if stamp is None]
        if missing:
            log(f"{len(missing)} photo(s) without EXIF date — falling back to "
                f"file mtime for those")
        return [p for _, p in sorted(
            ((stamp if stamp is not None else p.stat().st_mtime, p) for stamp, p in dated),
            key=lambda pair: pair[0],
        )]

    return sorted(photos, key=lambda p: p.name.lower())


# --------------------------------------------------------------------------- #
#  Slideshow — Ken Burns
# --------------------------------------------------------------------------- #

# Four moves, cycled so consecutive photos never repeat the same motion.
KEN_BURNS_MOVES = [
    ("zoom in",       "min(1+0.0013*on,1.26)", "iw/2-(iw/zoom/2)",              "ih/2-(ih/zoom/2)"),
    ("zoom out",      "max(1.26-0.0013*on,1.0)", "iw/2-(iw/zoom/2)",            "ih/2-(ih/zoom/2)"),
    ("pan right",     "1.18",                  "(iw-iw/zoom)*on/{frames}",      "ih/2-(ih/zoom/2)"),
    ("pan down",      "1.18",                  "iw/2-(iw/zoom/2)",              "(ih-ih/zoom)*on/{frames}"),
]


def ken_burns_clip(
    photo: Path, out: Path, seconds: float, size: tuple[int, int], fps: int, move_idx: int,
) -> str:
    """Render one still into a moving clip.

    zoompan on a raw photo shows visible stepping, so the image is first scaled
    to twice the output size — the sub-pixel motion then lands on real detail
    instead of jittering between source pixels.
    """
    width, height = size
    frames = max(2, int(round(seconds * fps)))
    name, z, x, y = KEN_BURNS_MOVES[move_idx % len(KEN_BURNS_MOVES)]

    vf = (
        f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
        f"crop={width * 2}:{height * 2},"
        f"zoompan=z='{z}':x='{x.format(frames=frames)}':y='{y.format(frames=frames)}':"
        f"d={frames}:s={width}x{height}:fps={fps},"
        f"setsar=1,format=yuv420p"
    )

    run([
        "ffmpeg", "-v", "error",
        "-i", str(photo),
        # A silent track on every clip keeps the stitcher's audio handling uniform.
        "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
        "-vf", vf, "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-shortest",
        "-r", str(fps), str(out), "-y",
    ])
    return name


def build_slideshow(
    photos: list[Path], work: Path, size: tuple[int, int], fps: int,
    per_photo: float, transition: str, transition_duration: float,
) -> Path:
    from tools.video.video_stitch import VideoStitch

    clips_dir = work / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []

    for i, photo in enumerate(photos):
        clip = clips_dir / f"kb_{i:03d}.mp4"
        move = ken_burns_clip(photo, clip, per_photo, size, fps, i)
        clips.append(clip)
        log(f"{i + 1}/{len(photos)}  {photo.name}  ({move})")

    out = work / "slideshow.mp4"
    if len(clips) == 1:
        shutil.copy(clips[0], out)
        return out

    result = VideoStitch().execute({
        "operation": "stitch",
        "clips": [str(c) for c in clips],
        "output_path": str(out),
        "transition": transition,
        "transition_duration": transition_duration,
        "auto_normalize": True,
        "target_resolution": f"{size[0]}x{size[1]}",
        "target_fps": fps,
    })
    if not result.success or not out.exists():
        raise SystemExit(f"Stitch failed: {result.error}")
    return out


# --------------------------------------------------------------------------- #
#  Collage — Remotion CollageBurst
# --------------------------------------------------------------------------- #

def collage_layout(count: int, stagger: float, hold: float, first_in: float) -> list[dict]:
    """Place each photo on the vertical frame.

    Cards alternate across a centre line and walk down the frame, so they
    overlap like a pile rather than tiling a grid. Rotation alternates too —
    without it the stack reads as a spreadsheet.
    """
    layout: list[dict] = []
    for i in range(count):
        column = i % 3            # left / right / centre, cycling
        x = (0.32, 0.68, 0.50)[column]
        # Walk down the frame, then wrap back up so long sets keep filling it.
        y = 0.26 + ((i % 6) / 6.0) * 0.48
        layout.append({
            "x": x,
            "y": round(y, 4),
            "widthPct": 0.52 if i % 4 == 0 else 0.44,
            "aspect": 3 / 4,
            "rotation": (-8, 7, -4, 6, -6, 5)[i % 6],
            "inSeconds": round(first_in + i * stagger, 3),
            "hero": i % 4 == 0,
            "seed": i + 1,
        })
    return layout


def collage_background(photo: Path, out: Path, seconds: float, fps: int) -> None:
    """An ambient bed for the collage, made from one of the photos.

    The composition blurs and dims whatever it gets, so a slow push on a single
    frame is enough — and it keeps the palette tied to the set.
    """
    width, height = SIZES["vertical"]
    frames = max(2, int(round(seconds * fps)))
    run([
        "ffmpeg", "-v", "error", "-i", str(photo),
        "-vf",
        f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
        f"crop={width * 2}:{height * 2},"
        f"zoompan=z='min(1+0.0009*on,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={width}x{height}:fps={fps},setsar=1,format=yuv420p",
        "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        str(out), "-y",
    ])


def build_collage(
    photos: list[Path], work: Path, fps: int, stagger: float, hold: float,
) -> Path:
    prepare_remotion_env()

    staged = remotion_public("collage")
    for photo in photos:
        shutil.copy(photo, staged / photo.name)

    first_in = COLLAGE_TEXT_CLEAR_S + 1.7          # after the curtain has opened
    total = first_in + len(photos) * stagger + hold
    collage_background(photos[0], staged / "background.mp4", total + 1.0, fps)

    layout = collage_layout(len(photos), stagger, hold, first_in)
    clips = [
        {"src": f"automontage/collage/{photo.name}", "kind": "image",
         "outSeconds": round(total, 3), **spot}
        for photo, spot in zip(photos, layout)
    ]

    props = {
        "backgroundSrc": "automontage/collage/background.mp4",
        "backgroundInSeconds": 0,
        "curtainStartSeconds": COLLAGE_TEXT_CLEAR_S + 0.3,
        "curtainEndSeconds": COLLAGE_TEXT_CLEAR_S + 1.5,
        "clips": clips,
    }
    props_file = REMOTION_ROOT / "public" / "demo-props" / "automontage-collage.json"
    props_file.parent.mkdir(parents=True, exist_ok=True)
    props_file.write_text(json.dumps(props, indent=2), encoding="utf-8")

    out = work / "collage.mp4"
    start_frame = int(round(COLLAGE_TEXT_CLEAR_S * fps))
    end_frame = int(round(total * fps)) - 1
    log(f"rendering frames {start_frame}-{end_frame} "
        f"({(end_frame - start_frame + 1) / fps:.1f}s at {fps}fps)")

    run([
        "npx", "remotion", "render", "src/index.tsx", "CollageBurst",
        f"--props={props_file.relative_to(REMOTION_ROOT)}",
        f"--frames={start_frame}-{end_frame}",
        "--codec=h264", "--crf=20",
        f"--output={out.resolve()}",
    ], cwd=REMOTION_ROOT, timeout=3600)

    if not out.exists():
        raise SystemExit("Remotion produced no collage output")
    return out


# --------------------------------------------------------------------------- #
#  Music
# --------------------------------------------------------------------------- #

def add_music(video: Path, music: Path, out: Path, fade: float = 2.0) -> Path:
    """Lay a music bed under the video, trimmed, levelled and faded to length.

    Any audio already on the video (the silent beds from Ken Burns clips) is
    replaced outright — there is nothing worth keeping underneath.

    Tracks arrive at wildly different levels, so the bed is normalised to the
    EBU R128 target social platforms expect (-16 LUFS) before the fades go on.
    Without it, one export is inaudible and the next one clips.
    """
    duration = media_duration(video)
    fade_start = max(0.0, duration - fade)
    run([
        "ffmpeg", "-v", "error", "-i", str(video), "-i", str(music),
        "-filter_complex",
        f"[1:a]atrim=0:{duration:.3f},"
        f"loudnorm=I=-16:TP=-1.5:LRA=11,"
        f"afade=t=in:st=0:d={fade:.2f},"
        f"afade=t=out:st={fade_start:.3f}:d={fade:.2f},"
        f"aformat=sample_rates=48000:channel_layouts=stereo[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(out), "-y",
    ])
    return out


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="autophotos",
        description="Turn a folder of photos into a video.",
    )
    parser.add_argument("inputs", type=Path, nargs="+",
                        help="photo folder(s) or individual image files")
    parser.add_argument("--style", choices=["slideshow", "collage"], default="slideshow",
                        help="slideshow=calm Ken Burns (default), collage=social cards")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="exact output path; default lands in output/")
    parser.add_argument("--order", choices=["name", "date", "shuffle"], default="name",
                        help="date reads EXIF capture time")
    parser.add_argument("--seed", type=int, default=1, help="shuffle seed")
    parser.add_argument("--limit", type=int, default=None, help="use at most N photos")
    parser.add_argument("--per-photo", type=float, default=None,
                        help="seconds per photo (slideshow 3.5, collage 0.75)")
    parser.add_argument("--size", choices=list(SIZES), default=None,
                        help="slideshow only; collage is always vertical")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--transition", choices=["cut", "crossfade", "fade"],
                        default="crossfade", help="slideshow only")
    parser.add_argument("--transition-duration", type=float, default=0.7)
    parser.add_argument("--hold", type=float, default=2.5,
                        help="collage only; seconds held after the last card lands")
    parser.add_argument("--music", type=Path, default=None, help="audio track to lay under")
    parser.add_argument("--title", default="", help="opening title card")
    parser.add_argument("--outro", default="", help="closing lower-third")
    parser.add_argument("--label", default="", help="name for the file in output/")
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    require_engine()
    require_binaries()
    prepare_remotion_env()

    photos = collect_photos(args.inputs)
    if not photos:
        sys.exit("No supported images found. Looked for: "
                 + ", ".join(sorted(PHOTO_SUFFIXES)))

    photos = order_photos(photos, args.order, args.seed)
    if args.limit:
        photos = photos[:args.limit]

    if args.music and not args.music.exists():
        sys.exit(f"Music file not found: {args.music}")

    per_photo = args.per_photo or (3.5 if args.style == "slideshow" else 0.75)
    size = SIZES[args.size or ("landscape" if args.style == "slideshow" else "vertical")]
    if args.style == "collage":
        size = SIZES["vertical"]

    work = (args.work_dir or Path("/tmp") / f"autophotos-{int(time.time())}").resolve()
    work.mkdir(parents=True, exist_ok=True)

    started = time.time()
    stage = Stage(5)

    # 1 — line up the photos --------------------------------------------------
    stage("Collecting photos")
    log(f"{len(photos)} photo(s), ordered by {args.order}")
    log("first: " + ", ".join(p.name for p in photos[:4])
        + (" …" if len(photos) > 4 else ""))

    # 2 — build the visual ----------------------------------------------------
    if args.style == "slideshow":
        stage(f"Building slideshow ({size[0]}x{size[1]}, {per_photo}s per photo)")
        assembled = build_slideshow(photos, work, size, args.fps, per_photo,
                                    args.transition, args.transition_duration)
    else:
        stage(f"Building collage ({size[0]}x{size[1]}, {per_photo}s apart)")
        assembled = build_collage(photos, work, args.fps, per_photo, args.hold)
    log(f"{media_duration(assembled):.2f}s")

    # 3 — music ---------------------------------------------------------------
    stage("Adding music")
    if args.music:
        assembled = add_music(assembled, args.music, work / "with_music.mp4")
        log(f"laid {args.music.name} under the cut")
    else:
        log("no music supplied")

    # 4 — titles --------------------------------------------------------------
    stage("Rendering titles")
    titled = work / "titled.mp4"
    if args.title or args.outro:
        add_title_overlays(assembled, titled, args.title, args.outro)
    else:
        shutil.copy(assembled, titled)
        log("no title requested")

    # 5 — file it in the library ---------------------------------------------
    stage("Filing in the library")
    label = args.label or args.title or f"{args.style}-{len(photos)}-photos"
    out_path = args.output.expanduser().resolve() if args.output else library_path(label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(titled), out_path)

    final = probe_media(out_path)
    write_manifest(out_path, {
        "source": "photos",
        "style": args.style,
        "photo_count": len(photos),
        "photos": [p.name for p in photos],
        "order": args.order,
        "seconds_per_photo": per_photo,
        "music": args.music.name if args.music else None,
        "title": args.title or None,
        "resolution": f"{final['width']}x{final['height']}",
        "duration_seconds": round(final["duration"], 2),
    })

    print(
        f"\n✅ {out_path}\n"
        f"   {final['width']}x{final['height']} @ {final['fps']}fps · "
        f"{final['duration']:.2f}s · {out_path.stat().st_size / 1e6:.1f} MB\n"
        f"   {len(photos)} photos · {args.style} · {time.time() - started:.0f}s elapsed"
    )

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"   intermediates: {work}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
