## Язык программирования

### Общая характеристика

Реализован императивный язык программирования `alg` с Java/Lua-подобным синтаксисом. Язык поддерживает переменные, условия, циклы, функции, строки и ввод-вывод.

### Синтаксис (BNF)

```bnf
program     ::= { statement }
statement   ::= assignment | if_stmt | while_stmt | for_stmt
              | print_stmt | read_stmt | func_def | return_stmt | block
assignment  ::= IDENTIFIER "=" expression ";"
var_decl    ::= ("let" | "int" | "char") IDENTIFIER ["=" expression] ";"
if_stmt     ::= "if" "(" expression ")" block [ "else" block ]
while_stmt  ::= "while" "(" expression ")" block
for_stmt    ::= "for" "(" init ";" cond ";" update ")" block
print_stmt  ::= "print" "(" expression ")" ";"
read_stmt   ::= "read" "(" IDENTIFIER ")" ";"
func_def    ::= "function" IDENTIFIER "(" [params] ")" block
return_stmt ::= "return" [expression] ";"
block       ::= "{" { statement } "}"

expression  ::= or_expr
or_expr     ::= and_expr { "||" and_expr }
and_expr    ::= equality { "&&" equality }
equality    ::= comparison { ("=="|"!=") comparison }
comparison  ::= addition { ("<"|">"|"<="|">=") addition }
addition    ::= multiply { ("+"|"-") multiply }
multiply    ::= unary { ("*"|"/"|"%") unary }
unary       ::= ["-"] primary
primary     ::= NUMBER | STRING | IDENTIFIER | "(" expression ")"
              | func_call | "true" | "false"
```

### Семантика

- **Стратегия вычислений**: строгая (applicative order)
- **Области видимости**: лексические. Глобальные переменные доступны везде.
- **Типизация**: динамическая. Типы: integer, char.
- **Литералы**: целые (`42`, `0xFF`), строковые (`"hello"`).
- **Вывод строк**: `print("строка")` выводит как есть, без `\n`. Для переноса используйте `print("\n")`.

### Отображение выражений на регистры

Сложные выражения вычисляются через последовательность инструкций с сохранением промежуточных результатов в регистры R0-R3. Результат выражения всегда в R0.

## Организация памяти

### Модель памяти (Von Neumann)

Единое адресное пространство 64KB (16-бит адреса). Машинное слово — 32 бита.

```
┌─────────────────────────────────────────┐
│ 0x0000-0x00FF  Вектор прерываний       │ (резерв)
│ 0x0100-0x0FFF  Код программы           │ (~3.5KB, паддинг до 3840 байт)
│ 0x1000-0x7FFF  Данные                  │ (переменные, константы)
│ 0x8000-0xFFFF  Стек (растёт вниз)      │
└─────────────────────────────────────────┘
```

### Регистры

| Регистр | Размер | Назначение |
|---------|--------|------------|
| R0-R3 | 32 бит | Общего назначения |
| PC | 16 бит | Счётчик команд |
| MAR | 16 бит | Memory Address Register |
| MDR | 32 бит | Memory Data Register |
| FLAGS | — | Z (zero), N (negative) |
| V0-V3 | 4×32 бита | Векторные регистры |

### Размещение данных

- **Переменные**: Глобальные, статическая память (0x1000+), по 4 байта.
- **Строки**: C-строки (null-terminated), вывод посимвольно через OUT.

## Система команд

### Формат инструкций (CISC, переменная длина)

```
Байт 0: [OPCODE:6 бит][MOD:2 бита]
Байт 1+: Операнды (зависят от MOD)
```

### Режимы адресации

| MOD | Название | Формат | Длина |
|-----|----------|--------|-------|
| 00 | Рег-Рег | `[OPCODE][MOD][Rd\|Rs]` | 2 байта |
| 01 | Рег-Imm | `[OPCODE][MOD][Rd][imm16]` | 4 байта |
| 10 | Рег-Память | `[OPCODE][MOD][Rd][addr16]` | 4 байта |
| 11 | Прямой адрес | `[OPCODE][MOD][addr16]` | 3 байта |

### Набор инструкций

| Инструкция | Opcode | Описание |
|------------|--------|----------|
| MOV Rd, #imm | 0x02 | Загрузка константы |
| ADD Rd, Rs | 0x04 | Сложение |
| SUB Rd, Rs | 0x05 | Вычитание |
| MUL Rd, Rs | 0x06 | Умножение |
| DIV Rd, Rs | 0x07 | Деление |
| AND/OR Rd, Rs | 0x08/0x09 | Побитовые операции |
| CMP Rs1, Rs2 | 0x0C | Сравнение |
| JMP addr | 0x10 | Безусловный переход |
| JZ/JNZ addr | 0x11/0x12 | Условные переходы |
| JL/JG addr | 0x13/0x14 | Переходы по флагам |
| LOAD R, [addr] | 0x20 | Загрузка из памяти |
| STORE [addr], R | 0x21 | Сохранение в память |
| IN R, port | 0x40 | Ввод из порта |
| OUT port, R | 0x41 | Вывод в порт |
| VADD/VMUL | 0x5A/0x5C | Векторные операции |

