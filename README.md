# automontage

Automatic video editing engine. Feed it a raw video file, get back an edited,
captioned cut.

It wires two projects into one pipeline:

- **[OpenMontage](https://github.com/calesthio/OpenMontage)** — the agentic video
  production system. Supplies transcription, silence/speech analysis, trimming,
  stitching, and the bridge to Remotion.
- **[Remotion](https://github.com/remotion-dev/remotion)** — React-based video
  rendering. Draws the animated word-by-word captions, title cards, and overlays.

## Setup

```bash
./setup.sh
```

Clones OpenMontage into `engine/`, creates a `.venv` with its Python
dependencies plus `faster-whisper` and the Claude SDK, and runs `npm install`
for the Remotion composer. Installs `ffmpeg` if it's missing. Re-runnable.

## Run

```bash
./automontage raw.mp4
```

That's the whole thing. Output lands in `output/montage.mp4`.

Useful variations:

```bash
# Cut down to roughly 45 seconds, with a title card
./automontage raw.mp4 --target 45 --title "Launch Recap"

# Let Claude choose the beats (needs ANTHROPIC_API_KEY)
./automontage raw.mp4 --select llm --brief "punchy product teaser" --target 60

# Keep every take, just remove the dead air
./automontage raw.mp4 --select all --transition cut
```

## How it works

```
raw.mp4
   │
   ├─ 1. probe          ffprobe — duration, resolution, fps
   ├─ 2. analyse        OpenMontage SilenceCutter → speech segments
   ├─ 3. transcribe     OpenMontage Transcriber (faster-whisper) → word timings
   ├─ 4. select         which segments survive  (heuristic | Claude | keep-all)
   ├─ 5. cut            OpenMontage VideoTrimmer → one clip per segment
   ├─ 6. stitch         OpenMontage VideoStitch → crossfade / fade / hard cut
   └─ 7. finish         Remotion → animated captions + titles
   │
output/montage.mp4
```

Every stage prints what it did, so a run is auditable as it goes.

### Choosing the cut

`--select` picks the editor:

| Mode | What it does | Needs |
|---|---|---|
| `auto` (default) | Ranks segments by loudness and length, keeps the best until `--target` is reached | nothing |
| `llm` | Claude reads the transcript and picks the beats, and suggests a title | `ANTHROPIC_API_KEY` |
| `all` | Keeps every speech segment — only the silence goes | nothing |

`llm` falls back to `auto` if the key is missing or the call fails.

### Captions

Captions come from local Whisper transcription. The model downloads on first
run (~150 MB for `base`); if that download is unavailable the pipeline says so
and renders the cut without captions rather than failing.

To supply your own transcript instead, use `--transcript file.json` — a list of
segments (or `{"segments": [...]}`), each carrying word-level
`{word, start, end}` entries in source-video seconds.

Caption timings are remapped from the source timeline onto the edited one, with
crossfade overlap accounted for, so words stay locked to the audio that
survived the cut.

## Options

```
--target SECONDS         approximate length of the finished cut
--select auto|llm|all    who chooses the cut (default: auto)
--brief TEXT             creative direction for --select llm
--model ID               Claude model (default: claude-opus-5)
--title TEXT             opening title card
--outro TEXT             closing lower-third
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
--keep-work              keep intermediate clips for inspection
-o, --output PATH        default: output/montage.mp4
```

## Requirements

Python 3.10+, Node 18+, ffmpeg, and a Chromium for Remotion's renderer.
Remotion downloads its own Chrome Headless Shell by default; if that's blocked,
point it at an existing browser:

```bash
export REMOTION_BROWSER_EXECUTABLE=/path/to/chrome
export REMOTION_IGNORE_CERT_ERRORS=1   # only behind a TLS-intercepting proxy
```

`setup.sh` and the pipeline both auto-detect a local Chromium when one is present.

## Layout

```
automontage           the command
setup.sh              provisioning
montage/pipeline.py   the pipeline
engine/OpenMontage/   third-party checkout (gitignored)
  remotion-composer/  Remotion compositions and components
output/               finished videos (gitignored)
```

OpenMontage is AGPL-3.0; Remotion has its own licence terms for companies above
a certain size. Check both before commercial use.
