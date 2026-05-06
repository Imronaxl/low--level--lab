// Euler Problem 4 (Scalar) - наибольший палиндром из произведения двух 3-значных чисел
// Поиск скалярным методом (без векторизации)

function is_palindrome(int n) {
    int original = n;
    int reversed = 0;
    
    while (n > 0) {
        int digit = n % 10;
        reversed = reversed * 10 + digit;
        n = n / 10;
    }
    
    return original == reversed;
}

int max = 0;
int i = 999;

while (i >= 100) {
    int j = 999;
    while (j >= 100) {
        int prod = i * j;
        
        // Оптимизация: если произведение меньше текущего максимума, пропускаем
        if (prod > max) {
            if (is_palindrome(prod)) {
                max = prod;
            }
        }
        
        j = j - 1;
    }
    i = i - 1;
}

output_num(max);
output_char('\n');
