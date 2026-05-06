#!/usr/bin/env python3
"""
Транслятор: компиляция программ на языке alg в бинарный машинный код
Использование: python -m tools.compile <input.alg> <output.bin>
"""

import os
import sys

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lang.lexer import Lexer
from lang.parser import Parser
from translator.codegen import CodeGenerator


def compile_file(input_path: str, output_path: str, debug: bool = False):
    """Компиляция файла с исходным кодом в бинарный файл"""

    # Чтение исходного файла
    with open(input_path, encoding="utf-8") as f:
        source_code = f.read()

    # Лексический анализ
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    if debug:
        print("=== Tokens ===")
        for token in tokens[:20]:  # Первые 20 токенов для отладки
            print(token)
        if len(tokens) > 20:
            print(f"... и ещё {len(tokens) - 20} токенов")

    # Синтаксический анализ
    parser = Parser(tokens)
    ast = parser.parse()

    if debug:
        print("\n=== AST ===")
        print(ast)

    # Генерация кода
    codegen = CodeGenerator()
    machine_code, data_section = codegen.generate(ast)

    # Запись бинарного файла (код + данные)
    with open(output_path, "wb") as f:
        f.write(machine_code)
        if data_section:
            f.write(data_section)

    print(f"Compiled: {input_path} -> {output_path}")
    print(f"Code size: {len(machine_code)} bytes")

    return machine_code


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m tools.compile <input.alg> <output.bin> [--debug]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    debug_mode = "--debug" in sys.argv

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)

    compile_file(input_file, output_file, debug=debug_mode)
