"""
Тесты для ISA (кодирование/декодирование) и симулятора
"""

import pytest

from src.isa import AddrMode, Decoder, Encoder, Instruction, OpCode
from src.processor import Simulator


class TestEncoderDecoder:
    def test_encode_mov_imm(self):
        """MOV R0, 42 (MOD=01, immediate)"""
        inst = Instruction(OpCode.MOV, [0, 42], mod=AddrMode.IMM)
        encoded = Encoder.encode(inst)
        # Ожидаем: byte0=[OPCODE:6][MOD:2], byte1=[Rd:4][RFU:4], byte2=imm
        assert len(encoded) == 3
        assert encoded[0] == ((0x02 << 2) | 0x01)  # opcode=2, mod=1
        assert encoded[1] == (0 << 4)  # Rd=0
        assert encoded[2] == 42

    def test_encode_add_reg(self):
        """ADD R0, R1 (MOD=00, reg-reg)"""
        inst = Instruction(OpCode.ADD, [0, 1], mod=AddrMode.REG)
        encoded = Encoder.encode(inst)
        assert len(encoded) == 2
        # OpCode.ADD = 0x04
        assert encoded[0] == ((0x04 << 2) | 0x00)  # opcode=4, mod=0
        assert encoded[1] == (0 << 4) | 1  # Rd=0, Rs=1

    def test_decode_mov_imm(self):
        """Декодирование MOV R0, 42"""
        code = bytes([((0x02 << 2) | 0x01), (0 << 4), 42])
        decoder = Decoder()
        inst, size = decoder.decode(code, 0)
        assert inst is not None
        assert inst.opcode == OpCode.MOV
        assert inst.mod == AddrMode.IMM
        assert inst.operands == [0, 42]
        assert size == 3

    def test_decode_add_reg(self):
        """Декодирование ADD R0, R1"""
        # OpCode.ADD = 0x04
        code = bytes([((0x04 << 2) | 0x00), (0 << 4) | 1])
        decoder = Decoder()
        inst, size = decoder.decode(code, 0)
        assert inst is not None
        assert inst.opcode == OpCode.ADD
        assert inst.mod == AddrMode.REG
        assert inst.operands == [0, 1]
        assert size == 2


class TestSimulatorBasic:
    def test_mov_imm(self):
        """MOV R0, 42; HALT"""
        code = bytearray()
        # MOV R0, 42 (16-bit immediate little-endian)
        code.append((0x02 << 2) | 0x01)  # opcode=MOV, mod=IMM
        code.append(0 << 4)  # Rd=0
        code.append(42)  # imm low
        code.append(0)  # imm high
        # HALT
        code.append((0x01 << 2) | 0x00)  # opcode=HALT, mod=REG

        sim = Simulator()
        sim.load_program(bytes(code))
        result = sim.run(max_ticks=100)

        assert result == True  # Завершился HALT
        assert sim.datapath.reg_read(0) == 42

    def test_add_reg(self):
        """MOV R0,10; MOV R1,20; ADD R0,R1; HALT"""
        code = bytearray()
        # MOV R0, 10 (16-bit immediate)
        code.extend([(0x02 << 2) | 0x01, 0 << 4, 10, 0])
        # MOV R1, 20 (16-bit immediate)
        code.extend([(0x02 << 2) | 0x01, 1 << 4, 20, 0])
        # ADD R0, R1 (OpCode.ADD = 0x04)
        code.extend([(0x04 << 2) | 0x00, (0 << 4) | 1])
        # HALT
        code.extend([(0x01 << 2) | 0x00])

        sim = Simulator()
        sim.load_program(bytes(code))
        result = sim.run(max_ticks=100)

        assert result == True
        assert sim.datapath.reg_read(0) == 30
        assert sim.datapath.reg_read(1) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
