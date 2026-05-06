"""
Модульные тесты для лексера и парсера.
"""

from src.lang import ast, parse, tokenize


class TestLexer:
    def test_number(self):
        tokens = tokenize("123")
        assert tokens[0].type == "NUMBER"
        assert tokens[0].value == "123"

    def test_string(self):
        tokens = tokenize('"hello"')
        assert tokens[0].type == "STRING"
        assert tokens[0].value == "hello"

    def test_ident(self):
        tokens = tokenize("foo_bar")
        assert tokens[0].type == "IDENT"
        assert tokens[0].value == "foo_bar"

    def test_keywords(self):
        tokens = tokenize("let function if else while for return print read")
        expected = ["LET", "FUNCTION", "IF", "ELSE", "WHILE", "FOR", "RETURN", "PRINT", "READ"]
        for i, exp in enumerate(expected):
            assert tokens[i].type == exp

    def test_operators(self):
        tokens = tokenize("+ - * / % == != < > <= >= && || = !")
        types = [t.type for t in tokens[:-1]]  # без EOF
        assert types == [
            "PLUS",
            "MINUS",
            "STAR",
            "SLASH",
            "PERCENT",
            "EQ",
            "NE",
            "LT",
            "GT",
            "LE",
            "GE",
            "AND",
            "OR",
            "ASSIGN",
            "NOT",
        ]

    def test_comments_single_line(self):
        tokens = tokenize("let x = 5 // comment\nprint(x)")
        values = [t.value for t in tokens if t.type in ("LET", "PRINT")]
        assert "LET" in [t.type for t in tokens]
        assert "PRINT" in [t.type for t in tokens]

    def test_comments_multi_line(self):
        tokens = tokenize("let /* comment */ x = 5")
        assert len([t for t in tokens if t.type == "LET"]) == 1


class TestParser:
    def test_var_decl(self):
        ast_tree = parse(tokenize("let x = 5;"))
        assert len(ast_tree.declarations) == 1
        decl = ast_tree.declarations[0]
        assert isinstance(decl, ast.VarDecl)
        assert decl.name == "x"
        assert isinstance(decl.init, ast.Num)
        assert decl.init.value == 5

    def test_assign(self):
        ast_tree = parse(tokenize("x = 10;"))
        assert len(ast_tree.declarations) == 1
        assign = ast_tree.declarations[0]
        assert isinstance(assign, ast.Assign)
        assert assign.target.name == "x"
        assert assign.value.value == 10

    def test_binop(self):
        ast_tree = parse(tokenize("let y = 2 + 3 * 4;"))
        decl = ast_tree.declarations[0]
        expr = decl.init
        assert isinstance(expr, ast.BinOp)
        assert expr.op == "+"
        assert isinstance(expr.left, ast.Num)
        assert expr.left.value == 2
        assert isinstance(expr.right, ast.BinOp)
        assert expr.right.op == "*"

    def test_if_stmt(self):
        ast_tree = parse(tokenize("if (x > 0) { print(x); } else { print(0); }"))
        assert len(ast_tree.declarations) == 1
        if_stmt = ast_tree.declarations[0]
        assert isinstance(if_stmt, ast.IfStmt)
        assert isinstance(if_stmt.cond, ast.BinOp)
        assert len(if_stmt.then_body) == 1
        assert len(if_stmt.else_body) == 1

    def test_while_stmt(self):
        ast_tree = parse(tokenize("while (x < 10) { x = x + 1; }"))
        assert len(ast_tree.declarations) == 1
        while_stmt = ast_tree.declarations[0]
        assert isinstance(while_stmt, ast.WhileStmt)
        assert len(while_stmt.body) == 1

    def test_for_stmt(self):
        code = "for (let i = 0; i < 10; i++) { print(i); }"
        ast_tree = parse(tokenize(code))
        assert len(ast_tree.declarations) == 1
        for_stmt = ast_tree.declarations[0]
        assert isinstance(for_stmt, ast.ForStmt)
        assert isinstance(for_stmt.init, ast.VarDecl)

    def test_func_def(self):
        code = "function add(a, b) { return a + b; }"
        ast_tree = parse(tokenize(code))
        assert len(ast_tree.declarations) == 1
        func = ast_tree.declarations[0]
        assert isinstance(func, ast.FuncDef)
        assert func.name == "add"
        assert func.params == ["a", "b"]
        assert func.return_expr is not None

    def test_func_call(self):
        ast_tree = parse(tokenize("print(add(2, 3));"))
        print_stmt = ast_tree.declarations[0]
        assert isinstance(print_stmt, ast.PrintStmt)
        call = print_stmt.expr
        assert isinstance(call, ast.FuncCall)
        assert call.name == "add"
        assert len(call.args) == 2

    def test_complex_expr(self):
        code = "let result = (a + b) * (c - d) / 2;"
        ast_tree = parse(tokenize(code))
        decl = ast_tree.declarations[0]
        expr = decl.init
        assert isinstance(expr, ast.BinOp)
        assert expr.op == "/"


class TestAST:
    def test_ast_readability(self):
        """Проверка что AST человекочитаемое (требование варианта alg)."""
        code = """
        let x = 42;
        let y = x * 2 + 10;
        if (y > 100) {
            print(y);
        } else {
            print(0);
        }
        """
        ast_tree = parse(tokenize(code))

        # Проверяем структуру
        assert len(ast_tree.declarations) == 3

        var_x = ast_tree.declarations[0]
        assert var_x.name == "x"
        assert var_x.init.value == 42

        var_y = ast_tree.declarations[1]
        assert var_y.name == "y"
        assert isinstance(var_y.init, ast.BinOp)

        if_stmt = ast_tree.declarations[2]
        assert isinstance(if_stmt, ast.IfStmt)
        assert isinstance(if_stmt.cond, ast.BinOp)
        assert if_stmt.cond.op == ">"
