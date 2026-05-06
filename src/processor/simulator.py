"""
Симулятор процессора с точностью до такта (tick-level)
Реализует микропрограммное управление (microcoded)
"""

import sys
from dataclasses import dataclass
from pathlib import Path

# Добавляем src в путь импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from isa.instructions import OpCode
from processor.datapath import DataPath
from processor.microcode import MICROCODE, MicroOp


@dataclass
class LogEntry:
    tick: int
    pc: int
    micro_op: str
    instruction: str
    registers: list[int]
    flags: dict[str, bool]
    output: str


class ControlUnit:
    """Microcoded Control Unit"""

    def __init__(self, datapath: DataPath):
        self.datapath = datapath
        self.current_microcode: list[MicroOp] = []
        self.micro_pc: int = 0
        self.current_inst: str | None = ""
        self.halted: bool = False
        self.initialized: bool = False  # Флаг первой инициализации

    def fetch_decode(self) -> bool:
        """FETCH + DECODE цикл. Возвращает False если HALT или конец памяти"""
        dp = self.datapath
        pc = dp.state.pc

        if pc >= len(dp.memory):
            return False

        # Читаем первый байт инструкции
        byte0 = dp.mem_read(pc)

        # Проверяем специальные opcode (I/O и векторные) - они используют полный байт
        if byte0 >= 0x40 and byte0 <= 0x5F:
            opcode_val = byte0
            mod = 0  # Для специальных инструкций mod не используется
        else:
            # Стандартные инструкции с MOD битами
            opcode_val = (byte0 >> 2) & 0x3F
            mod = byte0 & 0x03

        try:
            opcode = OpCode(opcode_val)
        except ValueError:
            raise RuntimeError(f"Неизвестный opcode {opcode_val} at PC={pc}")

        # Получаем микрокод для этой инструкции
        if opcode_val not in MICROCODE:
            raise RuntimeError(f"Нет микрокода для opcode {opcode_val}")

        self.current_microcode = MICROCODE[opcode_val].copy()
        self.micro_pc = 0
        self.current_inst = f"{opcode.name}"

        # Сохраняем информацию о декодировании в datapath
        dp.state.decoded_imm = 0
        dp.state.decoded_rd = 0
        dp.state.decoded_rs = 0

        # Декодируем операнды в зависимости от типа инструкции
        if byte0 >= 0x40 and byte0 <= 0x5F:
            # Специальные инструкции (IN/OUT, векторные)
            if byte0 == 0x40 or byte0 == 0x41:  # IN/OUT: [opcode][op1][op2]
                if pc + 1 < len(dp.memory):
                    dp.state.decoded_rd = dp.mem_read(pc + 1) & 0x07  # reg или port
                if pc + 2 < len(dp.memory):
                    dp.state.decoded_rs = dp.mem_read(pc + 2) & 0x07  # port или reg
            elif byte0 >= 0x50:  # Векторные: [opcode][vec_byte]
                if pc + 1 < len(dp.memory):
                    vec_byte = dp.mem_read(pc + 1)
                    dp.state.decoded_rd = (vec_byte >> 5) & 0x07  # vd
                    dp.state.decoded_rs = (vec_byte >> 2) & 0x07  # vs1
        else:
            # Стандартные инструкции
            dp.state.decoded_rd = (
                (dp.mem_read(pc + 1) >> 4) & 0x0F if pc + 1 < len(dp.memory) else 0
            )
            dp.state.decoded_rs = dp.mem_read(pc + 1) & 0x0F if pc + 1 < len(dp.memory) else 0

            # Для immediate режима читаем значение
            if mod == 1:  # IMM режим
                if pc + 2 < len(dp.memory):
                    dp.state.decoded_imm = dp.mem_read(pc + 2) & 0xFF
                if pc + 3 < len(dp.memory):
                    dp.state.decoded_imm |= (dp.mem_read(pc + 3) << 8) & 0xFFFF

        return True

    def execute_micro_step(self) -> bool:
        """Выполняет один микрошаг (один такт). Возвращает False если завершено"""
        if self.halted:
            return False

        if self.micro_pc >= len(self.current_microcode):
            # Микропрограмма завершена, переходим к следующей инструкции
            return True

        micro_op = self.current_microcode[self.micro_pc]
        self._execute_micro_op(micro_op)
        self.micro_pc += 1

        return self.micro_pc < len(self.current_microcode)

    def _execute_micro_op(self, micro_op: MicroOp):
        """Выполнение конкретной микрооперации"""
        dp = self.datapath

        if micro_op == MicroOp.FETCH_ADDR:
            dp.state.mar = dp.state.pc

        elif micro_op == MicroOp.FETCH_MEM:
            # Читаем байт из памяти по адресу MAR
            dp.state.mdr = dp.mem_read(dp.state.mar)
            dp.state.pc += 1

        elif micro_op == MicroOp.DECODE:
            # Декодирование уже произошло при загрузке микрокода
            # Здесь читаем дополнительные байты операндов для специальных инструкций

            byte0 = dp.mem_read(dp.state.mar)

            # Проверяем специальные opcode (I/O и векторные)
            if byte0 >= 0x40 and byte0 <= 0x5F:
                if byte0 == 0x40 or byte0 == 0x41:  # IN/OUT: [opcode][op1][op2] - 3 байта
                    op1 = dp.mem_read(dp.state.mar + 1)
                    op2 = dp.mem_read(dp.state.mar + 2)
                    dp.state.decoded_rd = op1 & 0x07
                    dp.state.decoded_rs = op2 & 0x07
                    dp.state.pc = dp.state.mar + 3
                elif byte0 >= 0x50:  # Векторные: [opcode][vec_byte] - 2 байта
                    vec_byte = dp.mem_read(dp.state.mar + 1)
                    dp.state.decoded_rd = (vec_byte >> 5) & 0x07
                    dp.state.decoded_rs = (vec_byte >> 2) & 0x07
                    dp.state.pc = dp.state.mar + 2
            else:
                # Стандартные инструкции с MOD битами
                mod = byte0 & 0x03

                # Сохраняем номер регистра из byte1 (который находится по адресу mar+1)
                if mod == 1:  # IMM режим - читаем immediate (16 бит)
                    # byte1 находится по адресу mar+1, содержит [Rd:4][RFU:4]
                    byte1 = dp.mem_read(dp.state.mar + 1)
                    rd = (byte1 >> 4) & 0x0F
                    dp.state.decoded_rd = rd
                    # immediate - 16 бит, little-endian: byte2 (low) + byte3 (high)
                    imm_low = dp.mem_read(dp.state.mar + 2)
                    imm_high = dp.mem_read(dp.state.mar + 3)
                    dp.state.decoded_imm = imm_low | (imm_high << 8)
                    # Обновляем PC на адрес следующей инструкции (4 байта всего)
                    dp.state.pc = dp.state.mar + 4
                elif mod == 2:  # MEM режим - читаем адрес (16 бит)
                    byte1 = dp.mem_read(dp.state.mar + 1)
                    rd = (byte1 >> 4) & 0x03
                    dp.state.decoded_rd = rd
                    addr_low = dp.mem_read(dp.state.mar + 2)
                    addr_high = dp.mem_read(dp.state.mar + 3)
                    dp.state.decoded_imm = addr_low | (addr_high << 8)
                    dp.state.pc = dp.state.mar + 4
                elif mod == 0:  # REG-REG режим
                    byte1 = dp.mem_read(dp.state.mar + 1)
                    rd = (byte1 >> 4) & 0x03
                    rs = byte1 & 0x03
                    dp.state.decoded_rd = rd
                    dp.state.decoded_rs = rs
                    dp.state.pc = dp.state.mar + 2
                elif mod == 3:  # DIR режим (прямая адресация для JMP)
                    addr_low = dp.mem_read(dp.state.mar + 1)
                    addr_high = dp.mem_read(dp.state.mar + 2)
                    dp.state.decoded_imm = addr_low | (addr_high << 8)
                    dp.state.pc = dp.state.mar + 3

        elif micro_op == MicroOp.REG_WRITE_IMM:
            # Запись immediate значения в регистр (номер регистра уже декодирован)
            dp.reg_write(dp.state.decoded_rd, dp.state.decoded_imm)

        elif micro_op == MicroOp.REG_READ_A:
            pass  # Подготовка к чтению первого операнда

        elif micro_op == MicroOp.REG_READ_B:
            pass  # Подготовка к чтению второго операнда

        elif micro_op == MicroOp.ALU_SET_A:
            pass  # Установка входа A

        elif micro_op == MicroOp.ALU_SET_B:
            pass  # Установка входа B

        elif micro_op == MicroOp.ALU_ADD:
            mod = dp.mem_read(dp.state.mar) & 0x03
            rd = dp.state.decoded_rd

            if mod == 0:  # REG-REG
                rs = dp.state.decoded_rs
                a = dp.reg_read(rd)
                b = dp.reg_read(rs)
            else:  # IMM
                a = dp.reg_read(rd)
                b = dp.state.decoded_imm

            result = dp.alu_add(a, b)
            dp.reg_write(rd, result)

        elif micro_op == MicroOp.REG_READ_A:
            # Чтение регистра для OUT инструкции
            pass

        elif micro_op == MicroOp.IO_WRITE:
            # Вывод значения из регистра в порт
            # Формат OUT инструкции: [OPCODE=0x41] [PORT] [REG]
            # MAR указывает на первый байт (opcode), поэтому порт и регистр по смещениям +1 и +2
            port_addr = dp.mem_read(dp.state.mar + 1)
            reg_idx = dp.mem_read(dp.state.mar + 2) & 0x07
            value = dp.reg_read(reg_idx)
            dp.port_write(port_addr, value)

        elif micro_op == MicroOp.HALT_OP:
            self.halted = True

        elif micro_op == MicroOp.NOP:
            pass

        # Остальные микрооперации будут добавлены по мере необходимости


