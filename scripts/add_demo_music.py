"""Compose a quiet retro score and mux it without changing video frames."""

from __future__ import annotations

import math
import random
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

RATE = 24000
BEAT = 60 / 96
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/recordings/personal-assistant-youtube.mp4"
OUTPUT = SOURCE.with_stem("personal-assistant-youtube-music")


def compose(path: Path, duration: float) -> None:
    """Synthesize original deterministic music with no sampled recordings."""
    count = math.ceil(duration * RATE)
    left = array("f", [0.0]) * count
    right = array("f", [0.0]) * count
    rng = random.Random(29)

    def note(
        start: float,
        length: float,
        midi: int,
        gain: float,
        pan: float,
        soft: bool = False,
    ) -> None:
        first = round(start * RATE)
        samples = min(round(length * RATE), count - first)
        frequency = 440 * 2 ** ((midi - 69) / 12)
        phase_step = math.tau * frequency / RATE
        for index in range(max(0, samples)):
            time = index / RATE
            release = min(1.0, (samples - index) / (RATE * 0.12))
            envelope = min(1.0, time / 0.025) * release
            envelope *= math.exp(-time * (1.2 if soft else 3.0))
            phase = index * phase_step
            tone = math.sin(phase) + 0.22 * math.sin(2 * phase)
            tone += 0.08 * math.sin(3 * phase)
            value = gain * envelope * tone
            left[first + index] += value * (1 - pan) / 2
            right[first + index] += value * (1 + pan) / 2

    def drum(start: float, kind: str, gain: float) -> None:
        length = 0.28 if kind == "kick" else 0.1
        first = round(start * RATE)
        samples = min(round(length * RATE), count - first)
        previous = 0.0
        for index in range(max(0, samples)):
            time = index / RATE
            if kind == "kick":
                phase = math.tau * (
                    46 * time + 1.5 * (1 - math.exp(-35 * time))
                )
                value = math.sin(phase) * math.exp(-time * 20)
            else:
                noise = rng.uniform(-1, 1)
                value = (noise - previous) * math.exp(-time * 65)
                previous = noise
            value *= gain * min(1.0, time / 0.003)
            left[first + index] += value
            right[first + index] += value

    # Cmaj7, Am7, Fmaj7, G6: mellow chords with a sparse upper melody.
    chords = (
        (60, 64, 67, 71),
        (57, 60, 64, 67),
        (53, 57, 60, 64),
        (55, 59, 62, 64),
    )
    bars = math.ceil(duration / (4 * BEAT))
    for bar in range(bars):
        start = bar * 4 * BEAT
        chord = chords[(bar // 2) % len(chords)]
        for position, midi in enumerate(chord):
            note(start, 4.4 * BEAT, midi, 0.055, (position - 1.5) / 3, True)
        for beat in (0, 2):
            note(start + beat * BEAT, 1.5 * BEAT, chord[0] - 24, 0.14, 0)
        if bar >= 4:
            for step in range(8):
                pitch = chord[(step + bar % 2) % 4] + 12
                note(start + step * BEAT / 2, BEAT, pitch, 0.028, 0.3)
            for beat in range(4):
                drum(start + beat * BEAT, "kick", 0.06)
                drum(start + (beat + 0.5) * BEAT, "hat", 0.012)
        if bar % 8 in (4, 5, 6):
            for step, degree in enumerate((2, 3, 1)):
                note(
                    start + step * BEAT,
                    1.4 * BEAT,
                    chord[degree] + 12,
                    0.045,
                    -0.2,
                    True,
                )

    peak = max(
        max(abs(value) for value in left),
        max(abs(value) for value in right),
        0.001,
    )
    pcm = array("h")
    for index in range(count):
        fade = min(1.0, index / (RATE * 2), (count - index) / (RATE * 5))
        scale = 14000 * fade / peak
        pcm.append(round(left[index] * scale))
        pcm.append(round(right[index] * scale))
    if sys.byteorder != "little":
        pcm.byteswap()
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(pcm.tobytes())


def main() -> None:
    duration = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(SOURCE),
            ],
            text=True,
        ).strip()
    )
    with tempfile.TemporaryDirectory(prefix="demo-music-") as temporary:
        score = Path(temporary) / "score.wav"
        compose(score, duration)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(SOURCE),
                "-i",
                str(score),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-af",
                "loudnorm=I=-24:TP=-3:LRA=7",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "48000",
                "-t",
                str(duration),
                "-movflags",
                "+faststart",
                str(OUTPUT),
            ],
            check=True,
        )
    print(OUTPUT)


if __name__ == "__main__":
    main()
