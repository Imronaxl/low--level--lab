"""
Лексер для языка alg.
Разбивает исходный код на токены.
"""

from dataclasses import dataclass


class TokenType:
    # Литералы
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"

    # Ключевые слова
    LET = "LET"
    FUNCTION = "FUNCTION"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    FOR = "FOR"
    RETURN = "RETURN"
    PRINT = "PRINT"
    READ = "READ"
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    INT = "INT"  # int
    CHAR = "CHAR"  # char

    # Операторы
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    PERCENT = "PERCENT"
    EQ = "EQ"  # ==
    NE = "NE"  # !=
    LT = "LT"  # <
    GT = "GT"  # >
    LE = "LE"  # <=
    GE = "GE"  # >=
    AND = "AND"  # &&
    OR = "OR"  # ||
    ASSIGN = "ASSIGN"  # =
    NOT = "NOT"  # !
    INC = "INC"  # ++
    DEC = "DEC"  # --
    PLUS_EQ = "PLUS_EQ"  # +=
    MINUS_EQ = "MINUS_EQ"  # -=

    # Разделители
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"  # [
    RBRACKET = "RBRACKET"  # ]
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"

    # Специальные
    EOF = "EOF"
    NEWLINE = "NEWLINE"


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"


KEYWORDS = {
    "let": TokenType.LET,
    "function": TokenType.FUNCTION,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
    "read": TokenType.READ,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "int": TokenType.INT,
    "char": TokenType.CHAR,
}


class LexerError(Exception):
    """Ошибка лексера."""

    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def error(self, message: str):
        raise LexerError(f"Lexer error at line {self.line}, column {self.column}: {message}")

    def peek(self) -> str | None:
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek_next(self) -> str | None:
        if self.pos + 1 >= len(self.source):
            return None
        return self.source[self.pos + 1]

    def advance(self) -> str | None:
        ch = self.peek()
        if ch is not None:
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return ch

    def skip_whitespace_and_comments(self):
        while True:
            ch = self.peek()
            if ch is None:
                break
            if ch in " \t\r" or ch == "\n":
                self.advance()
            elif ch == "/" and self.peek_next() == "/":
                # Однострочный комментарий
                while self.peek() and self.peek() != "\n":
                    self.advance()
            elif ch == "/" and self.peek_next() == "*":
                # Многострочный комментарий
                self.advance()  # /
                self.advance()  # *
                while True:
                    if self.peek() is None:
                        self.error("Unterminated comment")
                    if self.peek() == "*" and self.peek_next() == "/":
                        self.advance()  # *
                        self.advance()  # /
                        break
                    self.advance()
            else:
                break

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.column
        result = ""
        while self.peek() and self.peek().isdigit():
            result += self.advance()
        return Token(TokenType.NUMBER, result, start_line, start_col)

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.column
        self.advance()  # opening "
        result = ""
        while True:
            ch = self.peek()
            if ch is None:
                self.error("Unterminated string")
            if ch == '"':
                self.advance()  # closing "
                break
            if ch == "\\":
                self.advance()
                escaped = self.advance()
                if escaped is None:
                    self.error("Unterminated escape sequence")
                if escaped == "n":
                    result += "\n"
                elif escaped == "t":
                    result += "\t"
                elif escaped == "\\":
                    result += "\\"
                elif escaped == '"':
                    result += '"'
                else:
                    result += escaped
            else:
                result += self.advance()
        return Token(TokenType.STRING, result, start_line, start_col)

    def read_ident(self) -> Token:
        start_line, start_col = self.line, self.column
        result = ""
        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
            result += self.advance()

        token_type = KEYWORDS.get(result, TokenType.IDENT)
        return Token(token_type, result, start_line, start_col)

    def add_token(self, token: Token):
        self.tokens.append(token)

    def tokenize(self) -> list[Token]:
        while True:
            self.skip_whitespace_and_comments()

            ch = self.peek()
            if ch is None:
                self.add_token(Token(TokenType.EOF, "", self.line, self.column))
                break

            start_line, start_col = self.line, self.column

            # Числа
            if ch.isdigit():
                self.add_token(self.read_number())
                continue

            # Строки
            if ch == '"':
                self.add_token(self.read_string())
                continue

            # Идентификаторы и ключевые слова
            if ch.isalpha() or ch == "_":
                self.add_token(self.read_ident())
                continue

            # Операторы и разделители (двухсимвольные)
            two_char = ch + (self.peek_next() or "")
            if two_char == "==":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.EQ, "==", start_line, start_col))
            elif two_char == "!=":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.NE, "!=", start_line, start_col))
            elif two_char == "<=":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.LE, "<=", start_line, start_col))
            elif two_char == ">=":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.GE, ">=", start_line, start_col))
            elif two_char == "&&":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.AND, "&&", start_line, start_col))
            elif two_char == "||":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.OR, "||", start_line, start_col))
            elif two_char == "++":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.INC, "++", start_line, start_col))
            elif two_char == "--":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.DEC, "--", start_line, start_col))
            elif two_char == "+=":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.PLUS_EQ, "+=", start_line, start_col))
            elif two_char == "-=":
                self.advance()
                self.advance()
                self.add_token(Token(TokenType.MINUS_EQ, "-=", start_line, start_col))
            # Односимвольные
            elif ch == "+":
                self.advance()
                self.add_token(Token(TokenType.PLUS, "+", start_line, start_col))
            elif ch == "-":
                self.advance()
                self.add_token(Token(TokenType.MINUS, "-", start_line, start_col))
            elif ch == "*":
                self.advance()
                self.add_token(Token(TokenType.STAR, "*", start_line, start_col))
            elif ch == "/":
                self.advance()
                self.add_token(Token(TokenType.SLASH, "/", start_line, start_col))
            elif ch == "%":
                self.advance()
                self.add_token(Token(TokenType.PERCENT, "%", start_line, start_col))
            elif ch == "<":
                self.advance()
                self.add_token(Token(TokenType.LT, "<", start_line, start_col))
            elif ch == ">":
                self.advance()
                self.add_token(Token(TokenType.GT, ">", start_line, start_col))
            elif ch == "=":
                self.advance()
                self.add_token(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch == "!":
                self.advance()
                self.add_token(Token(TokenType.NOT, "!", start_line, start_col))
            elif ch == "(":
                self.advance()
                self.add_token(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                self.advance()
                self.add_token(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == "{":
                self.advance()
                self.add_token(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == "}":
                self.advance()
                self.add_token(Token(TokenType.RBRACE, "}", start_line, start_col))
            elif ch == "[":
                self.advance()
                self.add_token(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == "]":
                self.advance()
                self.add_token(Token(TokenType.RBRACKET, "]", start_line, start_col))
            elif ch == ",":
                self.advance()
                self.add_token(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == ";":
                self.advance()
                self.add_token(Token(TokenType.SEMICOLON, ";", start_line, start_col))
            else:
                self.error(f"Unexpected character: {ch!r}")

        return self.tokens


def tokenize(source: str) -> list[Token]:
    """Удобная функция для токенизации."""
    lexer = Lexer(source)
    return lexer.tokenize()
