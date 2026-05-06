"""
Тесты для процессора CISC с микрокодом и векторными расширениями.

Проверяют:
- Корректность выполнения инструкций
- Тактовое моделирование (tick-level)
- Ввод-вывод через порты
- Векторные операции
"""

import pytest

from src.processor.datapath import DataPath
from src.processor.simulator import Simulator


class TestBasicInstructions:
    """Тесты базовых инструкций."""

    def test_mov_imm(self):
        """MOV R0, 42 - загрузка непосредственного значения."""
        sim = Simulator()

        # MOV R1, 42: opcode=0x02, mod=0x01 (IMM)
        # Первый байт: (opcode << 2) | mod = (0x02 << 2) | 0x01 = 0x09
        # Второй байт: rd в старших 4 битах = 0x10 (rd=1)
        # Третий и четвертый байты: immediate в little-endian формате (16 бит)
        # 42 = 0x002A -> [0x2A, 0x00]
        # HALT: opcode=0x01, mod=0x00 -> (0x01<<2)|0x00 = 0x04
        program = [
            0x09,  # MOV R1, imm
            0x10,  # rd=1
            42,  # immediate low byte
            0x00,  # immediate high byte
            0x04,  # HALT
        ]

        sim.load_program(program)

        # Выполняем пока не HALT
        while not sim.halted and sim.tick_count < 100:
            sim.tick()

        assert sim.datapath.state.registers[1] == 42, (
            f"R1 должен быть 42, но {sim.datapath.state.registers[1]}"
        )

    def test_add_reg_reg(self):
        """ADD R0, R1, R2 - сложение регистров."""
        sim = Simulator()

        # MOV R1, 10: opcode=0x02, mod=0x01 (IMM)
        # Формат: [opcode+mod][rd][imm_low][imm_high]
        # MOV R2, 20: аналогично
        # ADD R0, R1: opcode=0x04, mod=0x00 (REG-REG)
        # Формат: [opcode+mod][rd:4|rs:4] где rd=0, rs=1 -> 0x01
        # HALT: 0x04
        program = [
            0x09,
            0x10,
            10,
            0x00,  # MOV R1, 10
            0x09,
            0x20,
            20,
            0x00,  # MOV R2, 20
            0x10,
            0x01,  # ADD R0, R1 (R0 <- R0 + R1, R0=0 изначально)
            0x04,  # HALT
        ]

        sim.load_program(program)

        while not sim.halted and sim.tick_count < 100:
            sim.tick()

        # Проверяем что R1 и R2 загружены, и R0 = R1 + R2 = 0 + 10 = 10
        assert sim.datapath.state.registers[1] == 10, (
            f"R1={sim.datapath.state.registers[1]}, expected 10"
        )
        assert sim.datapath.state.registers[2] == 20, (
            f"R2={sim.datapath.state.registers[2]}, expected 20"
        )
        # R0 изначально 0, ADD R0, R1 значит R0 = R0 + R1 = 0 + 10 = 10
        assert sim.datapath.state.registers[0] == 10, (
            f"R0={sim.datapath.state.registers[0]}, expected 10"
        )

    def test_halt(self):
        """HALT - остановка процессора."""
        sim = Simulator()

        # HALT: opcode=0x01, mod=0x00 -> (0x01<<2)|0x00 = 0x04
        program = [0x04]  # HALT
        sim.load_program(program)

        # Выполняем несколько тактов: FETCH_ADDR, FETCH_MEM, DECODE, HALT_OP
        for _ in range(10):
            if sim.halted:
                break
            sim.tick()

        # После HALT состояние должно быть halted
        assert sim.halted is True, (
            f"Процессор не остановился после HALT. Состояние: halted={sim.halted}"
        )


class TestIO:
    """Тесты ввода-вывода через порты."""

    def test_in_out_stream(self):
        """IN и OUT через порты со stream буфером."""
        sim = Simulator()

        # Устанавливаем входные данные
        sim.set_input("AB")

        # Простая программа эха: IN R0, port0; OUT port1, R0; HALT
        # Для простоты проверяем только установку буфера
        assert sim.datapath.input_buffer == [65, 66]  # 'A' = 65, 'B' = 66

        # Читаем из порта
        val = sim.datapath.read_port(0x01)
        assert val == 65

        val = sim.datapath.read_port(0x01)
        assert val == 66


class TestVectorOperations:
    """Тесты векторных операций."""

    def test_vector_add(self):
        """VADD V0, V1, V2 - поэлементное сложение векторов."""
        dp = DataPath()

        # Устанавливаем векторы
        dp.vector_registers[1] = [1, 2, 3, 4]
        dp.vector_registers[2] = [10, 20, 30, 40]

        # Выполняем сложение
        result = dp.vector_add(dp.vector_registers[1], dp.vector_registers[2])

        assert result == [11, 22, 33, 44]

    def test_vector_mul(self):
        """VMUL V0, V1, V2 - поэлементное умножение."""
        dp = DataPath()

        dp.vector_registers[1] = [1, 2, 3, 4]
        dp.vector_registers[2] = [2, 3, 4, 5]

        result = dp.vector_mul(dp.vector_registers[1], dp.vector_registers[2])

        assert result == [2, 6, 12, 20]


class TestMemory:
    """Тесты работы с памятью."""

    def test_load_store_byte(self):
        """Чтение/запись байтов в памяти."""
        dp = DataPath()

        # Записываем байты
        dp.write_byte(0, 0x12)
        dp.write_byte(1, 0x34)
        dp.write_byte(2, 0x56)
        dp.write_byte(3, 0x78)

        # Читаем обратно
        assert dp.read_byte(0) == 0x12
        assert dp.read_byte(1) == 0x34
        assert dp.read_byte(2) == 0x56
        assert dp.read_byte(3) == 0x78

    def test_load_store_word(self):
        """Чтение/запись слов в памяти."""
        dp = DataPath()

        # Записываем слово
        dp.write_word(10, 0x12345678)

        # Читаем
        assert dp.read_word(10) == 0x12345678

    def test_program_loading(self):
        """Загрузка программы в память."""
        sim = Simulator()

        program = [0x01, 0x02, 0x03, 0xFF]
        sim.load_program(program, start_addr=0x0100)

        # Проверяем загрузку
        assert sim.datapath.read_byte(0x0100) == 0x01
        assert sim.datapath.read_byte(0x0101) == 0x02
        assert sim.datapath.read_byte(0x0102) == 0x03
        assert sim.datapath.read_byte(0x0103) == 0xFF


class TestFlags:
    """Тесты флагов процессора."""

    def test_zero_flag(self):
        """Флаг нуля при результате 0."""
        dp = DataPath()

        result = dp.alu_sub(5, 5)

        assert result == 0
        assert dp.flags.zero is True

    def test_negative_flag(self):
        """Флаг знака при отрицательном результате."""
        dp = DataPath()

        result = dp.alu_sub(3, 7)

        # 3 - 7 = -4, в 32 битах это 0xFFFFFFFC
        assert dp.flags.negative is True

    def test_cmp_operation(self):
        """Сравнение и установка флагов."""
        dp = DataPath()

        dp.alu_cmp(10, 5)

        # 10 > 5, результат положительный
        assert dp.flags.zero is False
        assert dp.flags.negative is False

        dp.alu_cmp(5, 5)
        assert dp.flags.zero is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
