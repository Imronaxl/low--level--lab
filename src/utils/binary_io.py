"""Утилиты для работы с бинарными файлами."""

from pathlib import Path

from isa.encoding import disassemble_to_text


def write_binary_file(path: Path, data: bytes):
    """Записывает бинарные данные в файл."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def read_binary_file(path: Path) -> bytes:
    """Читает бинарные данные из файла."""
    with open(path, "rb") as f:
        return f.read()


def write_debug_dump(path: Path, binary_data: bytes, instructions: list):
    """Записывает отладочный дамп в текстовом формате."""
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("=== Debug Dump ===")
    lines.append(f"Total size: {len(binary_data)} bytes")
    lines.append("")
    lines.append("Instructions:")
    lines.append("-" * 60)

    # Генерируем дамп инструкций
    dump_text = disassemble_to_text(instructions)
    lines.append(dump_text)

    lines.append("")
    lines.append("-" * 60)
    lines.append("Raw hex dump:")

    # Добавляем raw hex dump
    for i in range(0, len(binary_data), 16):
        chunk = binary_data[i : i + 16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:04X}: {hex_part:<48} {ascii_part}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