### Кодирование: пример MOV R0, #42

```
Opcode=0x02 (MOV), MOD=01 (IMM)
Байт 0: (0x02 << 2) | 0x01 = 0x09
Байт 1: (Rd=0 << 4) = 0x00
Байт 2: 42 & 0xFF = 0x2A
Байт 3: 42 >> 8 = 0x00
Результат: 09 00 2A 00
```

## Транслятор

### Интерфейс

```bash
python tools/compile.py <input.alg> [-o output.bin] [--debug] [--lst listing.txt]
```

### Этапы компиляции

1. **Лексический анализ** (`src/lang/lexer.py`): токенизация исходного кода
2. **Синтаксический анализ** (`src/lang/parser.py`): построение AST
3. **Генерация кода** (`src/translator/codegen.py`): AST → машинные инструкции
4. **Сборка образа** (`src/utils/image.py`): заголовок ALG4 + code + data

### Бинарный формат ALG4

```
[Magic: "ALG4" (4 байта)]
[Version: uint16 LE]
[Entry: uint16 LE]
[Text offset: uint16 LE]
[Text size: uint16 LE]
[Data offset: uint16 LE]
[Data size: uint16 LE]
[Code section]
[Data section]
```

## Модель процессора

### Архитектура

- **Тип**: CISC с переменной длиной инструкций
- **Память**: Von Neumann, единое 64KB адресное пространство
- **Управление**: Микрокодированное (MICROCODE словарь)
- **Точность**: Tick-accurate (1 микрооперация = 1 такт)

### DataPath

- ALU: арифметика, логика, сравнения
- Регистры: R0-R3 (общего назначения), V0-V3 (векторные)
- Память: единая, байтовая адресация
- I/O: Port-mapped (порт 0x01=stdin, 0x02=stdout)

### Микрокод

Каждая инструкция = список микроопераций. Пример для ADD:

```python
MICROCODE[0x04] = [
    FETCH_ADDR,    # MAR ← PC
    FETCH_MEM,     # MDR ← MEM[MAR]; PC++
    DECODE,        # Декодировать operands
    REG_READ_A,    # A ← R[0]
    REG_READ_B,    # B ← R[1]
    ALU_ADD,       # R[0] ← A + B
]
```

## Тестирование

### Запуск тестов

```bash
bash run_test.sh
# или
python -m pytest tests/unit/ -v
ruff check src/ tools/
```

### Юнит-тесты (35 тестов)

- `test_lang.py`: лексер (7) + парсер (8) + AST (1)
- `test_isa_simulator.py`: кодирование/декодирование (4) + симулятор (2)
- `test_processor.py`: инструкции (3) + I/O (1) + векторы (2) + память (3) + флаги (3)

### Примеры (golden-тесты)

Расположены в `examples/`:

| # | Название | Описание |
|---|----------|----------|
| 01 | hello | Hello World |
| 02 | cat | Эхо ввода |
| 03 | hello_user_name | Приветствие пользователя |
| 04 | sort | Сортировка чисел |
| 05 | test_simple | Базовая арифметика |
| 06 | double_precision | Арифметика 64 бит |
| 07 | vector_demo | Векторные операции |
| 08 | euler4_scalar | Euler Problem #4 |

## Пример использования

```bash
python tools/compile.py examples/01_hello/source.alg -o /tmp/hello.bin

python tools/run.py /tmp/hello.bin

python tools/compile.py examples/02_cat/source.alg -o /tmp/cat.bin
echo -n "Hi" > /tmp/in.txt
python tools/run.py /tmp/cat.bin /tmp/in.txt

python tools/compile.py examples/01_hello/source.alg -o /tmp/hello.bin --lst /tmp/hello.lst
```

## Структура проекта

```
├── src/
│   ├── lang/         # Язык (lexer, parser, ast)
│   ├── isa/          # Система команд (instructions, encoding)
│   ├── translator/   # Транслятор (codegen)
│   ├── processor/    # Процессор (datapath, simulator, microcode)
│   └── utils/        # Утилиты (binary_io, image)
├── tests/
│   ├── unit/         # 35 юнит-тестов
│   └── golden/       # Golden-тесты
├── examples/         # Примеры программ (01_hello...08_euler4)
├── tools/
│   ├── compile.py    # Компилятор
│   └── run.py        # Симулятор
├── fig/              # Диаграммы
├── .github/workflows/ci.yml
├── run_test.sh
├── pyproject.toml
└── README.md
```
