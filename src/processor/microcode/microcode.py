"""Микрокод для CISC процессора с векторными расширениями."""

from enum import IntEnum, auto


class MicroOp(IntEnum):
    """Микрооперации для управления DataPath."""

    NOP = 0
    # Выборка инструкции
    FETCH_ADDR = auto()  # MAR <- PC
    FETCH_MEM = auto()  # MDR <- MEM[MAR], PC <- PC + 1
    DECODE = auto()  # Декодирование IR в управляющие сигналы

    # Работа с регистрами общего назначения
    REG_READ_A = auto()  # A <- R[rs]
    REG_READ_B = auto()  # B <- R[rt]
    REG_WRITE_IMM = auto()  # R[rd] <- immediate (из декодера)
    REG_WRITE_ALU = auto()  # R[rd] <- ALU_result
    REG_WRITE_MEM = auto()  # R[rd] <- MDR

    # Запись в память
    MEM_WRITE = auto()  # MEM[MAR] <- MDR

    # ALU операции
    ALU_SET_A = auto()  # ALU.A <- A
    ALU_SET_B = auto()  # ALU.B <- B (или immediate)
    ALU_ADD = auto()  # ALU.result <- A + B
    ALU_SUB = auto()  # ALU.result <- A - B
    ALU_MUL = auto()  # ALU.result <- A * B
    ALU_DIV = auto()  # ALU.result <- A / B
    ALU_AND = auto()  # ALU.result <- A & B
    ALU_OR = auto()  # ALU.result <- A | B
    ALU_XOR = auto()  # ALU.result <- A ^ B
    ALU_CMP = auto()  # Установка флагов по сравнению A и B
    ALU_UPDATE_FLAGS = auto()  # Обновление флагов из ALU

    # Векторные операции
    VREG_READ_A = auto()  # VA <- VR[vs]
    VREG_READ_B = auto()  # VB <- VR[vt]
    VREG_WRITE = auto()  # VR[vd] <- VResult
    VALU_ADD = auto()  # Векторное сложение
    VALU_SUB = auto()  # Векторное вычитание
    VALU_MUL = auto()  # Векторное умножение

    # Ввод-вывод
    IO_READ = auto()  # MDR <- PORT[port_addr]
    IO_WRITE = auto()  # PORT[port_addr] <- MDR

    # Управление потоком
    JMP = auto()  # PC <- target
    JZ = auto()  # Если ZF=1, PC <- target
    JNZ = auto()  # Если ZF=0, PC <- target
    JL = auto()  # Если SF=1, PC <- target
    JGE = auto()  # Если SF=0, PC <- target

    # Память (данные)
    MEM_LOAD = auto()  # MDR <- MEM[decoded_imm]
    MEM_STORE = auto()  # MEM[decoded_imm] <- R[rd]

    # Специальные
    HALT_OP = auto()  # Остановка процессора


