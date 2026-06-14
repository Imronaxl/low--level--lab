#!/usr/bin/env python3
"""
Симулятор процессора: выполнение бинарного машинного кода
Использование: python tools/run.py <program.bin> [input.txt] [--debug] [--log output.log]
"""

import os
import sys

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from processor.simulator import Simulator
from utils.image import read_image


def run_program(
    binary_path: str,
    input_path: str = None,
    debug: bool = False,
    max_ticks: int = 100000,
    log_path: str = None,
):
    """Запуск программы на симуляторе процессора"""

    # Чтение бинарного образа
    image = read_image(binary_path)

    # Создание симулятора
    sim = Simulator()
    sim.load_program(image["code"])

    # Загрузка данных из образа в память
    if image["data"]:
        for i, byte in enumerate(image["data"]):
            addr = 0x1000 + i
            if addr < len(sim.datapath.memory):
                sim.datapath.memory[addr] = byte

    # Загрузка входных данных (если есть)
    if input_path and os.path.exists(input_path):
        with open(input_path, encoding="utf-8") as f:
            input_data = f.read()
        sim.set_input(input_data)
        if debug:
            print(f"Input loaded: {len(input_data)} chars")

    # Журнал выполнения
    log = []

    # Выполнение с точностью до такта
    tick = 0
    while not sim.halted and tick < max_ticks:
        sim.tick()
        tick += 1

        state = sim.datapath.state
        log.append(
            {
                "tick": tick,
                "pc": state.pc,
                "registers": list(state.registers),
                "flags": dict(state.flags),
                "output": "".join(chr(c) for c in state.output_buffer[-5:] if 0 < c < 128),
            }
        )

        if debug and tick % 100 == 0:
            print(f"Tick {tick}: PC={state.pc}, Flags={state.flags}")

    # Вывод результатов
    output_text = "".join(chr(c) for c in sim.datapath.state.output_buffer if 0 < c < 128)

    print("=" * 50)
    print("EXECUTION COMPLETE")
    print("=" * 50)
    print(f"Total ticks: {tick}")
    print(f"Halted: {sim.halted}")
    print(f"Output:\n{output_text}")
    print("=" * 50)

    state = sim.datapath.state
    print("\nFinal Register State:")
    for i, reg in enumerate(state.registers):
        print(f"  R{i}: {reg} (0x{reg:08X})")

    print("\nVector Registers:")
    for i, vreg in enumerate(state.vector_registers):
        print(f"  V{i}: {vreg}")

    print(
        f"\nFlags: Z={state.flags['Z']}, N={state.flags['N']}, C={state.flags['C']}, V={state.flags['V']}"
    )

    # Сохранение журнала
    if log_path:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# Execution Log\n")
            f.write(f"# Total ticks: {tick}\n")
            f.write(f"# Output: {output_text}\n\n")
            for entry in log:
                f.write(
                    f"Tick {entry['tick']:6d}: PC={entry['pc']:04X} | R0={entry['registers'][0]:5d} R1={entry['registers'][1]:5d} | Out='{entry['output']}'\n"
                )
        print(f"\nLog saved to: {log_path}")

    return output_text, log


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/run.py <program.bin> [input.txt] [--debug] [--log output.log]")
        sys.exit(1)

    binary_file = sys.argv[1]
    input_file = None
    debug_mode = False
    log_file = None

    for arg in sys.argv[2:]:
        if arg == "--debug":
            debug_mode = True
        elif arg == "--log" and len(sys.argv) > sys.argv.index(arg) + 1:
            log_file = sys.argv[sys.argv.index(arg) + 1]
        elif not arg.startswith("--"):
            input_file = arg

    if not os.path.exists(binary_file):
        print(f"Error: File '{binary_file}' not found")
        sys.exit(1)

    run_program(binary_file, input_file, debug=debug_mode, log_path=log_file)
