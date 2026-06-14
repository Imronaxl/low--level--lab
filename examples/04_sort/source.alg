// Сортировка пузырьком (упрощенная версия для 5 элементов)
// Тест: sort

int a = 0;
int b = 0;
int c = 0;
int d = 0;
int e = 0;
int temp = 0;

// Чтение 5 чисел
read(a);
read(b);
read(c);
read(d);
read(e);

// Сортировка пузырьком (раскрытые циклы)
// Первый проход
if (a > b) { temp = a; a = b; b = temp; }
if (b > c) { temp = b; b = c; c = temp; }
if (c > d) { temp = c; c = d; d = temp; }
if (d > e) { temp = d; d = e; e = temp; }

// Второй проход
if (a > b) { temp = a; a = b; b = temp; }
if (b > c) { temp = b; b = c; c = temp; }
if (c > d) { temp = c; c = d; d = temp; }

// Третий проход
if (a > b) { temp = a; a = b; b = temp; }
if (b > c) { temp = b; b = c; c = temp; }

// Четвертый проход
if (a > b) { temp = a; a = b; b = temp; }

// Вывод отсортированных значений
print(a);
print(b);
print(c);
print(d);
print(e);