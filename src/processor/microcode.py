"""
Микрокод для Control Unit (microcoded)
Каждая инструкция разбивается на микрооперации (такты)
"""

from enum import IntEnum, auto


class MicroOp(IntEnum):
    FETCH_ADDR = auto()
    FETCH_MEM = auto()
    DECODE = auto()
    REG_READ_A = auto()
    REG_READ_B = auto()
    REG_WRITE = auto()
    REG_WRITE_IMM = auto()
    ALU_SET_A = auto()
    ALU_SET_B = auto()
    ALU_ADD = auto()
    ALU_SUB = auto()
    ALU_MUL = auto()
    ALU_DIV = auto()
    ALU_AND = auto()
    ALU_OR = auto()
    ALU_XOR = auto()
    ALU_NOT = auto()
    ALU_CMP = auto()
    MEM_READ = auto()
    MEM_WRITE = auto()
    JMP = auto()
    JZ = auto()
    JNZ = auto()
    JL = auto()
    JG = auto()
    IO_READ = auto()
    IO_WRITE = auto()
    VREG_READ = auto()
    VREG_WRITE = auto()
    VALU_ADD = auto()
    VALU_MUL = auto()
    VALU_CMP = auto()
    HALT = auto()
    NOP = auto()


# Микропрограммы: opcode -> список микроопераций
# Соответствие OpCode из instructions.py:
# MOV=0x02, ADD=0x04, SUB=0x05, MUL=0x06, DIV=0x07
# AND=0x08, OR=0x09, XOR=0x0A, NOT=0x0B, CMP=0x0C
# JMP=0x10, JZ=0x11, JNZ=0x12, JL=0x13, JG=0x14
# LOAD=0x20, STORE=0x21
# IN=0x40, OUT=0x41
# VLOAD=0x50, VSTORE=0x51, VADD=0x52, VSUB=0x53, VMUL=0x54, VDIV=0x55, VCMP=0x56, VSET=0x57

MICROCODE: dict[int, list[MicroOp]] = {
    # Базовые
    0x00: [MicroOp.NOP],
    0x01: [MicroOp.HALT],
    0x02: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.REG_WRITE_IMM],
    # Арифметика (MOD зависит от операндов, обработка в decoder)
    0x04: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_ADD,
        MicroOp.REG_WRITE,
    ],
    0x05: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_SUB,
        MicroOp.REG_WRITE,
    ],
    0x06: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_MUL,
        MicroOp.REG_WRITE,
    ],
    0x07: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_DIV,
        MicroOp.REG_WRITE,
    ],
    0x08: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_AND,
        MicroOp.REG_WRITE,
    ],
    0x09: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_OR,
        MicroOp.REG_WRITE,
    ],
    0x0A: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_XOR,
        MicroOp.REG_WRITE,
    ],
    0x0B: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_NOT,
        MicroOp.REG_WRITE,
    ],
    # Сравнение
    0x0C: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_CMP,
    ],
    # Переходы
    0x10: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.JMP],
    0x11: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.JZ],
    0x12: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.JNZ],
    0x13: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.JL],
    0x14: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.JG],
    # Память
    0x20: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.MEM_READ,
        MicroOp.REG_WRITE,
    ],
    0x21: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.MEM_WRITE,
    ],
    # Ввод-Вывод (Port-mapped)
    0x40: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.IO_READ,
        MicroOp.REG_WRITE,
    ],
    0x41: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.IO_WRITE],
    # Векторные операции
    0x52: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ,
        MicroOp.VALU_ADD,
        MicroOp.VREG_WRITE,
    ],
    0x53: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ,
        MicroOp.ALU_SUB,
        MicroOp.VREG_WRITE,
    ],
    0x54: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ,
        MicroOp.VALU_MUL,
        MicroOp.VREG_WRITE,
    ],
    0x55: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ,
        MicroOp.ALU_DIV,
        MicroOp.VREG_WRITE,
    ],
    0x56: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ,
        MicroOp.VALU_CMP,
    ],
    0x57: [MicroOp.FETCH_ADDR, MicroOp.FETCH_MEM, MicroOp.DECODE, MicroOp.VREG_WRITE],
}
