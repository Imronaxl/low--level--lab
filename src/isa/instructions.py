"""
Определение системы команд (ISA) для варианта:
CISC | Vector | Port-mapped I/O | Von Neumann

Формат инструкций (переменная длина):
- Байт 0: [OPCODE:6 бит][MOD:2 бита]
- Байт 1+: Операнды в зависимости от MOD
  - MOD=00: Регистр-Регистр (1 байт доп)
  - MOD=01: Регистр-Немедленное (2 байта доп: рег + imm8)
  - MOD=10: Регистр-Память (3 байта доп: рег + addr16)
  - MOD=11: Векторная операция (специальный формат)
"""

from dataclasses import dataclass
from enum import IntEnum


class OpCode(IntEnum):
    # Базовые (0x00-0x0F) - должны быть < 64 для 6-битного поля
    NOP = 0x00
    HALT = 0x01
    MOV = 0x02

    # Арифметика (0x04-0x0F)
    ADD = 0x04
    SUB = 0x05
    MUL = 0x06
    DIV = 0x07
    AND = 0x08
    OR = 0x09
    XOR = 0x0A
    NOT = 0x0B

    # Сравнение
    CMP = 0x0C

    # Переходы (0x10-0x1F)
    JMP = 0x10
    JZ = 0x11
    JNZ = 0x12
    JL = 0x13
    JG = 0x14
    CALL = 0x15
    RET = 0x16

    # Стек
    PUSH = 0x18
    POP = 0x19

    # Память (0x20-0x2F)
    LOAD = 0x20
    STORE = 0x21

    # Ввод-Вывод (Port-mapped) (0x40-0x4F) - должны быть >= 0x40 для декодера
    IN = 0x40
    OUT = 0x41

    # Векторные (0x50-0x5F) - должны быть < 64
    VLOAD = 0x50
    VSTORE = 0x51
    VADD = 0x52
    VSUB = 0x53
    VMUL = 0x54
    VDIV = 0x55
    VCMP = 0x56
    VSET = 0x57  # Заполнение вектора скаляром


@dataclass
class Instruction:
    opcode: OpCode
    operands: list[int | str]
    mod: int = 0  # Режим адресации
    address: int = 0  # Адрес в памяти
    length: int = 0  # Длина инструкции в байтах

    def __repr__(self):
        ops = ", ".join(str(o) for o in self.operands)
        return f"{self.opcode.name} {ops}"


class AddrMode(IntEnum):
    REG = 0  # Регистр-Регистр
    IMM = 1  # Регистр-Немедленное
    MEM = 2  # Регистр-Память (прямая адресация)
    DIR = 3  # Прямая адресация для JMP/CALL
    VEC = 4  # Векторный режим


# Флаги процессора
FLAG_Z = 0x01  # Zero flag
FLAG_N = 0x02  # Negative flag
FLAG_C = 0x04  # Carry flag
FLAG_V = 0x08  # Overflow flag
