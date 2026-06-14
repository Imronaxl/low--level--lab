#!/usr/bin/env python3
"""
Транслятор: компиляция программ на языке alg в бинарный машинный код
Использование: python tools/compile.py <input.alg> [-o output.bin] [--debug] [--lst listing.txt]
"""

import os
import sys

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lang.lexer import Lexer
from lang.parser import Parser
from translator.codegen import CodeGenerator
from utils.image import write_image


def compile_file(input_path: str, output_path: str, debug: bool = False, lst_path: str | None = None):
    """Компиляция файла с исходным кодом в бинарный файл"""

    with open(input_path, encoding="utf-8") as f:
        source_code = f.read()

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    if debug:
        print("=== Tokens ===")
        for token in tokens[:20]:
            print(token)
        if len(tokens) > 20:
            print(f"... и ещё {len(tokens) - 20} токенов")

    parser = Parser(tokens)
    ast = parser.parse()

    if debug:
        print("\n=== AST ===")
        print(ast)

    codegen = CodeGenerator()
    machine_code, data_section = codegen.generate(ast)

    # Запись в формате ALG4 image
    write_image(output_path, machine_code, data_section)

    print(f"Compiled: {input_path} -> {output_path}")
    print(f"Code size: {len(machine_code)} bytes, Data size: {len(data_section)} bytes")

    # Генерация listing файла
    if lst_path:
        _write_listing(lst_path, machine_code, data_section, source_code)

    return machine_code


def _write_listing(lst_path: str, code: bytes, data: bytes, source: str):
    """Генерация listing файла (код + исходный текст)."""
    with open(lst_path, "w", encoding="utf-8") as f:
        f.write("=== Listing ===\n")
        f.write(f"Code size: {len(code)} bytes\n")
        f.write(f"Data size: {len(data)} bytes\n\n")

        f.write("--- Machine Code ---\n")
        for i in range(0, len(code), 16):
            chunk = code[i : i + 16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            f.write(f"{0x0100 + i:04X}: {hex_part}\n")

        f.write("\n--- Source ---\n")
        for i, line in enumerate(source.split("\n"), 1):
            f.write(f"{i:4d}: {line}\n")

    print(f"Listing: {lst_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/compile.py <input.alg> [-o output.bin] [--debug] [--lst listing.txt]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = "output.bin"
    debug_mode = "--debug" in sys.argv
    lst_file = None

    if "-o" in sys.argv:
        o_index = sys.argv.index("-o")
        if o_index + 1 < len(sys.argv):
            output_file = sys.argv[o_index + 1]

    if "--lst" in sys.argv:
        lst_index = sys.argv.index("--lst")
        if lst_index + 1 < len(sys.argv):
            lst_file = sys.argv[lst_index + 1]

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)

    compile_file(input_file, output_file, debug=debug_mode, lst_path=lst_file)
