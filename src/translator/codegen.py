"""Code Generator: AST -> Machine Code (Binary)

Генерирует бинарный код для CISC процессора.
Формат инструкций:
  MOV  R, #imm  : 0x09, reg<<4, imm_lo, imm_hi           (4 bytes)
  LOAD R, [addr] : 0x82, reg<<4, addr_lo, addr_hi         (4 bytes)
  STORE [addr], R: 0x86, reg<<4, addr_lo, addr_hi         (4 bytes)
  ADD  R, R      : 0x10, (rd<<4)|rs                       (2 bytes)
  SUB  R, R      : 0x14, (rd<<4)|rs                       (2 bytes)
  MUL  R, R      : 0x18, (rd<<4)|rs                       (2 bytes)
  DIV  R, R      : 0x1C, (rd<<4)|rs                       (2 bytes)
  CMP  R, R      : 0x30, (rd<<4)|rs                       (2 bytes)
  JMP  addr      : 0x43, addr_lo, addr_hi                 (3 bytes)
  JZ   addr      : 0x47, addr_lo, addr_hi                 (3 bytes)
  JNZ  addr      : 0x4B, addr_lo, addr_hi                 (3 bytes)
  JL   addr      : 0x4F, addr_lo, addr_hi                 (3 bytes)
  JG   addr      : 0x53, addr_lo, addr_hi                 (3 bytes)
  IN   R, port   : 0x40, reg, port                        (3 bytes)
  OUT  port, R   : 0x41, port, reg                        (3 bytes)
  HALT           : 0x04                                   (1 byte)
"""

from lang.ast import (
    Assign,
    BinOp,
    BreakStmt,
    ContinueStmt,
    Expr,
    ForStmt,
    FuncCall,
    FuncDef,
    Ident,
    IfStmt,
    Num,
    PrintStmt,
    Program,
    ReadStmt,
    ReturnStmt,
    Stmt,
    StringLit,
    UnaryOp,
    VarDecl,
    WhileStmt,
)

# Инструкции
MOV_IMM = 0x09
LOAD_MEM = 0x82
STORE_MEM = 0x86
ADD_REG = 0x10
SUB_REG = 0x14
MUL_REG = 0x18
DIV_REG = 0x1C
CMP_REG = 0x30
JMP = 0x43
JZ = 0x47
JNZ = 0x4B
JL = 0x4F
JG = 0x53
IN_PORT = 0x40
OUT_PORT = 0x41
HALT = 0x04

DATA_BASE = 0x1000
CODE_BASE = 0x0100
PORT_STDIN = 0x01
PORT_STDOUT = 0x02


