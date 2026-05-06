// Vector Demo - демонстрация векторных инструкций
// Векторные регистры V0-V7, каждый содержит 4 элемента (32-bit)

// Объявление векторных переменных
vector int v1 = {1, 2, 3, 4};
vector int v2 = {10, 20, 30, 40};
vector int result;

// Векторное сложение: result = v1 + v2
result = v1 + v2;  // {11, 22, 33, 44}

// Вывод результатов поэлементно
output_num(result[0]);
output_char(' ');
output_num(result[1]);
output_char(' ');
output_num(result[2]);
output_char(' ');
output_num(result[3]);
output_char('\n');

// Векторное умножение
v1 = v1 * v2;  // {10, 40, 90, 160}

output_num(v1[0]);
output_char(' ');
output_num(v1[1]);
output_char(' ');
output_num(v1[2]);
output_char(' ');
output_num(v1[3]);
output_char('\n');

// Векторное сравнение: создание маски
vector int cmp_result = v1 > v2;
// cmp_result[i] = 0xFFFFFFFF если v1[i] > v2[i], иначе 0

output_num(cmp_result[0]);
output_char(' ');
output_num(cmp_result[1]);
output_char('\n');
