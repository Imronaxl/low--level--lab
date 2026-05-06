"""
AST (Abstract Syntax Tree) определения для языка alg.
Синтаксис похож на Java/JavaScript/Lua.
"""

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class Num:
    """Числовой литерал."""

    value: int


@dataclass
class StringLit:
    """Строковый литерал (C-string, null-terminated)."""

    value: str


@dataclass
class Ident:
    """Идентификатор (переменная, функция)."""

    name: str


@dataclass
class BinOp:
    """Бинарная операция: +, -, *, /, %, ==, !=, <, >, <=, >=, &&, ||"""

    op: str
    left: "Expr"
    right: "Expr"


@dataclass
class UnaryOp:
    """Унарная операция: -, !"""

    op: str
    operand: "Expr"


@dataclass
class Assign:
    """Присваивание: var = expr"""

    target: Ident
    value: "Expr"


@dataclass
class VarDecl:
    """Объявление переменной: let var = expr или type var [= expr] [size]."""

    name: str
    init: Optional["Expr"] = None
    var_type: str = "int"  # 'int' или 'char'
    size: int | None = None  # размер массива, если объявлен


@dataclass
class IfStmt:
    """Условный оператор: if (cond) { ... } else { ... }"""

    cond: "Expr"
    then_body: list["Stmt"]
    else_body: list["Stmt"] | None = None


@dataclass
class WhileStmt:
    """Цикл while: while (cond) { ... }"""

    cond: "Expr"
    body: list["Stmt"]


@dataclass
class ForStmt:
    """Цикл for: for (let i = 0; i < n; i++) { ... }"""

    init: VarDecl | Assign | None
    cond: "Expr"
    update: Optional["Expr"]
    body: list["Stmt"]


@dataclass
class FuncDef:
    """Определение функции: function name(args) { ... }"""

    name: str
    params: list[str]
    body: list["Stmt"]
    return_expr: Optional["Expr"] = None


@dataclass
class FuncCall:
    """Вызов функции: name(args)"""

    name: str
    args: list["Expr"]


@dataclass
class PrintStmt:
    """Вывод: print(expr)"""

    expr: "Expr"


@dataclass
class ReadStmt:
    """Ввод: read(var)"""

    target: Ident


@dataclass
class ReturnStmt:
    """Возврат из функции: return expr"""

    expr: Optional["Expr"] = None


@dataclass
class BreakStmt:
    """Прерывание цикла: break"""

    pass


@dataclass
class ContinueStmt:
    """Продолжение цикла: continue"""

    pass


@dataclass
class InFuncCall:
    """Вызов функции in(): ввод символа"""

    pass


@dataclass
class OutFuncCall:
    """Вызов функции out(expr): вывод символа"""

    expr: "Expr"


@dataclass
class Block:
    """Блок операторов: { ... }"""

    statements: list["Stmt"]


@dataclass
class Program:
    """Корневой узел программы."""

    declarations: list


# Типы выражений и операторов (объявляем после всех классов)
Expr = Union[Num, StringLit, Ident, BinOp, UnaryOp, FuncCall]
Stmt = Union[
    VarDecl,
    Assign,
    IfStmt,
    WhileStmt,
    ForStmt,
    PrintStmt,
    ReadStmt,
    ReturnStmt,
    BreakStmt,
    ContinueStmt,
    InFuncCall,
    OutFuncCall,
    Block,
]

# Обновляем аннотацию Program после объявления Stmt
Program.__annotations__["declarations"] = list[FuncDef | VarDecl | Stmt]
