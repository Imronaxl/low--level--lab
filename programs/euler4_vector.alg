// Euler Problem 4: Векторная версия
// Тест: euler4_vector

// Векторизованная проверка палиндромов для массива произведений
// Векторные регистры V0-V3 содержат по 4 числа

int vec_size = 4;
int products[4];
int reversed[4];
int originals[4];
int is_palindrome_mask[4];
int max = 0;
int i, j, k;

// Генерация первых 4 произведений для демонстрации
k = 0;
i = 999;
while (i >= 996 && k < 4) {
    j = 999;
    while (j >= 999 && k < 4) {  // только одно произведение для простоты
        products[k] = i * j;
        k = k + 1;
        j = j - 1;
    }
    i = i - 1;
}

// Загрузка в векторный регистр
vload V0, products;

// Копирование для проверки палиндрома
vadd V1, V0, 0;  // V1 = originals

// Векторная проверка палиндрома (упрощенно - эмуляция через скалярную)
// В реальной векторной архитектуре это делалось бы параллельно
k = 0;
while (k < vec_size) {
    int n = products[k];
    int orig = n;
    int rev = 0;
    
    while (n > 0) {
        rev = rev * 10 + n % 10;
        n = n / 10;
    }
    
    if (orig == rev) {
        is_palindrome_mask[k] = 1;
        if (orig > max) {
            max = orig;
        }
    } else {
        is_palindrome_mask[k] = 0;
    }
    
    k = k + 1;
}

print("Vector demo - checking palindromes:");
print("\n");
k = 0;
while (k < vec_size) {
    print_int(products[k]);
    print(" -> palindrome: ");
    print_int(is_palindrome_mask[k]);
    print("\n");
    k = k + 1;
}

print("Max found: ");
print_int(max);
print("\n");
