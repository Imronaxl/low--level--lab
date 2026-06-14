"""
Модуль кодирования/декодирования инструкций в бинарный формат.

Формат CISC с переменной длиной:
- Первый байт: [OPCODE:6 бит][MOD:2 бита]
- MOD определяет количество и тип последующих байтов

MOD значения:
- 00: Регистр-Регистр (1 байт операндов)
- 01: Регистр-Непосредственный (3 байта: reg + 16-bit imm)
- 10: Регистр-Память (3 байта: reg + 16-bit addr)
- 11: Векторная инструкция (доп. байт для векторных операндов)
"""

import struct
from enum import IntEnum

from .instructions import Instruction, OpCode

# Alias для совместимости
Opcode = OpCode


class OperandType(IntEnum):
    REGISTER = 0
    VECTOR_REG = 1
    IMMEDIATE = 2
    MEMORY = 3
    PORT = 4


class Operand:
    def __init__(self, type: OperandType, value: int):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Operand({self.type.name}, {self.value})"


# Константы
NUM_GPR = 8  # R0-R7
NUM_VR = 8  # V0-V7


def encode_instruction(instr: Instruction) -> bytes:
    """Кодирует инструкцию в бинарный формат (little-endian)."""
    result = bytearray()

    opcode = instr.opcode
    operands = instr.operands

    # Для IN/OUT и векторных инструкций используем отдельные диапазоны opcode
    # чтобы избежать конфликтов с MOD битами
    if opcode in [OpCode.VADD, OpCode.VSUB, OpCode.VMUL, OpCode.VCMP, OpCode.VLOAD, OpCode.VSTORE]:
        # Векторные инструкции: opcode в диапазоне 0x58-0x5F
        # Используем полный opcode без модификации (MOD биты уже часть opcode)
        result.append(opcode.value)

        # Кодируем операнды в зависимости от типа инструкции
        if opcode in [OpCode.VADD, OpCode.VSUB, OpCode.VMUL, OpCode.VCMP]:
            if len(operands) >= 3:
                vd = operands[0].value & 0x07
                vs1 = operands[1].value & 0x07
                vs2 = operands[2].value & 0x07
                vec_byte = (vd << 5) | (vs1 << 2) | vs2
                result.append(vec_byte)
        elif opcode in [OpCode.VLOAD, OpCode.VSTORE]:
            if len(operands) >= 2:
                vn = operands[0].value & 0x07
                addr = operands[1].value & 0xFFFF
                result.append(vn)
                result.extend(struct.pack("<H", addr))
        return bytes(result)

    elif opcode in [OpCode.IN, OpCode.OUT]:
        # I/O инструкции: используем полный opcode без маскирования MOD битов
        # Формат: [OPCODE_FULL] [operand1] [operand2]
        result.append(opcode.value)  # Сохраняем полный opcode (0x40 или 0x41)

        if opcode == OpCode.IN:
            if len(operands) >= 2:
                reg = (
                    operands[0].value & 0x07
                    if hasattr(operands[0], "value")
                    else operands[0] & 0x07
                )
                port = (
                    operands[1].value & 0xFF
                    if hasattr(operands[1], "value")
                    else operands[1] & 0xFF
                )
                result.append(reg)
                result.append(port)
        else:  # OUT
            if len(operands) >= 2:
                port = (
                    operands[0].value & 0xFF
                    if hasattr(operands[0], "value")
                    else operands[0] & 0xFF
                )
                reg = (
                    operands[1].value & 0x07
                    if hasattr(operands[1], "value")
                    else operands[1] & 0x07
                )
                result.append(port)
                result.append(reg)
        return bytes(result)

    # Для остальных инструкций используем MOD биты
    if len(operands) >= 2 and operands[1].type == OperandType.IMMEDIATE:
        mod = 0b01  # Непосредственный операнд
    elif len(operands) >= 2 and operands[1].type == OperandType.MEMORY:
        mod = 0b10  # Память
    else:
        mod = 0b00  # Регистр-Регистр

    # Первый байт: [OPCODE:6][MOD:2] -> сдвигаем opcode на 2 бита влево, mod в младшие 2 бита
    first_byte = ((opcode.value & 0x3F) << 2) | (mod & 0x03)
    result.append(first_byte)

    # Кодируем операнды в зависимости от типа инструкции
    if opcode in [OpCode.LOAD, OpCode.STORE]:
        # LOAD R, #imm или LOAD R, [addr]
        if len(operands) >= 2:
            reg = operands[0].value & 0x07
            if mod == 0b01:  # Immediate
                imm = operands[1].value & 0xFFFF
                result.append(reg)
                result.extend(struct.pack("<H", imm))
            elif mod == 0b10:  # Memory
                addr = operands[1].value & 0xFFFF
                result.append(reg)
                result.extend(struct.pack("<H", addr))
    elif opcode in [OpCode.JMP, OpCode.JZ, OpCode.JNZ, OpCode.JG, OpCode.JL, OpCode.CALL]:
        # Переходы: 16-bit адрес
        if len(operands) >= 1:
            addr = operands[0].value & 0xFFFF
            result.extend(struct.pack("<H", addr))
    elif opcode in [OpCode.IN, OpCode.OUT]:
        # IN R, port или OUT port, R
        if len(operands) >= 2:
            if opcode == OpCode.IN:
                reg = operands[0].value & 0x07
                port = operands[1].value & 0xFF
                result.append(reg)
                result.append(port)
            else:  # OUT
                port = operands[0].value & 0xFF
                reg = operands[1].value & 0x07
                result.append(port)
                result.append(reg)
    elif opcode in [
        OpCode.ADD,
        OpCode.SUB,
        OpCode.MUL,
        OpCode.DIV,
        OpCode.AND,
        OpCode.OR,
        OpCode.XOR,
        OpCode.CMP,
    ]:
        # Арифметика/Логика: зависит от MOD
        if len(operands) >= 3:
            dest = operands[0].value & 0x07
            src1 = operands[1].value & 0x07
            if mod == 0b00:  # Reg, Reg, Reg
                src2 = operands[2].value & 0x07
                result.append((dest << 5) | (src1 << 2) | src2)
            elif mod == 0b01:  # Reg, Reg, Imm
                imm = operands[2].value & 0xFFFF
                result.append((dest << 5) | (src1 << 2))
                result.extend(struct.pack("<H", imm))
            elif mod == 0b10:  # Reg, Reg, [Addr]
                addr = operands[2].value & 0xFFFF
                result.append((dest << 5) | (src1 << 2))
                result.extend(struct.pack("<H", addr))
    elif opcode == OpCode.MOV:
        # MOV: зависит от MOD
        if len(operands) >= 2:
            dest = operands[0].value & 0x07
            if mod == 0b01:  # Reg, Imm - используем 16-bit immediate
                imm = operands[1].value & 0xFFFF
                result.append(dest)
                result.extend(struct.pack("<H", imm))  # 2 байта
            elif mod == 0b10:  # Reg, [Addr]
                addr = operands[1].value & 0xFFFF
                result.append(dest)
                result.extend(struct.pack("<H", addr))
            elif mod == 0b00:  # Reg, Reg
                src = operands[1].value & 0x07
                result.append((dest << 5) | src)
    elif opcode in [OpCode.NOP, OpCode.HALT, OpCode.RET]:
        pass  # Нет операндов

    return bytes(result)


