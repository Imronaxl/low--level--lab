# Лабораторная работа №4 — Полная подготовка к защите

**Вариант:** `alg | cisc | neum | mc | tick | binary | stream | port | cstr | prob1 | vector`

---

## 1. Структура проекта (соответствует эталону)

```
├── .github/workflows/ci.yml    ← CI/CD (GitHub Actions)
├── examples/                   ← Именованные примеры программ
│   ├── 01_hello/               ← Hello World
│   ├── 02_cat/                 ← Эхо ввода
│   ├── 03_hello_user_name/     ← Приветствие
│   ├── 04_sort/                ← Сортировка
│   ├── 05_test_simple/         ← Арифметика
│   ├── 06_double_precision/    ← 64-бит арифметика
│   ├── 07_vector_demo/         ← Векторные операции
│   └── 08_euler4_scalar/       ← Euler Problem #4
├── fig/                        ← Диаграммы (SVG)
│   ├── datapath.svg            ← Схема DataPath
│   ├── memory_map.svg          ← Карта памяти
│   ├── pipeline.svg            ← Pipeline трансляции
│   └── isa_encoding.svg        ← Кодирование ISA
├── src/
│   ├── lang/                   ← Язык программирования
│   │   ├── lexer.py            ← Лексер → токены
│   │   ├── parser.py           ← Парсер → AST
│   │   └── ast.py              ← Узлы AST
│   ├── isa/                    ← Система команд
│   │   ├── instructions.py     ← OpCode, Instruction
│   │   ├── encoding.py         ← Кодирование/декодирование
│   │   ├── encoder.py          ← Ассемблер
│   │   └── decoder.py          ← Дизассемблер
│   ├── translator/
│   │   └── codegen.py          ← AST → машинный код
│   ├── processor/
│   │   ├── datapath.py         ← Регистры, ALU, память
│   │   ├── simulator.py        ← ControlUnit + tick-level
│   │   └── microcode/
│   │       └── microcode.py    ← Микропрограммы
│   └── utils/
│       ├── binary_io.py        ← Бинарный I/O
│       └── image.py            ← Формат ALG4 (magic + заголовок)
├── tests/
│   ├── unit/                   ← 35 юнит-тестов
│   │   ├── test_lang.py        ← Лексер + парсер (16)
│   │   ├── test_isa_simulator.py ← ISA + симулятор (6)
│   │   └── test_processor.py   ← Процессор (13)
│   └── golden/                 ← Golden-тесты
├── tools/
│   ├── compile.py              ← Компилятор (.alg → .bin)
│   └── run.py                  ← Симулятор (.bin → вывод)
├── pyproject.toml              ← Конфигурация проекта
├── run_test.sh                 ← Тест-скрипт
├── README.md                   ← Техническая документация
└── DEFENSE.md                  ← Этот файл
```

---

## 2. Теория: Язык программирования (alg)

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
- **Стратегия**: строгая (applicative order)
- **Области видимости**: лексические
- **Типы**: integer, char
- **Литералы**: `42`, `0xFF`, `"hello"`

### Pipeline трансляции
```
Source (.alg) → Lexer → Tokens → Parser → AST → CodeGen → Binary (ALG4)
```

---

## 3. Теория: Архитектура (CISC + Von Neumann + Vector)

### Память (Von Neumann, 64KB)
```
0x0000-0x00FF: Вектор прерываний (резерв)
0x0100-0x0FFF: Код программы (паддинг до 3840 байт)
0x1000-0x7FFF: Данные (переменные, константы)
0x8000-0xFFFF: Стек (растёт вниз)
```

### Регистры
| Регистр | Размер | Назначение |
|---------|--------|------------|
| R0-R3 | 32 бит | Общего назначения |
| PC | 16 бит | Счётчик команд |
| MAR | 16 бит | Адресный регистр |
| MDR | 32 бит | Регистр данных |
| FLAGS | — | Z (zero), N (negative) |
| V0-V3 | 4×32 бита | Векторные |