class Simulator:
    """Tick-level симулятор процессора"""

    def __init__(self):
        self.datapath = DataPath()
        self.control_unit = ControlUnit(self.datapath)
        self.tick_count: int = 0
        self.log: list[LogEntry] = []
        self.running: bool = False

    @property
    def halted(self) -> bool:
        """Свойство для проверки остановки процессора"""
        return self.control_unit.halted

    def load_program(self, code: bytes, start_addr: int = 0x0100):
        """Загрузка программы в память"""
        self.datapath.load_program(code, start_addr)

    def set_input(self, data: str):
        """Установка входных данных"""
        self.datapath.set_input(data)

    def reset(self):
        """Сброс процессора"""
        self.datapath.reset()
        self.control_unit = ControlUnit(self.datapath)
        self.tick_count = 0
        self.log = []
        self.running = False

    def tick(self) -> bool:
        """
        Выполняет один такт процессора.
        Возвращает True если процессор ещё работает, False если остановлен (HALT).
        """
        if self.control_unit.halted:
            return False

        cu = self.control_unit
        dp = self.datapath

        # Если это первый такт или микропрограмма завершена, загружаем следующую инструкцию
        if len(cu.current_microcode) == 0 or cu.micro_pc >= len(cu.current_microcode):
            if not cu.fetch_decode():
                cu.halted = True
                return False

        # Выполняем один микрошаг
        cu.execute_micro_step()

        self.tick_count += 1

        # Логирование
        self._log_tick()

        # Возвращаем True если процессор ещё работает
        return not cu.halted

    def run(self, max_ticks: int = 10000) -> bool:
        """Запуск процессора до HALT или max_ticks"""
        self.running = True
        for _ in range(max_ticks):
            if not self.tick():
                self.running = False
                return self.control_unit.halted
        return False  # Превышено max_ticks

    def _log_tick(self):
        """Добавление записи в журнал"""
        entry = LogEntry(
            tick=self.tick_count,
            pc=self.datapath.state.pc,
            micro_op=self.control_unit.current_microcode[self.control_unit.micro_pc - 1].name
            if self.control_unit.micro_pc > 0
            else "INIT",
            instruction=self.control_unit.current_inst,
            registers=self.datapath.state.registers.copy(),
            flags=self.datapath.state.flags.copy(),
            output=self.datapath.get_output()[-50:] if self.datapath.get_output() else "",
        )
        self.log.append(entry)

    def get_output(self) -> str:
        """Получение выходных данных"""
        return self.datapath.get_output()

    def get_state(self) -> dict:
        """Получение текущего состояния"""
        return self.datapath.get_state_dict()
