# automontage

Automatic video editing engine. Two entry points:

```bash
./automontage raw.mp4      # video in  → edited, captioned cut out
./autophotos  photos/      # photos in → finished video out
```

Built on two projects:

- **[OpenMontage](https://github.com/calesthio/OpenMontage)** — the agentic video
  production system. Supplies transcription, silence/speech analysis, trimming,
  stitching, and the bridge to Remotion.
- **[Remotion](https://github.com/remotion-dev/remotion)** — React-based video
  rendering. Draws animated word-by-word captions, title cards, and the photo
  collage.

## Setup

```bash
./setup.sh
```

Clones OpenMontage into `engine/`, creates a `.venv` with its Python
dependencies plus `faster-whisper` and the Claude SDK, and runs `npm install`
for the Remotion composer. Installs `ffmpeg` if missing. Re-runnable.

## The output library

Every finished render is collected in **`output/`** and **never overwritten**:

```
output/
  2026-08-10_0548_lето-2024.mp4
  2026-08-10_0548_lето-2024.json     ← how it was made
  2026-08-10_0551_launch-recap.mp4
  2026-08-10_0551_launch-recap.json
```

Names are `<date>_<time>_<label>`, so the folder sorts chronologically and two
runs can never collide. The label comes from `--label`, falling back to
`--title`, then the source filename.

Each video gets a sidecar JSON recording the settings, the photos or cut points
used, and the resulting duration — an archive is only useful if you can tell
later why a given cut looks the way it does.

`output/` is gitignored: video files don't belong in git. Use `-o path.mp4` to
write somewhere specific instead.

---

## Video → edited cut

```bash
./automontage raw.mp4
./automontage raw.mp4 --target 45 --title "Launch Recap"
./automontage raw.mp4 --select llm --brief "punchy product teaser"
./automontage raw.mp4 --select all --transition cut     # only drop the silence
```

### How it works

```
raw.mp4
   ├─ 1. probe          ffprobe — duration, resolution, fps
   ├─ 2. analyse        SilenceCutter → speech segments
   ├─ 3. transcribe     Transcriber (faster-whisper) → word-level timings
   ├─ 4. select         which segments survive
   ├─ 5. cut            VideoTrimmer → one clip per segment
   ├─ 6. stitch         VideoStitch → crossfade / fade / hard cut
   └─ 7. finish         Remotion → animated captions + titles
output/<date>_<label>.mp4
```

**Silence is the edit.** Pauses between phrases become cut points; the speech
between them becomes the candidate segments.

| `--select` | What it does | Needs |
|---|---|---|
| `auto` (default) | Ranks segments by loudness and length, keeps the best until `--target` is reached | nothing |
| `llm` | Claude reads the transcript, picks the beats, suggests a title | `ANTHROPIC_API_KEY` |
| `all` | Keeps every speech segment — only the silence goes | nothing |

`llm` falls back to `auto` if the key is missing or the call fails.

### Captions

Captions come from local Whisper transcription; the model downloads on first run
(~150 MB for `base`). If that download is unavailable the pipeline says so and
renders without captions rather than failing.

Bring your own transcript with `--transcript file.json` — a list of segments (or
`{"segments": [...]}`) with word-level `{word, start, end}` entries in
source-video seconds.

Caption timings are remapped from the source timeline onto the edited one, with
crossfade overlap accounted for, so words stay locked to the audio that survived.

---

## Photos → video

```bash
./autophotos photos/                                       # calm Ken Burns slideshow
./autophotos photos/ --order date --title "Лето 2024"      # personal archive, by EXIF date
./autophotos photos/ --style collage --music track.mp3     # vertical cut for social
```

Two styles, because the two jobs are different:

| `--style` | Look | Format |
|---|---|---|
| `slideshow` (default) | One photo at a time, slow Ken Burns move on each, crossfades between | 1920x1080 (`--size vertical\|square`) |
| `collage` | Photos fly in as tilted cards over an ambient background and pile up | 1080x1920, fixed |

```
photos/
   ├─ 1. collect     gather and order (filename | EXIF date | shuffle)
   ├─ 2. build       Ken Burns clips + stitch   ·or·  Remotion collage
   ├─ 3. music       optional bed, normalised to -16 LUFS, faded
   ├─ 4. titles      Remotion title card / end tag
   └─ 5. file        into output/
```

`--order date` reads EXIF capture time, falling back to file mtime for photos
that don't carry one. Supported: jpg, png, webp, bmp, tif, heic.

Photos are never modified — everything is composed into new files.

---

## Options

Shared by both commands: `-o/--output`, `--label`, `--title`, `--outro`,
`--work-dir`, `--keep-work`.

**`./automontage`**

```
--target SECONDS         approximate length of the finished cut
--select auto|llm|all    who chooses the cut (default: auto)
--brief TEXT             creative direction for --select llm
--model ID               Claude model (default: claude-opus-5)
--captions auto|off      caption rendering (default: auto)
--transcript FILE        use this transcript instead of running Whisper
--whisper-model SIZE     tiny|base|small|medium|large-v2|large-v3
--language CODE          ISO 639-1; omit to auto-detect
--transition cut|crossfade|fade      default: crossfade
--transition-duration S  default: 0.4
--silence-threshold DB   what counts as silence (default: -35)
--min-silence S          shortest gap that becomes a cut (default: 0.6)
--font-size N            caption size (default: 52)
--highlight HEX          active-word colour (default: #22D3EE)
```

**`./autophotos`**

```
--style slideshow|collage    default: slideshow
--order name|date|shuffle    default: name
--seed N                     shuffle seed
--limit N                    use at most N photos
--per-photo SECONDS          slideshow 3.5, collage 0.75 (stagger between cards)
--size landscape|vertical|square    slideshow only
--transition cut|crossfade|fade     slideshow only (default: crossfade)
--transition-duration S      default: 0.7
--hold SECONDS               collage only; held after the last card (default: 2.5)
--music FILE                 audio bed, auto-levelled and faded
--fps N                      default: 30
```

## Performance

Rendering is the slow part. Measured on this machine:

| Job | Time |
|---|---|
| 24s video → 13s cut, no captions | ~15s |
| the same with captions and titles | ~50s |
| 8 photos → 11s slideshow with title | ~100s |
| 8 photos → 10s vertical collage with music and title | ~170s |

For long sources, `--captions off` skips the most expensive stage.

## Requirements

Python 3.10+, Node 18+, ffmpeg, and a Chromium for Remotion's renderer.
Remotion downloads its own Chrome Headless Shell by default; if that's blocked,
point it at an existing browser:

```bash
export REMOTION_BROWSER_EXECUTABLE=/path/to/chrome
export REMOTION_IGNORE_CERT_ERRORS=1   # only behind a TLS-intercepting proxy
```

`setup.sh` and both pipelines auto-detect a local Chromium when one is present.

## Layout

```
automontage           video → cut
autophotos            photos → video
setup.sh              provisioning
montage/
  common.py           shared helpers + the output library
  pipeline.py         video pipeline
  photos.py           photo pipelines
  remotion/           Remotion config installed into the composer by setup.sh
engine/OpenMontage/   third-party checkout (gitignored)
output/               the library — finished videos + manifests (gitignored)
```

## Notes

The collage reuses OpenMontage's `CollageBurst` composition, which opens with a
demo caption hardcoded in the component and not exposed through its props. Rather
than patching a vendored file, `photos.py` renders from just after that caption
has faded, which keeps the curtain reveal and leaves the stray text out.

OpenMontage is AGPL-3.0; Remotion has its own licence terms for companies above
a certain size. Check both before commercial use.