### Почему CISC?
- Переменная длина инструкций (1-4 байта)
- 4 режима адресации (рег-рег, рег-imm, рег-память, прямой)
- Векторные расширения

---

## 4. Теория: Система команд (ISA)

### Формат
```
Байт 0: [OPCODE:6][MOD:2]
Байт 1+: Операнды (зависят от MOD)
```

### Инструкции
| Инструкция | Opcode | MOD | Длина |
|------------|--------|-----|-------|
| MOV Rd, #imm | 0x02 | 01 | 4 байта |
| ADD Rd, Rs | 0x04 | 00 | 2 байта |
| CMP Rs1, Rs2 | 0x0C | 00 | 2 байта |
| JMP addr | 0x10 | 11 | 3 байта |
| JZ/JNZ addr | 0x11/0x12 | 11 | 3 байта |
| LOAD R, [addr] | 0x20 | 10 | 4 байта |
| STORE [addr], R | 0x21 | 10 | 4 байта |
| IN R, port | 0x40 | — | 3 байта |
| OUT port, R | 0x41 | — | 3 байта |
| VADD/VMUL | 0x5A/0x5C | — | 2 байта |

### Пример: `MOV R0, #42`
```
Байт 0: (0x02 << 2) | 0x01 = 0x09
Байт 1: 0x00 (Rd=0)
Байт 2: 0x2A (42 low)
Байт 3: 0x00 (42 high)
→ 09 00 2A 00
```

---

## 5. Теория: Микрокод

### Цикл выполнения
```
FETCH_ADDR → FETCH_MEM → DECODE → EXECUTE
```

### Пример: `ADD R0, R1`
```python
MICROCODE[0x04] = [
    FETCH_ADDR,    # MAR ← PC
    FETCH_MEM,     # MDR ← MEM[MAR]; PC++
    DECODE,        # rd=0, rs=1
    REG_READ_A,    # A ← R[0]
    REG_READ_B,    # B ← R[1]
    ALU_ADD,       # R[0] ← A + B
]
```

### Почему микрокод?
- Упрощает ControlUnit
- Легко добавлять инструкции
- 1 микрооперация = 1 такт (tick-accurate)

---

## 6. Теория: CodeGen

### Отображение конструкций
| Язык | Инструкции |
|------|------------|
| `x = 5` | `MOV R0, #5; STORE [addr], R0` |
| `print(x)` | `LOAD R0,[x]; OUT 2,R0` |
| `print("Hi")` | `MOV R0,'H'; OUT 2,R0; MOV R0,'i'; OUT 2,R0` |
| `read(x)` | `IN R0,1; STORE [x],R0` |
| `if (a>b) {...}` | `CMP; JLE skip; ...; skip:` |
| `while (c) {...}` | `loop: CMP; JZ end; ...; JMP loop; end:` |

### Сравнения
```
==: MOV R,0; JNZ done; MOV R,1; done:
!=: MOV R,0; JZ done; MOV R,1; done:
<:  MOV R,1; JL done; MOV R,0; done:
>=: MOV R,0; JL done; MOV R,1; done:
>:  MOV R,0; JL skip; JZ skip; MOV R,1; skip:
<=: MOV R,1; JL skip; JZ skip; MOV R,0; skip:
```

---

## 7. Бинарный формат ALG4

```
Magic: "ALG4" (4 байта)
Version: uint16 LE
Entry: uint16 LE
Text offset: uint16 LE
Text size: uint16 LE
Data offset: uint16 LE
Data size: uint16 LE
[Code section]
[Data section]
```

---

## 8. Инструкция к демонстрации

### Подготовка
```bash
cd "/home/imeon/Рабочий стол/lab4AK/prototype2"
pip install -e ".[dev]" 2>/dev/null
```

### Шаг 1: Тест-скрипт (всё автоматически)
```bash
bash run_test.sh
```
→ Ruff OK, 35 tests PASS, hello/cat/test_simple работают.

### Шаг 2: Тесты вручную
```bash
python -m pytest tests/unit/ -v
```
→ 35 passed. Показать: лексер, парсер, ISA, процессор.

