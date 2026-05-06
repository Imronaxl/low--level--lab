// Euler Problem 4 (Vector) - наибольший палиндром с использованием векторных инструкций
// Демонстрация векторизации: одновременная проверка нескольких произведений

// Векторные регистры V0-V7, каждый содержит 4 элемента (32-bit)
// Инструкции: VLOAD, VSTORE, VADD, VMUL, VCMP, VREV (разворот цифр)

// Упрощенная векторная реализация для демонстрации:
// 1. Загружаем массив произведений в векторный регистр
// 2. Применяем векторную операцию проверки палиндрома
// 3. Находим максимум среди подходящих

function is_palindrome_vec(int v0, int v1, int v2, int v3) {
    // Векторная проверка 4 чисел одновременно
    // Возвращает битовую маску: бит i = 1 если число i - палиндром
    
    int mask = 0;
    
    // Проверка v0
    int rev0 = reverse_digits(v0);
    if (rev0 == v0) { mask = mask | 1; }
    
    // Проверка v1
    int rev1 = reverse_digits(v1);
    if (rev1 == v1) { mask = mask | 2; }
    
    // Проверка v2
    int rev2 = reverse_digits(v2);
    if (rev2 == v2) { mask = mask | 4; }
    
    // Проверка v3
    int rev3 = reverse_digits(v3);
    if (rev3 == v3) { mask = mask | 8; }
    
    return mask;
}

function reverse_digits(int n) {
    int reversed = 0;
    while (n > 0) {
        reversed = reversed * 10 + (n % 10);
        n = n / 10;
    }
    return reversed;
}

int max = 0;

// Векторизованный внешний цикл: обрабатываем по 4 значения i одновременно
int i = 996;  // кратно 4 для выравнивания

while (i >= 100) {
    // Вычисляем 4 произведения: i*999, (i+1)*999, (i+2)*999, (i+3)*999
    int p0 = i * 999;
    int p1 = (i + 1) * 999;
    int p2 = (i + 2) * 999;
    int p3 = (i + 3) * 999;
    
    // Векторная проверка палиндромов
    int mask = is_palindrome_vec(p0, p1, p2, p3);
    
    // Обновляем максимум для каждого палиндрома
    if ((mask & 1) != 0 && p0 > max) { max = p0; }
    if ((mask & 2) != 0 && p1 > max) { max = p1; }
    if ((mask & 4) != 0 && p2 > max) { max = p2; }
    if ((mask & 8) != 0 && p3 > max) { max = p3; }
    
    i = i - 4;
}

output_num(max);
output_char('\n');