def decode_instruction(data: bytes, address: int = 0) -> tuple[Instruction | None, int]:
    """Декодирует инструкцию из бинарных данных. Возвращает (инструкция, длина)."""
    if len(data) < 1:
        return None, 0

    first_byte = data[0]

    # Проверяем специальные диапазоны opcode (I/O и векторные)
    if first_byte >= 0x40 and first_byte <= 0x4F:
        # I/O инструкции: IN/OUT (0x40, 0x41)
        opcode_val = first_byte
        try:
            opcode = Opcode(opcode_val)
        except ValueError:
            return None, 0

        operands = []
        if opcode == OpCode.IN:
            if len(data) < 3:
                return None, 0
            reg = data[1] & 0x07
            port = data[2]
            operands = [
                Operand(OperandType.REGISTER, reg),
                Operand(OperandType.PORT, port),
            ]
            return Instruction(opcode=opcode, operands=operands, address=address, length=3), 3
        elif opcode == OpCode.OUT:
            if len(data) < 3:
                return None, 0
            port = data[1]
            reg = data[2] & 0x07
            operands = [
                Operand(OperandType.PORT, port),
                Operand(OperandType.REGISTER, reg),
            ]
            return Instruction(opcode=opcode, operands=operands, address=address, length=3), 3

    elif first_byte >= 0x58 and first_byte <= 0x5F:
        # Векторные инструкции (0x58-0x5F)
        try:
            opcode = Opcode(first_byte)
        except ValueError:
            return None, 0

        operands = []
        if opcode in [OpCode.VADD, OpCode.VSUB, OpCode.VMUL, OpCode.VCMP]:
            if len(data) < 2:
                return None, 0
            vec_byte = data[1]
            vd = (vec_byte >> 5) & 0x07
            vs1 = (vec_byte >> 2) & 0x07
            vs2 = vec_byte & 0x03
            operands = [
                Operand(OperandType.VECTOR_REG, vd),
                Operand(OperandType.VECTOR_REG, vs1),
                Operand(OperandType.VECTOR_REG, vs2),
            ]
            return Instruction(opcode=opcode, operands=operands, address=address, length=2), 2
        elif opcode in [OpCode.VLOAD, OpCode.VSTORE]:
            if len(data) < 4:
                return None, 0
            vn = data[1]
            addr = struct.unpack("<H", data[2:4])[0]
            operands = [
                Operand(OperandType.VECTOR_REG, vn),
                Operand(OperandType.MEMORY, addr),
            ]
            return Instruction(opcode=opcode, operands=operands, address=address, length=4), 4

    # Стандартные инструкции с MOD битами
    # Формат: [OPCODE:6 бит][MOD:2 бита] -> opcode в старших 6 битах, mod в младших 2
    opcode_val = (first_byte >> 2) & 0x3F
    mod = first_byte & 0x03

    try:
        opcode = Opcode(opcode_val)
    except ValueError:
        return None, 0

    operands = []
    length = 1
    offset = 1

    if opcode in [OpCode.VADD, OpCode.VSUB, OpCode.VMUL, OpCode.VCMP]:
        if len(data) < offset + 1:
            return None, 0
        vec_byte = data[offset]
        vd = (vec_byte >> 5) & 0x07
        vs1 = (vec_byte >> 2) & 0x07
        vs2 = vec_byte & 0x03
        operands = [
            Operand(OperandType.VECTOR_REG, vd),
            Operand(OperandType.VECTOR_REG, vs1),
            Operand(OperandType.VECTOR_REG, vs2),
        ]
        length = 2
    elif opcode in [OpCode.VLOAD, OpCode.VSTORE]:
        if len(data) < offset + 3:
            return None, 0
        vn = data[offset]
        addr = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
        operands = [
            Operand(OperandType.VECTOR_REG, vn),
            Operand(OperandType.MEMORY, addr),
        ]
        length = 4
    elif opcode in [OpCode.LOAD, OpCode.STORE]:
        if mod == 0b01 or mod == 0b10:
            if len(data) < offset + 3:
                return None, 0
            reg = data[offset] & 0x07
            value = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
            op_type = OperandType.IMMEDIATE if mod == 0b01 else OperandType.MEMORY
            operands = [
                Operand(OperandType.REGISTER, reg),
                Operand(op_type, value),
            ]
            length = 4
    elif opcode == OpCode.MOV:
        if mod == 0b01:  # MOV R, #imm
            if len(data) < offset + 3:
                return None, 0
            reg = data[offset] & 0x07
            imm = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
            operands = [
                Operand(OperandType.REGISTER, reg),
                Operand(OperandType.IMMEDIATE, imm),
            ]
            length = 4
        elif mod == 0b10:  # MOV R, [addr]
            if len(data) < offset + 3:
                return None, 0
            reg = data[offset] & 0x07
            addr = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
            operands = [
                Operand(OperandType.REGISTER, reg),
                Operand(OperandType.MEMORY, addr),
            ]
            length = 4
        elif mod == 0b00:  # MOV R, R
            if len(data) < offset + 1:
                return None, 0
            byte2 = data[offset]
            dest = (byte2 >> 5) & 0x07
            src = byte2 & 0x07
            operands = [
                Operand(OperandType.REGISTER, dest),
                Operand(OperandType.REGISTER, src),
            ]
            length = 2
    elif opcode in [OpCode.JMP, OpCode.JZ, OpCode.JNZ, OpCode.JG, OpCode.JL, OpCode.CALL]:
        if len(data) < offset + 2:
            return None, 0
        addr = struct.unpack("<H", data[offset : offset + 2])[0]
        operands = [Operand(OperandType.IMMEDIATE, addr)]
        length = 3
    elif opcode == OpCode.IN:
        if len(data) < offset + 2:
            return None, 0
        reg = data[offset] & 0x07
        port = data[offset + 1]
        operands = [
            Operand(OperandType.REGISTER, reg),
            Operand(OperandType.PORT, port),
        ]
        length = 3
    elif opcode == OpCode.OUT:
        if len(data) < offset + 2:
            return None, 0
        port = data[offset]
        reg = data[offset + 1] & 0x07
        operands = [
            Operand(OperandType.PORT, port),
            Operand(OperandType.REGISTER, reg),
        ]
        length = 3
    elif opcode in [
        OpCode.ADD,
        OpCode.SUB,
        OpCode.MUL,
        OpCode.DIV,
        OpCode.AND,
        OpCode.OR,
        OpCode.XOR,
        OpCode.CMP,
    ]:
        if mod == 0b00:
            if len(data) < offset + 1:
                return None, 0
            byte2 = data[offset]
            dest = (byte2 >> 5) & 0x07
            src1 = (byte2 >> 2) & 0x07
            src2 = byte2 & 0x03
            operands = [
                Operand(OperandType.REGISTER, dest),
                Operand(OperandType.REGISTER, src1),
                Operand(OperandType.REGISTER, src2),
            ]
            length = 2
        elif mod == 0b01 or mod == 0b10:
            if len(data) < offset + 3:
                return None, 0
            byte2 = data[offset]
            dest = (byte2 >> 5) & 0x07
            src1 = (byte2 >> 2) & 0x03
            value = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
            op_type = OperandType.IMMEDIATE if mod == 0b01 else OperandType.MEMORY
            operands = [
                Operand(OperandType.REGISTER, dest),
                Operand(OperandType.REGISTER, src1),
                Operand(op_type, value),
            ]
            length = 4
    elif opcode in [OpCode.NOP, OpCode.HALT, OpCode.RET]:
        pass  # Нет операндов

    instr = Instruction(opcode=opcode, operands=operands, address=address, length=length)
    return instr, length


