"""Render the captured terminal (not a simulated UI) to a 1080p MP4."""

from __future__ import annotations

import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import pyte
from PIL import Image, ImageDraw, ImageFont
from pyte.screens import Char

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "recordings"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
CELL_WIDTH, CELL_HEIGHT = 15, 24
LEFT, TOP = 60, 105
PALETTE = {
    "black": "151515",
    "red": "dd5555",
    "green": "55aa44",
    "brown": "ffaa00",
    "blue": "5555dd",
    "magenta": "bb66dd",
    "cyan": "00bbbb",
    "white": "dddddd",
    "brightblack": "666666",
    "brightred": "ff7777",
    "brightgreen": "88dd66",
    "brightbrown": "ffff55",
    "brightblue": "8888ff",
    "brightmagenta": "dd88ff",
    "brightcyan": "55ffff",
    "brightwhite": "ffffff",
}
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"


class Event(NamedTuple):
    seconds: float
    kind: str
    data: str


class Chapter(NamedTuple):
    seconds: float
    title: str
    keys: str


def load_events() -> list[Event]:
    lines = (OUTPUT / "personal-assistant-demo.cast").read_text().splitlines()
    header = json.loads(lines[0])
    if header["version"] != 2:
        raise ValueError("Expected asciicast v2 absolute timestamps")
    return [
        Event(float(row[0]), str(row[1]), str(row[2]))
        for row in (json.loads(line) for line in lines[1:])
    ]


def color(value: str, default: str) -> str:
    if value == "default":
        return default
    if value in PALETTE:
        return "#" + PALETTE[value]
    if re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return "#" + value
    raise ValueError(f"Unknown terminal color: {value}")


@lru_cache(maxsize=16384)
def glyph(cell: Char) -> Image.Image:
    foreground = color(cell.fg, "#dddddd")
    background = color(cell.bg, "#111111")
    if cell.reverse:
        foreground, background = background, foreground
    tile = Image.new("RGB", (CELL_WIDTH, CELL_HEIGHT), background)
    draw = ImageDraw.Draw(tile)
    # Terminal block glyphs fill the cell, independently of font ascenders.
    if len(cell.data) == 1:
        code = ord(cell.data)
        if 0x2581 <= code <= 0x2588:
            height = round(CELL_HEIGHT * (code - 0x2580) / 8)
            draw.rectangle(
                (0, CELL_HEIGHT - height, CELL_WIDTH, CELL_HEIGHT),
                fill=foreground,
            )
            return tile
        if 0x2589 <= code <= 0x258F:
            width = round(CELL_WIDTH * (0x2590 - code) / 8)
            draw.rectangle((0, 0, width - 1, CELL_HEIGHT), fill=foreground)
            return tile
        if code == 0x2594:
            draw.rectangle((0, 0, CELL_WIDTH, 2), fill=foreground)
            return tile
    font = terminal_bold if cell.bold else terminal_font
    draw.text((0, -1), cell.data, font=font, fill=foreground)
    if cell.underscore:
        draw.line((0, 22, 14, 22), fill=foreground)
    return tile


terminal_font = ImageFont.truetype(FONT_PATH, 25)
terminal_bold = ImageFont.truetype(FONT_PATH, 25, index=1)
title_font = ImageFont.truetype(FONT_PATH, 27)
caption_font = ImageFont.truetype(FONT_PATH, 24)


def draw_screen(screen: pyte.Screen, chapter: Chapter) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), "#0b1020")
    draw = ImageDraw.Draw(frame)
    draw.text((LEFT, 26), "PERSONAL ASSISTANT", font=title_font, fill="#f4f5ff")
    draw.text((1400, 31), "DEMO / TERMINAL", font=caption_font, fill="#8295c9")
    draw.rounded_rectangle((49, 92, 1870, 979), radius=12, fill="#222f50")
    for y in range(screen.lines):
        for x in range(screen.columns):
            frame.paste(
                glyph(screen.buffer[y][x]),
                (LEFT + x * CELL_WIDTH, TOP + y * CELL_HEIGHT),
            )
    draw.text((LEFT, 993), chapter.title, font=title_font, fill="#f4f5ff")
    draw.text((LEFT, 1033), chapter.keys, font=caption_font, fill="#91aaf6")
    return frame


def main() -> None:
    events = load_events()
    chapters = [
        Chapter(float(row["seconds"]), str(row["title"]), str(row["keys"]))
        for row in json.loads((OUTPUT / "demo-chapters.json").read_text())
    ]
    screen = pyte.Screen(120, 36)
    stream = pyte.Stream(screen)
    duration = events[-1].seconds + 2
    output_path = OUTPUT / "personal-assistant-youtube.mp4"
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pixel_format",
            "rgb24",
            "-video_size",
            f"{WIDTH}x{HEIGHT}",
            "-framerate",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        stdin=subprocess.PIPE,
    )
    assert process.stdin is not None
    event_index = 0
    chapter_index = 0
    pixels = b""
    contact_times = {int(ch.seconds + 5): ch.title for ch in chapters}
    saved: set[int] = set()
    try:
        for frame_index in range(int(duration * FPS)):
            seconds = frame_index / FPS
            changed = not pixels
            while (
                event_index < len(events)
                and events[event_index].seconds <= seconds
            ):
                event = events[event_index]
                if event.kind == "o":
                    stream.feed(event.data)
                    changed = True
                event_index += 1
            while (
                chapter_index + 1 < len(chapters)
                and chapters[chapter_index + 1].seconds <= seconds
            ):
                chapter_index += 1
                changed = True
            if changed:
                frame = draw_screen(screen, chapters[chapter_index])
                pixels = frame.tobytes()
            if int(seconds) in contact_times and int(seconds) not in saved:
                draw_screen(screen, chapters[chapter_index]).save(
                    OUTPUT / f"preview-{int(seconds):03}.png"
                )
                saved.add(int(seconds))
            process.stdin.write(pixels)
            if frame_index % (FPS * 20) == 0:
                print(f"MP4: {seconds:.0f}/{duration:.0f}s", flush=True)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg failed")
    # Merge short steps into useful chapters for the video description.
    youtube_chapters = [chapters[0]._replace(seconds=0)]
    for chapter in chapters[1:]:
        if (
            chapter.seconds - youtube_chapters[-1].seconds >= 10
            and duration - chapter.seconds >= 10
        ):
            youtube_chapters.append(chapter)
    (OUTPUT / "youtube-chapters.txt").write_text(
        "\n".join(
            f"{int(ch.seconds) // 60:02}:{int(ch.seconds) % 60:02} {ch.title}"
            for ch in youtube_chapters
        )
        + "\n"
    )
    print(output_path)


if __name__ == "__main__":
    main()
