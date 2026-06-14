// Арифметика двойной точности (64 бита на 32-битном слове)
// Тест: double_precision

// Представление 64-битного числа как пары 32-битных (high, low)
// Пример: сложение двух 64-битных чисел

int a_low = 0xFFFFFFFF;   // низшие 32 бита первого числа
int a_high = 0x00000001;  // старшие 32 бита первого числа (число = 0x00000001FFFFFFFF)

int b_low = 0x00000001;   // низшие 32 бита второго числа
int b_high = 0x00000000;  // старшие 32 бита второго числа (число = 0x0000000000000001)

int result_low = 0;
int result_high = 0;
int carry = 0;

// Сложение младших частей
result_low = a_low + b_low;

// Проверка переполнения (carry)
if (result_low < a_low) {
    carry = 1;
} else {
    carry = 0;
}

// Сложение старших частей с учетом переноса
result_high = a_high + b_high + carry;

// Вывод результата в hex (эмуляция через decimal)
print("Result high: ");
print(result_high);
print(", low: ");
print(result_low);
print("\n");

// Ожидаемый результат: 0x0000000200000000
// high = 2, low = 0
