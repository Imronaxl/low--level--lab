"""Code Generator: AST -> Machine Code (Binary)"""

from isa.encoding import Operand, OperandType, encode_instruction
from isa.instructions import Instruction, OpCode
from lang.ast import Assign, BinOp, Expr, Num, PrintStmt, Program, Stmt, StringLit


class CodeGenerator:
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.data: list[int] = []
        self.symbols: dict[str, int] = {}

    def emit(self, instr: Instruction):
        self.instructions.append(instr)

    def generate(self, ast: Program) -> tuple[bytes, bytes]:
        # Program имеет поле 'declarations', а не 'statements'
        for decl in ast.declarations:
            self.gen_stmt(decl)
        self.emit(Instruction(OpCode.HALT, []))

        code_bytes = b"".join(encode_instruction(instr) for instr in self.instructions)
        data_bytes = b"".join(d.to_bytes(4, "little") for d in self.data)
        return code_bytes, data_bytes

    def gen_stmt(self, stmt: Stmt):
        if isinstance(stmt, PrintStmt):
            # Для строковых литералов - вывод по символам
            if isinstance(stmt.expr, StringLit):
                s = stmt.expr.value
                for char in s:
                    # Загружаем ASCII код символа в R0
                    self.emit(
                        Instruction(
                            OpCode.MOV,
                            [
                                Operand(OperandType.REGISTER, 0),
                                Operand(OperandType.IMMEDIATE, ord(char)),
                            ],
                        )
                    )
                    # Выводим R0 в порт 2 (stdout)
                    self.emit(
                        Instruction(
                            OpCode.OUT,
                            [Operand(OperandType.PORT, 2), Operand(OperandType.REGISTER, 0)],
                        )
                    )
                # Выводим newline
                self.emit(
                    Instruction(
                        OpCode.MOV,
                        [
                            Operand(OperandType.REGISTER, 0),
                            Operand(OperandType.IMMEDIATE, ord("\n")),
                        ],
                    )
                )
                self.emit(
                    Instruction(
                        OpCode.OUT, [Operand(OperandType.PORT, 2), Operand(OperandType.REGISTER, 0)]
                    )
                )
            else:
                val_reg = self.gen_expr(stmt.expr)
                self.emit(
                    Instruction(
                        OpCode.OUT,
                        [Operand(OperandType.PORT, 2), Operand(OperandType.REGISTER, val_reg)],
                    )
                )
        elif isinstance(stmt, Assign):
            val_reg = self.gen_expr(stmt.value)
            if stmt.target.name not in self.symbols:
                self.symbols[stmt.target.name] = len(self.data) * 4 + 0x1000
                self.data.append(0)
            addr = self.symbols[stmt.target.name]
            self.emit(
                Instruction(
                    OpCode.STORE,
                    [Operand(OperandType.MEMORY, addr), Operand(OperandType.REGISTER, val_reg)],
                )
            )

    def gen_expr(self, expr: Expr) -> int:
        if isinstance(expr, Num):
            reg = 0
            self.emit(
                Instruction(
                    OpCode.MOV,
                    [
                        Operand(OperandType.REGISTER, reg),
                        Operand(OperandType.IMMEDIATE, expr.value),
                    ],
                )
            )
            return reg
        elif isinstance(expr, BinOp):
            l = self.gen_expr(expr.left)
            r = self.gen_expr(expr.right)
            op_map = {"+": OpCode.ADD, "-": OpCode.SUB, "*": OpCode.MUL, "/": OpCode.DIV}
            if expr.op in op_map:
                self.emit(
                    Instruction(
                        op_map[expr.op],
                        [
                            Operand(OperandType.REGISTER, l),
                            Operand(OperandType.REGISTER, l),
                            Operand(OperandType.REGISTER, r),
                        ],
                    )
                )
            return l
        return 0