### Шаг 3: Hello World (полный pipeline)
```bash
python tools/compile.py examples/01_hello/source.alg -o /tmp/h.bin
python tools/run.py /tmp/h.bin
```
→ `Hello, World!`

### Шаг 4: Cat (эхо ввода — stream I/O)
```bash
python tools/compile.py examples/02_cat/source.alg -o /tmp/c.bin
echo -n "Hi" > /tmp/in.txt
python tools/run.py /tmp/c.bin /tmp/in.txt
```
→ `Hi`

### Шаг 5: Приветствие (условия + цикл)
```bash
python tools/compile.py examples/03_hello_user_name/source.alg -o /tmp/hun.bin
echo -n "Alice" > /tmp/in.txt
python tools/run.py /tmp/hun.bin /tmp/in.txt
```
→ `What is your name? Hello, Alice!`

### Шаг 6: Сортировка
```bash
python tools/compile.py examples/04_sort/source.alg -o /tmp/s.bin
echo -n "53142" > /tmp/in.txt
python tools/run.py /tmp/s.bin /tmp/in.txt
```
→ `49 50 51 52 53`

### Шаг 7: Арифметика
```bash
python tools/compile.py examples/05_test_simple/source.alg -o /tmp/ts.bin
python tools/run.py /tmp/ts.bin
```
→ `30`

### Шаг 8: Double precision
```bash
python tools/compile.py examples/06_double_precision/source.alg -o /tmp/dp.bin
python tools/run.py /tmp/dp.bin
```
→ `Result high: 1, low: 65536`

### Шаг 9: Векторные операции
```bash
python tools/compile.py examples/07_vector_demo/source.alg -o /tmp/vd.bin
python tools/run.py /tmp/vd.bin
```
→ `Vector ADD result: 6 8 10 12`

### Шаг 10: Lint
```bash
ruff check src/ tools/
```
→ `All checks passed!`

### Шаг 11: Listing файл
```bash
python tools/compile.py examples/01_hello/source.alg -o /tmp/h.bin --lst /tmp/h.lst
cat /tmp/h.lst
```
→ Показать код + исходный текст.

---

## 9. Ответы на вопросы

### Общие
**Q: Какой вариант?**
A: `alg | cisc | neum | mc | tick | binary | stream | port | cstr | prob1 | vector`

**Q: Что реализовали?**
A: Полный pipeline: лексер → парсер → AST → codegen → ALG4 binary → tick-accurate симулятор. 35 тестов, 8 примеров, векторные операции.

### Архитектура
**Q: Как устроена память?**
A: Von Neumann, 64KB. Код: 0x0100, данные: 0x1000, стек: 0x8000.

**Q: Как кодируются инструкции?**
A: `[OPCODE:6][MOD:2]` + операнды. 4 режима адресации.

**Q: Как работает микрокод?**
A: Каждая инструкция = список микроопераций. 1 микрооперация = 1 такт.

### CodeGen
**Q: Как работают сравнения?**
A: Генерируют 0/1 в регистре через CMP + условные переходы.

**Q: Как выводятся числа?**
A: Деление на степени 10, вывод цифр как ASCII.

### Тестирование
**Q: Как тестировали?**
A: 35 unit-тестов + golden-тесты + run_test.sh.

### Ограничения
- euler4_scalar: медленный (tick-accurate)
- euler4_vector: не компилируется (массивы)
- Функции: аргументы/возвраты упрощены

---

## 10. Чек-лист

```bash
cd "/home/imeon/Рабочий стол/lab4AK/prototype2"
bash run_test.sh                        # Всё автоматически
python -m pytest tests/unit/ -q         # 35 passed
ruff check src/ tools/                  # All checks passed!
```

- [ ] Python 3.10+
- [ ] 35/35 тестов
- [ ] 8 примеров работают
- [ ] CI/CD настроен
- [ ] Диаграммы есть (fig/)
- [ ] README полный
- [ ] Можете объяснить архитектуру, ISA, микрокод, codegen
