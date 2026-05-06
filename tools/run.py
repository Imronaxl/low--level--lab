#!/usr/bin/env python3
"""
Симулятор процессора: выполнение бинарного машинного кода
Использование: python -m tools.run <program.bin> [input.txt] [--debug] [--log output.log]
"""

import os
import sys

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from processor.simulator import Simulator


def run_program(
    binary_path: str,
    input_path: str = None,
    debug: bool = False,
    max_ticks: int = 100000,
    log_path: str = None,
):
    """Запуск программы на симуляторе процессора"""

    # Чтение бинарного файла
    with open(binary_path, "rb") as f:
        machine_code = f.read()

    # Создание симулятора
    sim = Simulator()
    sim.load_program(machine_code)

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

        # Логгируем каждое состояние для golden тестов
        state = sim.datapath.state
        instr_info = (
            sim._get_current_instruction_info()
            if hasattr(sim, "_get_current_instruction_info")
            else "UNKNOWN"
        )
        log.append(
            {
                "tick": tick,
                "pc": state.pc,
                "instruction": instr_info,
                "registers": list(state.registers),
                "flags": dict(state.flags),
                "output": "".join(chr(c) for c in state.output_buffer[-5:] if 0 < c < 128),
            }
        )

        if debug and tick % 100 == 0:
            print(f"Tick {tick}: PC={state.pc}, ACC={state.acc}, Flags={state.flags}")

    # Вывод результатов
    output_text = "".join(chr(c) for c in sim.datapath.state.output_buffer if 0 < c < 128)

    print("=" * 50)
    print("EXECUTION COMPLETE")
    print("=" * 50)
    print(f"Total ticks: {tick}")
    print(f"Halted: {sim.halted}")
    print(f"Output:\n{output_text}")
    print("=" * 50)

    # Регистры
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
                    f"Tick {entry['tick']:6d}: PC={entry['pc']:04X} | {entry['instruction']:20s} | R0={entry['registers'][0]:5d} R1={entry['registers'][1]:5d} | Out='{entry['output']}'\n"
                )
        print(f"\nLog saved to: {log_path}")

    # Сохранение вывода
    if log_path:
        output_path = log_path.replace(".log", ".output")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Output saved to: {output_path}")

    return output_text, log


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tools.run <program.bin> [input.txt] [--debug] [--log output.log]")
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
