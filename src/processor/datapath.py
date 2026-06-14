"""
DataPath процессора: регистры, ALU, память, векторные блоки
Архитектура: CISC, Von Neumann, Vector extensions
"""

from dataclasses import dataclass, field


@dataclass
class DataPathState:
    """Состояние всех элементов DataPath"""

    # Регистры общего назначения (4 регистра для упрощения)
    registers: list[int] = field(default_factory=lambda: [0, 0, 0, 0])

    # Векторные регистры (4 регистра x 4 элемента)
    vector_registers: list[list[int]] = field(
        default_factory=lambda: [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    )

    # Специальные регистры
    pc: int = 0  # Program Counter
    acc: int = 0  # Accumulator (для совместимости)
    flags: dict[str, bool] = field(
        default_factory=lambda: {
            "Z": False,  # Zero
            "N": False,  # Negative
            "C": False,  # Carry
            "V": False,  # Overflow
        }
    )

    # Регистры адреса и данных памяти
    mar: int = 0  # Memory Address Register
    mdr: int = 0  # Memory Data Register

    # decoded immediate значение
    decoded_imm: int = 0

    # decoded addressing mode
    decoded_mod: int = 0

    # decoded register operands
    decoded_rd: int = 0
    decoded_rs: int = 0

    # ALU result register
    alu_result: int = 0

    # Порты ввода-вывода
    ports: dict[int, int] = field(default_factory=dict)

    # Буферы ввода-вывода (stream)
    input_buffer: list[int] = field(default_factory=list)
    output_buffer: list[int] = field(default_factory=list)


class DataPath:
    def __init__(self, memory_size: int = 65536):
        self.state = DataPathState()
        self.memory = [0] * memory_size  # Единая память (Von Neumann)
        self.memory_size = memory_size

    # === Регистры ===
    def reg_read(self, reg_num: int) -> int:
        if 0 <= reg_num < len(self.state.registers):
            return self.state.registers[reg_num]
        raise ValueError(f"Неверный номер регистра: {reg_num}")

    def reg_write(self, reg_num: int, value: int):
        if 0 <= reg_num < len(self.state.registers):
            self.state.registers[reg_num] = value & 0xFFFFFFFF  # 32-bit
        else:
            raise ValueError(f"Неверный номер регистра: {reg_num}")

    # === Векторные регистры ===
    def vreg_read(self, vreg_num: int, elem_idx: int = 0) -> int:
        if 0 <= vreg_num < len(self.state.vector_registers):
            if 0 <= elem_idx < 4:
                return self.state.vector_registers[vreg_num][elem_idx]
        raise ValueError("Неверный векторный регистр или индекс")

    def vreg_write(self, vreg_num: int, values: list[int]):
        if 0 <= vreg_num < len(self.state.vector_registers):
            for i in range(min(4, len(values))):
                self.state.vector_registers[vreg_num][i] = values[i] & 0xFFFFFFFF

    def vreg_broadcast(self, vreg_num: int, scalar: int):
        """Заполнить вектор скаляром"""
        if 0 <= vreg_num < len(self.state.vector_registers):
            self.state.vector_registers[vreg_num] = [scalar & 0xFFFFFFFF] * 4

    # === ALU операции ===
    def alu_add(self, a: int, b: int) -> int:
        result = (a + b) & 0xFFFFFFFF
        self._update_flags(result)
        return result

    def alu_sub(self, a: int, b: int) -> int:
        result = (a - b) & 0xFFFFFFFF
        self._update_flags(result)
        return result

    def alu_mul(self, a: int, b: int) -> int:
        result = (a * b) & 0xFFFFFFFF
        self._update_flags(result)
        return result

    def alu_div(self, a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("Деление на ноль")
        result = (a // b) & 0xFFFFFFFF
        self._update_flags(result)
        return result

    def alu_and(self, a: int, b: int) -> int:
        result = a & b
        self._update_flags(result)
        return result

    def alu_or(self, a: int, b: int) -> int:
        result = a | b
        self._update_flags(result)
        return result

    def alu_xor(self, a: int, b: int) -> int:
        result = a ^ b
        self._update_flags(result)
        return result

    def alu_not(self, a: int) -> int:
        result = (~a) & 0xFFFFFFFF
        self._update_flags(result)
        return result

    def alu_cmp(self, a: int, b: int):
        """Сравнение: устанавливает флаги"""
        diff = a - b
        self.state.flags["Z"] = diff == 0
        self.state.flags["N"] = diff < 0

    def _update_flags(self, result: int):
        self.state.flags["Z"] = result == 0
        self.state.flags["N"] = (result & 0x80000000) != 0  # Знаковый бит

    # === Память (Von Neumann) ===
    @property
    def flags(self):
        """Доступ к флагам как объект с атрибутами"""

        class FlagsObj:
            def __init__(self, flags_dict):
                self._flags = flags_dict

            @property
            def zero(self):
                return self._flags.get("Z", False)

            @property
            def negative(self):
                return self._flags.get("N", False)

            @property
            def carry(self):
                return self._flags.get("C", False)

            @property
            def overflow(self):
                return self._flags.get("V", False)

        return FlagsObj(self.state.flags)

    def read_byte(self, addr: int) -> int:
        """Чтение байта по адресу"""
        return self.mem_read(addr) & 0xFF

    def write_byte(self, addr: int, value: int):
        """Запись байта по адресу"""
        self.mem_write(addr, value & 0xFF)

    def read_word(self, addr: int) -> int:
        """Чтение 32-битного слова (little-endian)"""
        b0 = self.mem_read(addr) & 0xFF
        b1 = self.mem_read(addr + 1) & 0xFF
        b2 = self.mem_read(addr + 2) & 0xFF
        b3 = self.mem_read(addr + 3) & 0xFF
        return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0

    def write_word(self, addr: int, value: int):
        """Запись 32-битного слова (little-endian)"""
        self.mem_write(addr, value & 0xFF)
        self.mem_write(addr + 1, (value >> 8) & 0xFF)
        self.mem_write(addr + 2, (value >> 16) & 0xFF)
        self.mem_write(addr + 3, (value >> 24) & 0xFF)

    def mem_read(self, addr: int) -> int:
        if 0 <= addr < self.memory_size:
            return self.memory[addr]
        raise ValueError(f"Неверный адрес памяти: {addr}")

    def mem_write(self, addr: int, value: int):
        if 0 <= addr < self.memory_size:
            self.memory[addr] = value & 0xFFFFFFFF
        else:
            raise ValueError(f"Неверный адрес памяти: {addr}")

    def load_program(self, code: bytes, start_addr: int = 0x0100):
        """Загрузка программы в память (байт за байтом)"""
        # Устанавливаем PC в адрес начала программы
        self.state.pc = start_addr
        for i, byte in enumerate(code):
            self.mem_write(start_addr + i, byte)

    # === Ввод-Вывод (Port-mapped) ===
    def port_read(self, port_addr: int) -> int:
        """Чтение из порта ввода"""
        if port_addr == 0x01:  # STDIN
            if self.state.input_buffer:
                return self.state.input_buffer.pop(0)
            return 0  # Нет данных
        return self.state.ports.get(port_addr, 0)

    def port_write(self, port_addr: int, value: int):
        """Запись в порт вывода"""
        if port_addr == 0x02:  # STDOUT
            self.state.output_buffer.append(value & 0xFF)
        else:
            self.state.ports[port_addr] = value & 0xFFFFFFFF

    # Методы для совместимости с тестами
    def read_port(self, port_addr: int) -> int:
        return self.port_read(port_addr)

    def write_port(self, port_addr: int, value: int):
        self.port_write(port_addr, value)

    # === Векторные операции ===
    def vector_add(self, v1: list[int], v2: list[int]) -> list[int]:
        """Поэлементное сложение векторов"""
        return [(a + b) & 0xFFFFFFFF for a, b in zip(v1, v2)]

    def vector_sub(self, v1: list[int], v2: list[int]) -> list[int]:
        """Поэлементное вычитание"""
        return [(a - b) & 0xFFFFFFFF for a, b in zip(v1, v2)]

    def vector_mul(self, v1: list[int], v2: list[int]) -> list[int]:
        """Поэлементное умножение"""
        return [(a * b) & 0xFFFFFFFF for a, b in zip(v1, v2)]

    def vector_div(self, v1: list[int], v2: list[int]) -> list[int]:
        """Поэлементное деление"""
        result = []
        for a, b in zip(v1, v2):
            if b == 0:
                raise ZeroDivisionError("Деление на ноль в векторной операции")
            result.append((a // b) & 0xFFFFFFFF)
        return result

    @property
    def vector_registers(self):
        """Прямой доступ к векторным регистрам для тестов"""
        return self.state.vector_registers

    @property
    def input_buffer(self):
        """Прямой доступ к входному буферу для тестов"""
        return self.state.input_buffer

    @property
    def output_buffer(self):
        """Прямой доступ к выходному буферу"""
        return self.state.output_buffer

    def set_input(self, data: str):
        """Установка входного буфера (строка -> список ASCII кодов)"""
        self.state.input_buffer = [ord(c) for c in data]

    def get_output(self) -> str:
        """Получение выходного буфера как строки"""
        return "".join(chr(c & 0xFF) for c in self.state.output_buffer)

    # === Утилиты ===
    def reset(self):
        self.state = DataPathState()

    def get_state_dict(self) -> dict:
        return {
            "pc": self.state.pc,
            "registers": self.state.registers.copy(),
            "vector_registers": [v.copy() for v in self.state.vector_registers],
            "flags": self.state.flags.copy(),
            "output": self.get_output(),
        }