def encode_program(instructions: list[Instruction]) -> bytes:
    """Кодирует список инструкций в бинарный формат программы."""
    result = bytearray()
    for instr in instructions:
        encoded = encode_instruction(instr)
        result.extend(encoded)
    return bytes(result)


def disassemble_to_text(instructions: list[Instruction]) -> str:
    """Генерирует текстовый дамп инструкций в формате: addr - hex - mnemonic"""
    lines = []
    for instr in instructions:
        # Кодируем обратно для получения hex
        encoded = encode_instruction(instr)
        hex_str = encoded.hex().upper()
        # Формируем мнемонику
        ops_str = ", ".join(format_operand(op) for op in instr.operands)
        mnemonic = f"{instr.opcode.name} {ops_str}" if ops_str else instr.opcode.name
        lines.append(f"{instr.address:04X} - {hex_str:<8} - {mnemonic}")
    return "\n".join(lines)


def format_operand(op: Operand) -> str:
    """Форматирует операнд для вывода."""
    if op.type == OperandType.REGISTER:
        return f"R{op.value}"
    elif op.type == OperandType.VECTOR_REG:
        return f"V{op.value}"
    elif op.type == OperandType.IMMEDIATE:
        return f"#{op.value}"
    elif op.type == OperandType.MEMORY:
        return f"[{op.value:#06X}]"
    elif op.type == OperandType.PORT:
        return f"PORT{op.value:#04X}"
    return str(op.value)
