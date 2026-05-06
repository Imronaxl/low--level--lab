// Double Precision Arithmetic - арифметика 64 бит на 32-битном процессоре
// Используем два 32-битных регистра для представления 64-битного числа
// Формат: [high:32][low:32]

// Пример: сложение двух 64-битных чисел
// a = 0x00000001_00000000 (2^32)
// b = 0x00000000_FFFFFFFF (2^32 - 1)
// результат: 0x00000001_FFFFFFFF

int a_low = 0;
int a_high = 1;
int b_low = -1;  // 0xFFFFFFFF в дополнении до двух
int b_high = 0;

// Сложение младших частей
int res_low = a_low + b_low;
int carry = 0;
if (res_low < a_low) {  // проверка на переполнение
    carry = 1;
}

// Сложение старших частей с учетом переноса
int res_high = a_high + b_high + carry;

// Вывод результата (для демонстрации)
output_num(res_high);
output_char(' ');
output_num(res_low);
output_char('\n');

// Проверка: должно быть 1 FFFFFFFF (или 1 -1 в знаковой форме)
