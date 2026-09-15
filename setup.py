#!/usr/bin/env python3
"""Provision the automontage engine: OpenMontage + Remotion.

Runs on Windows, macOS and Linux. The platform differences are small and live
in one place each: where a virtualenv puts its interpreter, and how ffmpeg is
installed. Everything else is identical, which is the point — the Linux path
gets exercised constantly, so the Windows path rides on tested code.

    python setup.py          (Windows)
    ./setup.sh               (macOS / Linux — thin wrapper around this file)

Safe to re-run; every step is idempotent.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine" / "OpenMontage"
COMPOSER = ENGINE / "remotion-composer"

OPENMONTAGE_REPO = os.environ.get(
    "OPENMONTAGE_REPO", "https://github.com/calesthio/OpenMontage.git"
)
# Pinned to a commit this project is tested against. Upstream moves fast and has
# broken the Remotion bridge before. Track latest with OPENMONTAGE_REF=main.
OPENMONTAGE_REF = os.environ.get(
    "OPENMONTAGE_REF", "08e2151fa02de28a5d6a312b3d575692bf147ad7"
)

WINDOWS = os.name == "nt"


# --------------------------------------------------------------------------- #

def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def fail(msg: str) -> "None":
    print(f"\nОШИБКА: {msg}", file=sys.stderr)
    sys.exit(1)


def have(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> int:
    """Run a command with its output visible — these steps take minutes."""
    if cmd and not Path(cmd[0]).is_absolute():
        cmd = [have(cmd[0]) or cmd[0], *cmd[1:]]
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if check and proc.returncode != 0:
        fail(f"команда завершилась с ошибкой: {' '.join(str(c) for c in cmd[:4])}")
    return proc.returncode


def venv_python() -> Path:
    return ROOT / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")


# --------------------------------------------------------------------------- #

def check_prerequisites() -> None:
    step("Проверка системных зависимостей")

    if sys.version_info < (3, 10):
        fail(f"нужен Python 3.10 или новее, а запущен {sys.version.split()[0]}")

    missing = [n for n in ("git", "node", "npm") if not have(n)]
    if missing:
        if WINDOWS:
            ids = {"git": "Git.Git", "node": "OpenJS.NodeJS.LTS",
                   "npm": "OpenJS.NodeJS.LTS"}
            cmds = sorted({f"winget install --id {ids[m]} -e" for m in missing})
            fail("не хватает: " + ", ".join(missing) + "\nУстановите:\n  "
                 + "\n  ".join(cmds) + "\nПосле установки закройте и откройте "
                 "PowerShell заново, чтобы обновился PATH.")
        fail("не хватает: " + ", ".join(missing))

    print(f"python {sys.version.split()[0]} · node {version_of('node')} "
          f"· npm {version_of('npm')}")

    ensure_ffmpeg()


def version_of(name: str) -> str:
    try:
        out = subprocess.run([have(name) or name, "--version"],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else "?"
    except Exception:
        return "?"


def ensure_ffmpeg() -> None:
    if have("ffmpeg") and have("ffprobe"):
        print("ffmpeg на месте")
        return

    step("Установка ffmpeg")

    if WINDOWS:
        fail("ffmpeg не найден. Установите:\n"
             "  winget install --id Gyan.FFmpeg -e\n"
             "Затем ЗАКРОЙТЕ и снова откройте PowerShell — иначе Windows не "
             "увидит новую программу — и запустите setup.py ещё раз.")

    sudo: list[str] = []
    if os.geteuid() != 0:                     # type: ignore[attr-defined]
        if not have("sudo"):
            fail("нужны права root, чтобы установить ffmpeg")
        sudo = ["sudo"]

    if have("apt-get"):
        run([*sudo, "apt-get", "update", "-qq"], check=False)
        # --no-install-recommends skips VA driver packages: optional for us and
        # frequently 404 on stale mirrors.
        run([*sudo, "apt-get", "install", "-y", "--no-install-recommends", "ffmpeg"])
    elif have("dnf"):
        run([*sudo, "dnf", "install", "-y", "ffmpeg"])
    elif have("pacman"):
        run([*sudo, "pacman", "-S", "--noconfirm", "ffmpeg"])
    elif have("brew"):
        run(["brew", "install", "ffmpeg"])     # Homebrew refuses to run as root
    else:
        fail("установите ffmpeg вручную: https://ffmpeg.org/download.html")

    if not (have("ffmpeg") and have("ffprobe")):
        fail("ffmpeg установился, но не появился в PATH")


# --------------------------------------------------------------------------- #

def fetch_engine() -> None:
    step("Загрузка OpenMontage")
    ENGINE.parent.mkdir(parents=True, exist_ok=True)

    if not (ENGINE / ".git").is_dir():
        run(["git", "clone", "--depth", "1", OPENMONTAGE_REPO, str(ENGINE)])
    else:
        print("уже склонирован")

    if OPENMONTAGE_REF in ("main", "HEAD"):
        run(["git", "-C", str(ENGINE), "pull", "--ff-only"], check=False)
        print(f"версия: {head_of(ENGINE)} (последняя)")
        return

    if head_of(ENGINE, short=False) == OPENMONTAGE_REF:
        print(f"уже закреплён на {OPENMONTAGE_REF[:7]}")
        return

    ok = run(["git", "-C", str(ENGINE), "fetch", "--depth", "1", "origin",
              OPENMONTAGE_REF], check=False) == 0
    if ok:
        ok = run(["git", "-C", str(ENGINE), "checkout", "-q", "FETCH_HEAD"],
                 check=False) == 0
    print(f"версия: {head_of(ENGINE)}"
          + ("" if ok else "  (закрепить не удалось — если рендер упадёт, "
                           "подозревать в первую очередь это)"))


def head_of(repo: Path, short: bool = True) -> str:
    cmd = [have("git") or "git", "-C", str(repo), "rev-parse"]
    if short:
        cmd.append("--short")
    cmd.append("HEAD")
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.stdout.strip() or "?"


# --------------------------------------------------------------------------- #

def setup_python() -> None:
    step("Установка Python-зависимостей")
    venv = ROOT / ".venv"
    if not venv_python().exists():
        run([sys.executable, "-m", "venv", str(venv)])

    py = str(venv_python())
    run([py, "-m", "pip", "install", "-q", "--upgrade", "pip"], check=False)
    run([py, "-m", "pip", "install", "-q", "-r", str(ENGINE / "requirements.txt")])
    # Local speech-to-text for captions, the Claude SDK for --select llm, and
    # HEIC support — ffmpeg has no HEIF demuxer, so iPhone photos need transcoding.
    run([py, "-m", "pip", "install", "-q", "faster-whisper", "anthropic", "pillow-heif"])
    print(f"установлено в {venv}")


def setup_remotion() -> None:
    step("Установка Remotion")
    # Our config makes the headless browser environment-driven; the upstream
    # checkout ships none, so install it after every clone or pull.
    shutil.copy(ROOT / "montage" / "remotion" / "remotion.config.ts",
                COMPOSER / "remotion.config.ts")
    run(["npm", "install", "--no-audit", "--no-fund"], cwd=COMPOSER)


def check_browser() -> None:
    step("Проверка рендерера Remotion")
    candidates = [
        *Path("/opt/pw-browsers").glob("chromium_headless_shell-*/chrome-linux/headless_shell"),
        *Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"),
    ]
    for name in ("chromium", "chromium-browser", "google-chrome", "headless_shell"):
        found = have(name)
        if found:
            candidates.append(Path(found))

    for c in candidates:
        if c.exists():
            print(f"найден браузер: {c}")
            return
    print("локальный Chromium не найден — Remotion скачает свой при первом рендере")


# --------------------------------------------------------------------------- #

def main() -> int:
    check_prerequisites()
    fetch_engine()
    setup_python()
    setup_remotion()
    check_browser()

    step("Готово")
    if WINDOWS:
        print("\nЗапуск монтажа:\n"
              "  .\\autophotos.cmd input\\photos --title \"Проверка\"\n"
              "  .\\automontage.cmd input\\video\\запись.mp4\n")
    else:
        print("\nЗапуск монтажа:\n"
              "  ./autophotos input/photos --title \"Проверка\"\n"
              "  ./automontage input/video/запись.mp4\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