class CodeGenerator:
    def __init__(self):
        self.code = bytearray()
        self.data = bytearray()
        self.symbols: dict[str, int] = {}
        self.var_types: dict[str, str] = {}
        self.data_offset = 0
        self._break_stack: list[int] = []
        self._break_jmp_offsets: list[list[int]] = []
        self._continue_stack: list[int] = []

    # ── Инструкции ──

    def _emit(self, *args: int):
        self.code.extend(args)

    def _code_addr(self) -> int:
        return CODE_BASE + len(self.code)

    def _data_addr(self, name: str) -> int:
        if name not in self.symbols:
            self.symbols[name] = DATA_BASE + self.data_offset
            self.data_offset += 4
            while len(self.data) < self.data_offset:
                self.data.append(0)
        return self.symbols[name]

    def _mov_imm(self, reg: int, value: int):
        self._emit(MOV_IMM, (reg & 0x0F) << 4, value & 0xFF, (value >> 8) & 0xFF)

    def _load(self, reg: int, addr: int):
        self._emit(LOAD_MEM, (reg & 0x03) << 4, addr & 0xFF, (addr >> 8) & 0xFF)

    def _store(self, addr: int, reg: int):
        self._emit(STORE_MEM, (reg & 0x03) << 4, addr & 0xFF, (addr >> 8) & 0xFF)

    def _add(self, rd: int, rs: int):
        self._emit(ADD_REG, ((rd & 0x03) << 4) | (rs & 0x03))

    def _add_imm(self, rd: int, imm: int):
        self._emit(0x11, (rd & 0x03) << 4, imm & 0xFF, (imm >> 8) & 0xFF)

    def _sub(self, rd: int, rs: int):
        self._emit(SUB_REG, ((rd & 0x03) << 4) | (rs & 0x03))

    def _sub_imm(self, rd: int, imm: int):
        self._emit(0x15, (rd & 0x03) << 4, imm & 0xFF, (imm >> 8) & 0xFF)

    def _mul(self, rd: int, rs: int):
        self._emit(MUL_REG, ((rd & 0x03) << 4) | (rs & 0x03))

    def _div(self, rd: int, rs: int):
        self._emit(DIV_REG, ((rd & 0x03) << 4) | (rs & 0x03))

    def _and(self, rd: int, rs: int):
        self._emit(0x20, ((rd & 0x03) << 4) | (rs & 0x03))

    def _or(self, rd: int, rs: int):
        self._emit(0x24, ((rd & 0x03) << 4) | (rs & 0x03))

    def _cmp(self, r1: int, r2: int):
        self._emit(CMP_REG, ((r1 & 0x03) << 4) | (r2 & 0x03))

    def _jmp(self, addr: int):
        self._emit(JMP, addr & 0xFF, (addr >> 8) & 0xFF)

    def _jz(self, addr: int):
        self._emit(JZ, addr & 0xFF, (addr >> 8) & 0xFF)

    def _jnz(self, addr: int):
        self._emit(JNZ, addr & 0xFF, (addr >> 8) & 0xFF)

    def _jl(self, addr: int):
        self._emit(JL, addr & 0xFF, (addr >> 8) & 0xFF)

    def _jge(self, addr: int):
        self._emit(JG, addr & 0xFF, (addr >> 8) & 0xFF)

    def _jg(self, addr: int):
        self._emit(JG, addr & 0xFF, (addr >> 8) & 0xFF)

    def _out(self, port: int, reg: int):
        self._emit(OUT_PORT, port, reg & 0x07)

    def _inp(self, reg: int, port: int):
        self._emit(IN_PORT, reg & 0x07, port)

    def _halt(self):
        self._emit(HALT)

    def _patch_jmp(self, offset: int, target: int):
        self.code[offset + 1] = target & 0xFF
        self.code[offset + 2] = (target >> 8) & 0xFF

    # ── Генерация выражений ──

    def gen_expr(self, expr: Expr, reg: int = 0) -> int:
        """Генерирует выражение, результат в reg. Возвращает reg."""
        if isinstance(expr, Num):
            self._mov_imm(reg, expr.value)
            return reg

        if isinstance(expr, StringLit):
            self._mov_imm(reg, 0)
            return reg

        if isinstance(expr, Ident):
            if expr.name == "true":
                self._mov_imm(reg, 1)
                return reg
            if expr.name == "false":
                self._mov_imm(reg, 0)
                return reg
            addr = self._data_addr(expr.name)
            self._load(reg, addr)
            return reg

        if isinstance(expr, BinOp):
            if expr.op in ("==", "!=", "<", ">", "<=", ">="):
                left_reg = self.gen_expr(expr.left, reg)
                right_reg = self.gen_expr(expr.right, 1 if reg == 0 else 0)
                self._cmp(left_reg, right_reg)
                result_reg = left_reg
                if expr.op == "<":
                    self._mov_imm(result_reg, 1)
                    done = len(self.code)
                    self._jl(0)
                    self._mov_imm(result_reg, 0)
                    self._patch_jmp(done, self._code_addr())
                elif expr.op == ">":
                    self._mov_imm(result_reg, 0)
                    skip1 = len(self.code)
                    self._jl(0)
                    skip2 = len(self.code)
                    self._jz(0)
                    self._mov_imm(result_reg, 1)
                    self._patch_jmp(skip1, self._code_addr())
                    self._patch_jmp(skip2, self._code_addr())
                elif expr.op == "<=":
                    self._mov_imm(result_reg, 1)
                    skip1 = len(self.code)
                    self._jl(0)
                    skip2 = len(self.code)
                    self._jz(0)
                    self._mov_imm(result_reg, 0)
                    self._patch_jmp(skip1, self._code_addr())
                    self._patch_jmp(skip2, self._code_addr())
                elif expr.op == ">=":
                    self._mov_imm(result_reg, 0)
                    done = len(self.code)
                    self._jl(0)
                    self._mov_imm(result_reg, 1)
                    self._patch_jmp(done, self._code_addr())
                elif expr.op == "==":
                    self._mov_imm(result_reg, 0)
                    done = len(self.code)
                    self._jnz(0)
                    self._mov_imm(result_reg, 1)
                    self._patch_jmp(done, self._code_addr())
                elif expr.op == "!=":
                    self._mov_imm(result_reg, 0)
                    done = len(self.code)
                    self._jz(0)
                    self._mov_imm(result_reg, 1)
                    self._patch_jmp(done, self._code_addr())
                elif expr.op == "!=":
                    self._mov_imm(result_reg, 0)
                    done = len(self.code)
                    self._jz(0)
                    self._mov_imm(result_reg, 1)
                    self._patch_jmp(done, self._code_addr())
                return result_reg
            if expr.op == "||":
                left_reg = self.gen_expr(expr.left, reg)
                skip_jmp = len(self.code)
                self._jmp(0)
                true_jmp = len(self.code)
                self._jnz(0)
                self.gen_expr(expr.right, reg)
                done_jmp = len(self.code)
                self._jmp(0)
                self._patch_jmp(true_jmp, self._code_addr())
                self._mov_imm(reg, 1)
                self._patch_jmp(skip_jmp, self._code_addr())
                self._patch_jmp(done_jmp, self._code_addr())
                return reg
            if expr.op == "&&":
                left_reg = self.gen_expr(expr.left, reg)
                false_jmp = len(self.code)
                self._jz(0)
                self.gen_expr(expr.right, reg)
                done_jmp = len(self.code)
                self._jmp(0)
                self._patch_jmp(false_jmp, self._code_addr())
                self._mov_imm(reg, 0)
                self._patch_jmp(done_jmp, self._code_addr())
                return reg
            left_reg = self.gen_expr(expr.left, reg)
            right_reg = self.gen_expr(expr.right, 1 if reg == 0 else 0)
            op_map = {"+": ADD_REG, "-": SUB_REG, "*": MUL_REG, "/": DIV_REG}
            if expr.op in op_map:
                if expr.op == "+":
                    self._add(left_reg, right_reg)
                elif expr.op == "-":
                    self._sub(left_reg, right_reg)
                elif expr.op == "*":
                    self._mul(left_reg, right_reg)
                elif expr.op == "/":
                    self._div(left_reg, right_reg)
            return left_reg

        if isinstance(expr, UnaryOp):
            operand_reg = self.gen_expr(expr.operand, reg)
            if expr.op == "-":
                self._mov_imm(1, 0)
                self._sub(operand_reg, 1)
            return operand_reg

        if isinstance(expr, FuncCall):
            return self.gen_func_call(expr, reg)

        self._mov_imm(reg, 0)
        return reg

    def gen_func_call(self, expr: FuncCall, reg: int) -> int:
        """Упрощённый вызов встроенных функций."""
        if expr.name == "abs" and len(expr.args) == 1:
            arg_reg = self.gen_expr(expr.args[0], reg)
            self._mov_imm(1, 0)
            self._cmp(arg_reg, 1)
            return arg_reg
        for arg in expr.args:
            self.gen_expr(arg, reg)
        return reg

    # ── Генерация операторов ──

    def gen_stmt(self, stmt: Stmt):
        if isinstance(stmt, VarDecl):
            self._gen_var_decl(stmt)
        elif isinstance(stmt, Assign):
            self._gen_assign(stmt)
        elif isinstance(stmt, PrintStmt):
            self._gen_print(stmt)
        elif isinstance(stmt, ReadStmt):
            self._gen_read(stmt)
        elif isinstance(stmt, IfStmt):
            self._gen_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self._gen_while(stmt)
        elif isinstance(stmt, ForStmt):
            self._gen_for(stmt)
        elif isinstance(stmt, FuncDef):
            self._gen_func_def(stmt)
        elif isinstance(stmt, BreakStmt):
            if self._break_stack:
                jmp_offset = len(self.code)
                self._jmp(0)
                self._break_jmp_offsets[-1].append(jmp_offset)
        elif isinstance(stmt, ContinueStmt):
            if self._continue_stack:
                self._jmp(self._continue_stack[-1])
        elif isinstance(stmt, ReturnStmt):
            pass

    def _gen_var_decl(self, stmt: VarDecl):
        addr = self._data_addr(stmt.name)
        self.var_types[stmt.name] = stmt.var_type
        if stmt.init is not None:
            if isinstance(stmt.init, Num):
                self._mov_imm(0, stmt.init.value)
                self._store(addr, 0)
            elif isinstance(stmt.init, StringLit):
                pass
            else:
                reg = self.gen_expr(stmt.init, 0)
                self._store(addr, reg)

    def _gen_assign(self, stmt: Assign):
        addr = self._data_addr(stmt.target.name)
        reg = self.gen_expr(stmt.value, 0)
        self._store(addr, reg)

    def _gen_print(self, stmt: PrintStmt):
        if isinstance(stmt.expr, StringLit):
            for ch in stmt.expr.value:
                self._mov_imm(0, ord(ch))
                self._out(PORT_STDOUT, 0)
        elif isinstance(stmt.expr, Ident) and self.var_types.get(stmt.expr.name) == "char":
            addr = self._data_addr(stmt.expr.name)
            self._load(0, addr)
            self._out(PORT_STDOUT, 0)
        else:
            reg = self.gen_expr(stmt.expr, 0)
            self._print_int(reg)

    def _print_int(self, reg: int):
        """Генерирует код вывода числа из reg как десятичной строки."""
        r_num = reg
        r_tmp = 1 if reg != 1 else 0
        r_dig = 2 if reg != 2 else (0 if reg != 0 else 1)

        self._mov_imm(r_tmp, 0)
        self._cmp(r_num, r_tmp)
        zero_jz = len(self.code)
        self._jz(0)

        powers = [10000, 1000, 100, 10, 1]
        skip_jumps = []
        next_digit_addrs = []

        for pi, power in enumerate(powers):
            next_digit_addrs.append(self._code_addr())
            self._mov_imm(r_dig, 0)
            self._mov_imm(r_tmp, power)

            loop_start = self._code_addr()
            self._cmp(r_num, r_tmp)
            cmp_jl = len(self.code)
            self._jl(0)
            self._sub(r_num, r_tmp)
            self._add_imm(r_dig, 1)
            self._jmp(loop_start)
            self._patch_jmp(cmp_jl, self._code_addr())

            if pi < len(powers) - 1:
                self._mov_imm(r_tmp, 0)
                self._cmp(r_dig, r_tmp)
                sj = len(self.code)
                self._jz(0)
                skip_jumps.append(sj)

            self._add_imm(r_dig, ord("0"))
            self._out(PORT_STDOUT, r_dig)

        for i, sj in enumerate(skip_jumps):
            target = next_digit_addrs[i + 1] if i + 1 < len(next_digit_addrs) else self._code_addr()
            self._patch_jmp(sj, target)

        self._mov_imm(r_num, ord("\n"))
        self._out(PORT_STDOUT, r_num)
        done_jmp = len(self.code)
        self._jmp(0)

        self._patch_jmp(zero_jz, self._code_addr())
        self._mov_imm(r_num, ord("0"))
        self._out(PORT_STDOUT, r_num)
        self._mov_imm(r_num, ord("\n"))
        self._out(PORT_STDOUT, r_num)

        self._patch_jmp(done_jmp, self._code_addr())

    def _gen_read(self, stmt: ReadStmt):
        addr = self._data_addr(stmt.target.name)
        self._inp(0, PORT_STDIN)
        self._store(addr, 0)

    def _gen_if(self, stmt: IfStmt):
        reg = self.gen_expr(stmt.cond, 0)
        self._mov_imm(1, 0)
        self._cmp(reg, 1)

        if stmt.else_body:
            else_jmp = len(self.code)
            self._jz(0)
            for s in stmt.then_body:
                self.gen_stmt(s)
            end_jmp = len(self.code)
            self._jmp(0)
            self._patch_jmp(else_jmp, self._code_addr())
            for s in stmt.else_body:
                self.gen_stmt(s)
            self._patch_jmp(end_jmp, self._code_addr())
        else:
            end_jmp = len(self.code)
            self._jz(0)
            for s in stmt.then_body:
                self.gen_stmt(s)
            self._patch_jmp(end_jmp, self._code_addr())

    def _gen_while(self, stmt: WhileStmt):
        self._continue_stack.append(self._code_addr())
        loop_start = self._code_addr()
        reg = self.gen_expr(stmt.cond, 0)
        self._mov_imm(1, 0)
        self._cmp(reg, 1)
        end_jmp = len(self.code)
        self._jz(0)
        self._break_stack.append(end_jmp)
        self._break_jmp_offsets.append([])
        for s in stmt.body:
            self.gen_stmt(s)
        self._jmp(loop_start)
        self._patch_jmp(end_jmp, self._code_addr())
        for bo in self._break_jmp_offsets[-1]:
            self._patch_jmp(bo, self._code_addr())
        self._break_jmp_offsets.pop()
        self._break_stack.pop()
        self._continue_stack.pop()

    def _gen_for(self, stmt: ForStmt):
        if stmt.init:
            self.gen_stmt(stmt.init)
        self._continue_stack.append(self._code_addr())
        loop_start = self._code_addr()
        if stmt.cond and not (isinstance(stmt.cond, Num) and stmt.cond.value == 1):
            reg = self.gen_expr(stmt.cond, 0)
            self._mov_imm(1, 0)
            self._cmp(reg, 1)
            end_jmp = len(self.code)
            self._jz(0)
        else:
            end_jmp = None
        self._break_stack.append(end_jmp if end_jmp is not None else len(self.code))
        for s in stmt.body:
            self.gen_stmt(s)
        self._continue_stack.pop()
        if stmt.update:
            self.gen_expr(stmt.update, 0)
        if end_jmp is not None:
            self._jmp(loop_start)
            self._patch_jmp(end_jmp, self._code_addr())
        else:
            self._jmp(loop_start)
        if self._break_stack:
            self._break_stack.pop()

    def _gen_func_def(self, stmt: FuncDef):
        for s in stmt.body:
            self.gen_stmt(s)
        if stmt.return_expr:
            self.gen_expr(stmt.return_expr, 0)

    # ── Главный метод ──

    def generate(self, ast: Program) -> tuple[bytes, bytes]:
        for decl in ast.declarations:
            self.gen_stmt(decl)
        self._halt()

        code_bytes = bytes(self.code)

        while len(self.data) % 4 != 0:
            self.data.append(0)
        data_bytes = bytes(self.data)

        padding_size = DATA_BASE - CODE_BASE - len(code_bytes)
        if padding_size > 0:
            code_bytes += b"\x00" * padding_size

        return code_bytes, data_bytes
