"""
Декодирование бинарных инструкций (CISC, переменная длина)
"""

from .instructions import AddrMode, Instruction, OpCode


class Decoder:
    def __init__(self):
        self.pc = 0

    def decode(self, code: bytes, pc: int = 0) -> tuple[Instruction | None, int]:
        """
        Декодирует одну инструкцию из байтового кода.
        Возвращает (инструкция, размер_в_байтах)
        """
        if pc >= len(code):
            return None, 0

        byte0 = code[pc]

        # Специальные инструкции используют полный байт opcode (IN/OUT, векторные)
        if byte0 in (OpCode.IN.value, OpCode.OUT.value):
            # Формат: [opcode][port][reg] - 3 байта
            if pc + 2 >= len(code):
                raise ValueError("Недостаточно байтов для IN/OUT инструкции")
            port = code[pc + 1]
            reg = code[pc + 2]
            opcode = OpCode(byte0)
            return Instruction(opcode=opcode, operands=[port, reg], mod=0), 3

        # Векторные инструкции (0x58-0x5F)
        if 0x58 <= byte0 <= 0x5F:
            if pc + 1 >= len(code):
                raise ValueError("Недостаточно байтов для векторной инструкции")
            vec_byte = code[pc + 1]
            vd = (vec_byte >> 4) & 0x03
            vs1 = (vec_byte >> 2) & 0x03
            vs2 = (vec_byte >> 0) & 0x03
            opcode = OpCode(byte0)
            return Instruction(opcode=opcode, operands=[vd, vs1, vs2], mod=AddrMode.VEC), 2

        # Стандартные инструкции с MOD битами
        # Первый байт: [OPCODE:6][MOD:2]
        opcode_val = (byte0 >> 2) & 0x3F
        mod = byte0 & 0x03

        try:
            opcode = OpCode(opcode_val)
        except ValueError:
            raise ValueError(f"Неизвестный opcode: {opcode_val} at PC={pc}")

        operands = []
        size = 1  # Минимальный размер - 1 байт

        if mod == AddrMode.REG:
            # Регистр-Регистр: 1 доп байт
            if pc + 1 >= len(code):
                raise ValueError("Недостаточно байтов для REG режима")
            byte1 = code[pc + 1]
            rd = (byte1 >> 4) & 0x03
            rs = (byte1 >> 0) & 0x03
            operands = [rd, rs]
            size = 2

        elif mod == AddrMode.IMM:
            # Регистр-Немедленное: 2 доп байта
            if pc + 2 >= len(code):
                raise ValueError("Недостаточно байтов для IMM режима")
            byte1 = code[pc + 1]
            imm = code[pc + 2]
            rd = (byte1 >> 4) & 0x03
            operands = [rd, imm]
            size = 3

        elif mod == AddrMode.MEM:
            # Регистр-Память: 3 доп байта (адрес 16 бит)
            if pc + 3 >= len(code):
                raise ValueError("Недостаточно байтов для MEM режима")
            import struct

            byte1 = code[pc + 1]
            addr = struct.unpack("<H", code[pc + 2 : pc + 4])[0]
            rd = (byte1 >> 4) & 0x03
            operands = [rd, addr]
            size = 4

        elif mod == AddrMode.DIR:
            # Прямая адресация (JMP, CALL): 2 доп байта (адрес)
            if pc + 2 >= len(code):
                raise ValueError("Недостаточно байтов для DIR режима")
            import struct

            addr = struct.unpack("<H", code[pc + 1 : pc + 3])[0]
            operands = [addr]
            size = 3

        elif mod == AddrMode.VEC:
            # Векторный: 1 доп байт
            if pc + 1 >= len(code):
                raise ValueError("Недостаточно байтов для VEC режима")
            byte1 = code[pc + 1]
            vd = (byte1 >> 4) & 0x03
            vs1 = (byte1 >> 2) & 0x03
            vs2 = (byte1 >> 0) & 0x03
            operands = [vd, vs1, vs2]
            size = 2

        return Instruction(opcode=opcode, operands=operands, mod=mod), size

    def decode_all(self, code: bytes) -> list[tuple[int, Instruction]]:
        """Декодирует всю программу, возвращает список (PC, инструкция)"""
        instructions = []
        pc = 0
        while pc < len(code):
            inst, size = self.decode(code, pc)
            if inst is None:
                break
            instructions.append((pc, inst))
            pc += size
        return instructions
