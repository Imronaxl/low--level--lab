"""Бинарный формат образа ALG4.

Формат:
  [Magic: 4 bytes "ALG4"]
  [Version: 2 bytes (uint16 LE)]
  [Entry point: 2 bytes (uint16 LE)]
  [Text offset: 2 bytes (uint16 LE)]
  [Text size: 2 bytes (uint16 LE)]
  [Data offset: 2 bytes (uint16 LE)]
  [Data size: 2 bytes (uint16 LE)]
  [Text section: variable]
  [Data section: variable]

Общий заголовок: 16 байт.
"""

import struct
from pathlib import Path

MAGIC = b"ALG4"
VERSION = 1
HEADER_SIZE = 16  # 4 (magic) + 2 (version) + 2 (entry) + 2*4 (offsets+sizes) = 16


def pack_header(entry: int, text_offset: int, text_size: int, data_offset: int, data_size: int) -> bytes:
    """Упаковывает заголовок образа."""
    return struct.pack(
        "<4sHHHHHH",
        MAGIC,
        VERSION,
        entry,
        text_offset,
        text_size,
        data_offset,
        data_size,
    )


def unpack_header(data: bytes) -> dict:
    """Распаковывает заголовок образа."""
    if len(data) < HEADER_SIZE:
        raise ValueError(f"Файл слишком мал для заголовка: {len(data)} < {HEADER_SIZE}")
    magic, version, entry, text_off, text_sz, data_off, data_sz = struct.unpack(
        "<4sHHHHHH", data[:HEADER_SIZE]
    )
    if magic != MAGIC:
        raise ValueError(f"Неверный magic: {magic!r} (ожидалось {MAGIC!r})")
    return {
        "version": version,
        "entry": entry,
        "text_offset": text_off,
        "text_size": text_sz,
        "data_offset": data_off,
        "data_size": data_sz,
    }


def write_image(path: str | Path, code: bytes, data: bytes, entry: int = 0x0100):
    """Записывает бинарный образ с заголовком."""
    path = Path(path)
    text_offset = HEADER_SIZE
    data_offset = HEADER_SIZE + len(code)
    header = pack_header(entry, text_offset, len(code), data_offset, len(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(header)
        f.write(code)
        f.write(data)


def read_image(path: Path) -> dict:
    """Читает бинарный образ и возвращает его компоненты."""
    with open(path, "rb") as f:
        raw = f.read()
    info = unpack_header(raw)
    info["code"] = raw[info["text_offset"] : info["text_offset"] + info["text_size"]]
    info["data"] = raw[info["data_offset"] : info["data_offset"] + info["data_size"]]
    return info
