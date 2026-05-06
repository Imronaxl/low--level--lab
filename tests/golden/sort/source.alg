// Sort - сортировка списка чисел (простая пузырьковая сортировка)
// Ввод: количество чисел N, затем N чисел
// Вывод: отсортированные числа

int n;
n = input_num();  // читаем количество элементов

int arr[100];  // макс. 100 элементов
int i = 0;

// Чтение массива
while (i < n) {
    arr[i] = input_num();
    i = i + 1;
}

// Пузырьковая сортировка
int swapped = 1;
while (swapped != 0) {
    swapped = 0;
    i = 0;
    while (i < n - 1) {
        if (arr[i] > arr[i + 1]) {
            int temp = arr[i];
            arr[i] = arr[i + 1];
            arr[i + 1] = temp;
            swapped = 1;
        }
        i = i + 1;
    }
}

// Вывод отсортированного массива
i = 0;
while (i < n) {
    output_num(arr[i]);
    output_char('\n');
    i = i + 1;
}
