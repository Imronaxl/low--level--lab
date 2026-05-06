// Пример программы на языке alg
// Проверка работы парсера и AST

function add(a, b) {
    return a + b;
}

function is_palindrome(n) {
    let original = n;
    let reversed = 0;
    while (n > 0) {
        reversed = reversed * 10 + n % 10;
        n = n / 10;
    }
    return original == reversed;
}

let max = 0;
for (let i = 100; i < 1000; i = i + 1) {
    for (let j = 100; j < 1000; j = j + 1) {
        let prod = i * j;
        if (is_palindrome(prod) && prod > max) {
            max = prod;
        }
    }
}

print(max);
