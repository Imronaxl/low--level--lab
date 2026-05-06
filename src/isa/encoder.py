"""
Кодирование инструкций в бинарный формат (CISC, переменная длина)
Формат: [OPCODE:6][MOD:2] + операнды
"""

import struct

from .instructions import AddrMode, Instruction, OpCode


class Encoder:
    @staticmethod
    def encode(inst: Instruction) -> bytes:
        """Кодирует инструкцию в байты"""
        opcode = inst.opcode.value
        mod = inst.mod

        # Специальные инструкции (IN/OUT, векторные) используют полный байт opcode
        if inst.opcode in (OpCode.IN, OpCode.OUT):
            # Формат: [opcode][port][reg] - 3 байта
            port, reg = inst.operands[0], inst.operands[1]
            return bytes([opcode, port & 0xFF, reg & 0xFF])

        if inst.opcode.value >= 0x50 and inst.opcode.value <= 0x5F:
            # Векторные инструкции: [opcode][vec_byte]
            vd, vs1, vs2 = inst.operands[0], inst.operands[1], inst.operands[2]
            vec_byte = ((vd & 0x03) << 4) | ((vs1 & 0x03) << 2) | (vs2 & 0x03)
            return bytes([opcode, vec_byte])

        # Стандартные инструкции с MOD битами
        # Первый байт: [OPCODE:6][MOD:2]
        byte0 = ((opcode & 0x3F) << 2) | (mod & 0x03)
        result = bytearray([byte0])

        if inst.opcode == OpCode.HALT or inst.opcode == OpCode.NOP:
            # Инструкции без операндов
            pass
        elif mod == AddrMode.REG:
            # Регистр-Регистр: 1 байт [Rd:2][Rs:2][RFU:4]
            rd, rs = inst.operands[0], inst.operands[1]
            byte1 = ((rd & 0x03) << 4) | (rs & 0x03)
            result.append(byte1)

        elif mod == AddrMode.IMM:
            # Регистр-Немедленное: 2 байта [Rd:2][RFU:6], [Imm:8]
            rd, imm = inst.operands[0], inst.operands[1]
            byte1 = (rd & 0x03) << 4
            result.append(byte1)
            result.append(imm & 0xFF)

        elif mod == AddrMode.MEM:
            # Регистр-Память: 3 байта [Rd:2][RFU:6], [Addr:16]
            rd, addr = inst.operands[0], inst.operands[1]
            byte1 = (rd & 0x03) << 4
            result.append(byte1)
            result.extend(struct.pack("<H", addr & 0xFFFF))

        elif mod == AddrMode.DIR:
            # Прямая адресация (JMP, CALL): 2 байта адреса
            addr = inst.operands[0]
            result.extend(struct.pack("<H", addr & 0xFFFF))

        elif mod == AddrMode.VEC:
            # Векторный режим: 2 байта [Vd:2][Vs1:2][Vs2:2][RFU:2]
            vd, vs1, vs2 = inst.operands[0], inst.operands[1], inst.operands[2]
            byte1 = ((vd & 0x03) << 4) | ((vs1 & 0x03) << 2) | (vs2 & 0x03)
            result.append(byte1)

        return bytes(result)

    @staticmethod
    def encode_program(instructions: list[Instruction]) -> bytes:
        """Кодирует программу из списка инструкций"""
        result = bytearray()
        for inst in instructions:
            result.extend(Encoder.encode(inst))
        return bytes(result)