# Микропрограммы для каждой инструкции
# Формат: opcode -> список микроопераций
MICROCODE = {
    # === Базовые инструкции ===
    # NOP (0x00) - нет операции
    0x00: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.NOP,
    ],
    # HALT (0x01)
    0x01: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.HALT_OP,
    ],
    # MOV rd, imm (0x02) - пересылка непосредственного значения
    0x02: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,  # Чтение первого байта (рег/режим)
        MicroOp.DECODE,  # Декодирование rd, режима, чтение imm если есть
        MicroOp.REG_WRITE_IMM,  # Запись immediate в регистр
    ],
    # ADD rd, rs, rt (0x04) - сложение регистров
    0x04: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,  # A <- R[rs]
        MicroOp.REG_READ_B,  # B <- R[rt]
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_ADD,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # SUB rd, rs, rt (0x05) - вычитание
    0x05: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_SUB,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # MUL rd, rs, rt (0x06) - умножение
    0x06: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_MUL,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # DIV rd, rs, rt (0x07) - деление
    0x07: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_DIV,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # AND rd, rs, rt (0x08) - логическое И
    0x08: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_AND,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # OR rd, rs, rt (0x09) - логическое ИЛИ
    0x09: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_OR,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # XOR rd, rs, rt (0x0A) - исключающее ИЛИ
    0x0A: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_XOR,
        MicroOp.ALU_UPDATE_FLAGS,
        MicroOp.REG_WRITE_ALU,
    ],
    # CMP rs, rt (0x0C) - сравнение
    0x0C: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.REG_READ_B,
        MicroOp.ALU_SET_A,
        MicroOp.ALU_SET_B,
        MicroOp.ALU_CMP,
        MicroOp.ALU_UPDATE_FLAGS,
    ],
    # === Инструкции перехода ===
    # JMP target (0x10) - безусловный переход
    0x10: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,  # Извлекает target адрес
        MicroOp.JMP,
    ],
    # JZ target (0x11) - переход если zero flag
    0x11: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.JZ,
    ],
    # JNZ target (0x12) - переход если не zero
    0x12: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.JNZ,
    ],
    # JL target (0x13) - переход если меньше
    0x13: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.JL,
    ],
    # JG target (0x14) - переход если больше
    0x14: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.JGE,
    ],
    # CALL target (0x15) - вызов подпрограммы
    0x15: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.JMP,  # Упрощенно как JMP
    ],
    # RET (0x16) - возврат из подпрограммы
    0x16: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.JMP,  # Упрощенно
    ],
    # === Инструкции памяти ===
    # LOAD rd, [addr] (0x20) - загрузка из памяти
    0x20: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.MEM_LOAD,  # MDR <- MEM[decoded_imm]
        MicroOp.REG_WRITE_MEM,  # R[rd] <- MDR
    ],
    # STORE [addr], rs (0x21) - запись в память
    0x21: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.MEM_STORE,  # MEM[decoded_imm] <- R[rd]
    ],
    # === Ввод-вывод ===
    # OUT port, rs (0x41) - вывод в порт
    0x41: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.REG_READ_A,
        MicroOp.IO_WRITE,
    ],
    # IN rd, port (0x40) - ввод из порта
    0x40: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.IO_READ,
        MicroOp.REG_WRITE_MEM,
    ],
    # === Векторные инструкции ===
    # VLOAD vd, [addr] (0x58) - векторная загрузка
    0x58: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.VREG_WRITE,
    ],
    # VSTORE [addr], vs (0x59) - векторная запись
    0x59: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ_A,
        MicroOp.MEM_WRITE,
    ],
    # VADD vd, vs, vt (0x5A) - векторное сложение
    0x5A: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ_A,
        MicroOp.VREG_READ_B,
        MicroOp.VALU_ADD,
        MicroOp.VREG_WRITE,
    ],
    # VSUB vd, vs, vt (0x5B) - векторное вычитание
    0x5B: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ_A,
        MicroOp.VREG_READ_B,
        MicroOp.VALU_SUB,
        MicroOp.VREG_WRITE,
    ],
    # VMUL vd, vs, vt (0x5C) - векторное умножение
    0x5C: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ_A,
        MicroOp.VREG_READ_B,
        MicroOp.VALU_MUL,
        MicroOp.VREG_WRITE,
    ],
    # VDIV vd, vs, vt (0x5D) - векторное деление
    0x5D: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ_A,
        MicroOp.VREG_READ_B,
        MicroOp.VALU_ADD,
        MicroOp.VREG_WRITE,
    ],
    # VCMP vd, vs, vt (0x5E) - векторное сравнение
    0x5E: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_READ_A,
        MicroOp.VREG_READ_B,
        MicroOp.ALU_CMP,
        MicroOp.ALU_UPDATE_FLAGS,
    ],
    # VSET vd, imm (0x5F) - установка вектора
    0x5F: [
        MicroOp.FETCH_ADDR,
        MicroOp.FETCH_MEM,
        MicroOp.DECODE,
        MicroOp.VREG_WRITE,
    ],
}


def get_microcode(opcode: int) -> list[MicroOp]:
    """Получить микропрограмму для данного opcode."""
    return MICROCODE.get(opcode, [MicroOp.HALT_OP])
