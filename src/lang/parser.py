"""
Парсер для языка alg.
Преобразует токены в AST.
"""

from .ast import (
    Assign,
    BinOp,
    Block,
    BreakStmt,
    ContinueStmt,
    Expr,
    ForStmt,
    FuncCall,
    FuncDef,
    Ident,
    IfStmt,
    InFuncCall,
    Num,
    OutFuncCall,
    PrintStmt,
    Program,
    ReadStmt,
    ReturnStmt,
    StringLit,
    UnaryOp,
    VarDecl,
    WhileStmt,
)
from .lexer import Token, TokenType


class ParseError(Exception):
    """Ошибка парсера."""

    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def error(self, message: str):
        token = self.current()
        raise ParseError(f"Parse error at line {token.line}, column {token.column}: {message}")

    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        token = self.current()
        self.pos += 1
        return token

    def match(self, *types: str) -> bool:
        return self.current().type in types

    def expect(self, token_type: str, message: str = None) -> Token:
        if self.current().type != token_type:
            msg = message or f"Expected {token_type}, got {self.current().type}"
            self.error(msg)
        return self.advance()

    def parse(self) -> Program:
        declarations = []
        while not self.match(TokenType.EOF):
            decl = self.parse_declaration()
            if decl:
                declarations.append(decl)
        return Program(declarations)

    def parse_declaration(self):
        """Разбирает объявление функции, переменной (let или тип имя), или оператор."""
        if self.match(TokenType.FUNCTION):
            return self.parse_func_def()
        elif self.match(TokenType.LET):
            return self.parse_var_decl()
        elif self.match(TokenType.INT) or self.match(TokenType.CHAR):
            # Объявление типа: int x; char c[10];
            return self.parse_typed_var_decl()
        else:
            return self.parse_stmt()

    def parse_typed_var_decl(self) -> VarDecl:
        """Парсит объявление переменной с явным типом: type name [= expr] [size];"""
        type_token = self.current()
        var_type = "int" if type_token.type == TokenType.INT else "char"
        self.advance()

        name_token = self.expect(TokenType.IDENT, f"Ожидается имя переменной после типа {var_type}")
        name = name_token.value

        size = None
        # Проверка на массив: [ размер ] - только если нет инициализации
        if self.match(TokenType.LBRACKET):
            self.advance()  # пропускаем [
            size_token = self.expect(TokenType.NUMBER, "Ожидается размер массива в скобках")
            size = int(size_token.value)
            self.expect(TokenType.RBRACKET, "Ожидается закрывающая скобка ]")

        init = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            init = self.parse_expr()

        self.expect(TokenType.SEMICOLON, "Ожидается ';' в конце объявления переменной")

        return VarDecl(name=name, var_type=var_type, size=size, init=init)

    def parse_func_def(self) -> FuncDef:
        self.expect(TokenType.FUNCTION)
        name_token = self.expect(TokenType.IDENT, "Expected function name")
        name = name_token.value

        self.expect(TokenType.LPAREN)
        params = []
        if not self.match(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                self.advance()
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)

        self.expect(TokenType.LBRACE)
        body = []
        return_expr = None

        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            if self.match(TokenType.RETURN):
                return_expr = self.parse_return_stmt().expr
                break
            stmt = self.parse_stmt()
            if stmt:
                body.append(stmt)

        self.expect(TokenType.RBRACE)

        return FuncDef(name=name, params=params, body=body, return_expr=return_expr)

    def parse_var_decl(self) -> VarDecl:
        self.expect(TokenType.LET)
        name_token = self.expect(TokenType.IDENT, "Expected variable name")
        name = name_token.value

        init = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            init = self.parse_expr()

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return VarDecl(name=name, init=init)

    def parse_stmt(self):
        """Разбирает оператор."""
        if self.match(TokenType.IF):
            return self.parse_if_stmt()
        elif self.match(TokenType.WHILE):
            return self.parse_while_stmt()
        elif self.match(TokenType.FOR):
            return self.parse_for_stmt()
        elif self.match(TokenType.PRINT):
            return self.parse_print_stmt()
        elif self.match(TokenType.READ):
            return self.parse_read_stmt()
        elif self.match(TokenType.RETURN):
            return self.parse_return_stmt()
        elif self.match(TokenType.BREAK):
            return self.parse_break_stmt()
        elif self.match(TokenType.CONTINUE):
            return self.parse_continue_stmt()
        elif self.match(TokenType.LBRACE):
            return self.parse_block()
        elif self.match(TokenType.IDENT):
            # Присваивание или выражение-оператор
            return self.parse_assign_or_expr_stmt()
        else:
            self.error(f"Unexpected token: {self.current().type}")

    def parse_if_stmt(self) -> IfStmt:
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)
        cond = self.parse_expr()
        self.expect(TokenType.RPAREN)

        self.expect(TokenType.LBRACE)
        then_body = []
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            stmt = self.parse_stmt()
            if stmt:
                then_body.append(stmt)
        self.expect(TokenType.RBRACE)

        else_body = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.LBRACE)
            else_body = []
            while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
                stmt = self.parse_stmt()
                if stmt:
                    else_body.append(stmt)
            self.expect(TokenType.RBRACE)

        return IfStmt(cond=cond, then_body=then_body, else_body=else_body)

    def parse_while_stmt(self) -> WhileStmt:
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        cond = self.parse_expr()
        self.expect(TokenType.RPAREN)

        self.expect(TokenType.LBRACE)
        body = []
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            stmt = self.parse_stmt()
            if stmt:
                body.append(stmt)
        self.expect(TokenType.RBRACE)

        return WhileStmt(cond=cond, body=body)

    def parse_for_stmt(self) -> ForStmt:
        self.expect(TokenType.FOR)
        self.expect(TokenType.LPAREN)

        init = None
        if self.match(TokenType.LET):
            init = self.parse_var_decl()
        elif self.match(TokenType.IDENT):
            # Присваивание в init
            name_token = self.expect(TokenType.IDENT)
            if self.match(TokenType.ASSIGN):
                self.advance()
                value = self.parse_expr()
                init = Assign(target=Ident(name_token.value), value=value)
            else:
                self.error("Expected '=' in for loop init")

        # condition
        cond = Num(1)  # default true
        if not self.match(TokenType.SEMICOLON):
            cond = self.parse_expr()

        if self.match(TokenType.SEMICOLON):
            self.advance()

        # update
        update = None
        if not self.match(TokenType.RPAREN):
            # Разбираем выражение update (может быть i++, i+=1, и т.д.)
            if self.match(TokenType.IDENT):
                name_token = self.advance()
                if self.match(TokenType.INC):
                    # i++
                    self.advance()
                    update = BinOp(op="+", left=Ident(name_token.value), right=Num(1))
                elif self.match(TokenType.DEC):
                    # i--
                    self.advance()
                    update = BinOp(op="-", left=Ident(name_token.value), right=Num(1))
                elif self.match(TokenType.PLUS_EQ):
                    # i += expr
                    self.advance()
                    expr_val = self.parse_expr()
                    update = BinOp(op="+", left=Ident(name_token.value), right=expr_val)
                elif self.match(TokenType.MINUS_EQ):
                    # i -= expr
                    self.advance()
                    expr_val = self.parse_expr()
                    update = BinOp(op="-", left=Ident(name_token.value), right=expr_val)
                else:
                    # Просто выражение
                    update = self.parse_expr_rest(Ident(name_token.value))
            else:
                update = self.parse_expr()

        self.expect(TokenType.RPAREN)

        self.expect(TokenType.LBRACE)
        body = []
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            stmt = self.parse_stmt()
            if stmt:
                body.append(stmt)
        self.expect(TokenType.RBRACE)

        return ForStmt(init=init, cond=cond, update=update, body=body)

    def parse_print_stmt(self) -> PrintStmt:
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN)
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return PrintStmt(expr=expr)

    def parse_read_stmt(self) -> ReadStmt:
        self.expect(TokenType.READ)
        self.expect(TokenType.LPAREN)
        target = Ident(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return ReadStmt(target=target)

    def parse_return_stmt(self) -> ReturnStmt:
        self.expect(TokenType.RETURN)
        expr = None
        if not self.match(TokenType.SEMICOLON) and not self.match(TokenType.RBRACE):
            expr = self.parse_expr()
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return ReturnStmt(expr=expr)

    def parse_break_stmt(self) -> BreakStmt:
        self.expect(TokenType.BREAK)
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return BreakStmt()

    def parse_continue_stmt(self) -> ContinueStmt:
        self.expect(TokenType.CONTINUE)
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return ContinueStmt()

    def parse_in_call_stmt(self) -> InFuncCall:
        """Парсит вызов in(): ввод символа"""
        self.expect(TokenType.IN_FUNC)
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.RPAREN)
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return InFuncCall()

    def parse_out_call_stmt(self) -> OutFuncCall:
        """Парсит вызов out(expr): вывод символа"""
        self.expect(TokenType.OUT_FUNC)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN)
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return OutFuncCall(expr=expr)

    def parse_block(self) -> Block:
        self.expect(TokenType.LBRACE)
        statements = []
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            stmt = self.parse_stmt()
            if stmt:
                statements.append(stmt)
        self.expect(TokenType.RBRACE)
        return Block(statements=statements)

    def parse_assign_or_expr_stmt(self):
        """Присваивание или выражение как оператор."""
        name_token = self.expect(TokenType.IDENT)

        if self.match(TokenType.ASSIGN):
            self.advance()
            value = self.parse_expr()
            if self.match(TokenType.SEMICOLON):
                self.advance()
            return Assign(target=Ident(name_token.value), value=value)
        else:
            # Выражение как оператор (например, вызов функции)
            expr = self.parse_expr_rest(Ident(name_token.value))
            if self.match(TokenType.SEMICOLON):
                self.advance()
            return expr  # Возвращаем как выражение (для print и т.д.)

    def parse_expr(self) -> Expr:
        """Разбирает выражение с учетом приоритета операций."""
        return self.parse_or_expr()

    def parse_or_expr(self) -> Expr:
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            op = self.advance().value
            right = self.parse_and_expr()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_and_expr(self) -> Expr:
        left = self.parse_equality()
        while self.match(TokenType.AND):
            op = self.advance().value
            right = self.parse_equality()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_equality(self) -> Expr:
        left = self.parse_comparison()
        while self.match(TokenType.EQ, TokenType.NE):
            op = self.advance().value
            right = self.parse_comparison()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_comparison(self) -> Expr:
        left = self.parse_additive()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op = self.advance().value
            right = self.parse_additive()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_additive(self) -> Expr:
        left = self.parse_multiplicative()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_multiplicative(self) -> Expr:
        left = self.parse_unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_unary(self) -> Expr:
        if self.match(TokenType.MINUS, TokenType.NOT):
            op = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(op=op, operand=operand)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        if self.match(TokenType.NUMBER):
            token = self.advance()
            return Num(value=int(token.value))

        if self.match(TokenType.STRING):
            token = self.advance()
            return StringLit(value=token.value)

        if self.match(TokenType.IDENT):
            name_token = self.advance()
            if self.match(TokenType.LPAREN):
                # Вызов функции
                return self.parse_func_call(name_token.value)
            return Ident(name=name_token.value)

        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr

        self.error(f"Unexpected token in expression: {self.current().type}")

    def parse_func_call(self, name: str) -> FuncCall:
        self.expect(TokenType.LPAREN)
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self.parse_expr())
            while self.match(TokenType.COMMA):
                self.advance()
                args.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return FuncCall(name=name, args=args)

    def parse_expr_rest(self, left: Expr) -> Expr:
        """Продолжает разбор выражения после первого элемента."""
        return self.parse_binary_op_rest(left, 0)

    def parse_binary_op_rest(self, left: Expr, min_prec: int) -> Expr:
        """Pratt parsing для бинарных операций."""
        prec_map = {
            "||": 1,
            "&&": 2,
            "==": 3,
            "!=": 3,
            "<": 4,
            ">": 4,
            "<=": 4,
            ">=": 4,
            "+": 5,
            "-": 5,
            "*": 6,
            "/": 6,
            "%": 6,
        }

        while True:
            token = self.current()
            if token.type not in [
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.STAR,
                TokenType.SLASH,
                TokenType.PERCENT,
                TokenType.EQ,
                TokenType.NE,
                TokenType.LT,
                TokenType.GT,
                TokenType.LE,
                TokenType.GE,
                TokenType.AND,
                TokenType.OR,
            ]:
                break

            op = token.value
            prec = prec_map.get(op, 0)
            if prec < min_prec:
                break

            self.advance()
            right = self.parse_unary()

            while True:
                next_token = self.current()
                if next_token.type not in prec_map:
                    break
                next_prec = prec_map.get(next_token.value, 0)
                if next_prec <= prec:
                    break
                right = self.parse_binary_op_rest(right, next_prec)

            left = BinOp(op=op, left=left, right=right)

        return left


def parse(tokens: list[Token]) -> Program:
    """Удобная функция для парсинга."""
    parser = Parser(tokens)
    return parser.parse()
