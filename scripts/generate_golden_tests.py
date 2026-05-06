#!/usr/bin/env python3
"""
Скрипт для генерации Golden-тестов для всех обязательных алгоритмов.
Запускает компиляцию и симуляцию каждой программы, сохраняет:
- machine.bin (бинарный код)
- output.golden (вывод программы)
- log.golden (адаптированный журнал работы процессора)
- input.txt (входные данные если нужны)
"""

import os
import subprocess
import sys
from pathlib import Path

# Пути
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
PROGRAMS_DIR = PROJECT_ROOT / "programs"
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"

# Список тестов с описанием
TESTS = {
    "hello": {"source": "hello.alg", "input": "", "description": "Вывод Hello, World!"},
    "cat": {"source": "cat.alg", "input": "Hello\nWorld\nTest\n", "description": "Эхо ввода (cat)"},
    "hello_user_name": {
        "source": "hello_user_name.alg",
        "input": "Alice",
        "description": "Приветствие пользователя",
    },
    "sort": {
        "source": "sort.alg",
        "input": "5\n3\n8\n1\n9\n2\n",
        "description": "Сортировка чисел",
    },
    "euler4_scalar": {
        "source": "euler4_scalar.alg",
        "input": "",
        "description": "Euler #4 скалярная версия",
    },
    "vector_demo": {
        "source": "vector_demo.alg",
        "input": "",
        "description": "Демонстрация векторных операций",
    },
}


def compile_program(source_path, output_path):
    """Компиляция программы из .alg в .bin"""
    cmd = [sys.executable, str(TOOLS_DIR / "compile.py"), str(source_path), str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка компиляции {source_path}:")
        print(result.stderr)
        return False
    return True


def run_simulation(bin_path, input_data):
    """Запуск симулятора и получение вывода + журнала"""
    cmd = [sys.executable, str(TOOLS_DIR / "run.py"), str(bin_path)]

    env = os.environ.copy()
    if input_data:
        env["SIMULATOR_INPUT"] = input_data

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        print(f"❌ Ошибка симуляции {bin_path}:")
        print(result.stderr)
        return None, None

    # Вывод и журнал разделяются специальным маркером
    output = result.stdout
    log = result.stderr  # Журнал обычно идет в stderr

    return output, log


def create_golden_test(test_name, test_config):
    """Создание golden-теста для одной программы"""
    print(f"\n🔧 Создание теста: {test_name}")
    print(f"   Описание: {test_config['description']}")

    test_dir = GOLDEN_DIR / test_name
    test_dir.mkdir(parents=True, exist_ok=True)

    source_file = PROGRAMS_DIR / test_config["source"]
    if not source_file.exists():
        print(f"   ❌ Исходный файл не найден: {source_file}")
        return False

    bin_file = test_dir / "machine.bin"
    input_file = test_dir / "input.txt"
    output_file = test_dir / "output.golden"
    log_file = test_dir / "log.golden"
    config_file = test_dir / "config.json"

    # 1. Компиляция
    print("   📦 Компиляция...")
    if not compile_program(source_file, bin_file):
        return False
    print(f"   ✅ Бинарный код: {bin_file.stat().st_size} байт")

    # 2. Входные данные
    input_data = test_config.get("input", "")
    if input_data:
        with open(input_file, "w") as f:
            f.write(input_data)
        print(f"   📥 Входные данные: {len(input_data)} символов")
    else:
        # Пустой файл ввода если нужен
        input_file.touch()

    # 3. Симуляция
    print("   ▶️ Запуск симулятора...")
    output, log = run_simulation(bin_file, input_data)

    if output is None:
        return False

    # 4. Сохранение результатов
    with open(output_file, "w") as f:
        f.write(output)
    print(f"   💾 Вывод сохранен: {len(output)} символов")

    # Адаптация журнала (оставляем только важные строки)
    adapted_log = adapt_log(log, test_name)
    with open(log_file, "w") as f:
        f.write(adapted_log)
    print(f"   📋 Журнал адаптирован: {len(adapted_log)} байт")

    # 5. Конфигурация
    config_content = f'''{{
    "name": "{test_name}",
    "description": "{test_config["description"]}",
    "source": "{test_config["source"]}",
    "input_file": "input.txt",
    "output_file": "output.golden",
    "log_file": "log.golden",
    "binary_file": "machine.bin"
}}
'''
    with open(config_file, "w") as f:
        f.write(config_content)

    print("   ✅ Тест создан успешно!")
    return True


def adapt_log(full_log, test_name):
    """Адаптация журнала: оставляем только ключевые события"""
    lines = full_log.split("\n")
    adapted = []

    # Заголовок
    adapted.append(f"=== Journal for {test_name} ===")
    adapted.append("")

    key_events = ["START", "HALT", "OUT", "IN", "JMP", "CALL", "RET", "VADD", "VMUL", "VCMP"]

    tick_count = 0
    for line in lines:
        if not line.strip():
            continue

        # Оставляем первые и последние такты
        if "TICK" in line or "PC=" in line:
            tick_count += 1
            # Показываем каждый 10-й такт или ключевые события
            if tick_count % 10 == 0 or any(ev in line for ev in key_events):
                adapted.append(line)
        elif any(ev in line for ev in key_events):
            adapted.append(line)
        elif "REGISTERS" in line or "FLAGS" in line:
            # Показываем состояния регистров только при HALT
            if "HALT" in "".join(lines[max(0, lines.index(line) - 5) : lines.index(line) + 1]):
                adapted.append(line)

    # Если журнал слишком большой, показываем статистику
    if len(adapted) > 100:
        adapted = (
            adapted[:50] + [f"\n... ({len(adapted) - 100} строк пропущено) ..."] + adapted[-50:]
        )

    return "\n".join(adapted)


def main():
    print("🚀 Генерация Golden-тестов для лабораторной работы №4")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, test_config in TESTS.items():
        if create_golden_test(test_name, test_config):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"✅ Успешно: {passed}")
    print(f"❌ Ошибки: {failed}")
    print(f"📊 Всего: {passed + failed}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
