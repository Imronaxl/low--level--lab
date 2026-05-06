// Hello User Name - запрос имени и приветствие
print("What is your name?");
char name[100];
int i = 0;
char c;

// Чтение имени посимвольно
while (true) {
    read(c);
    if (c == 0 || c == '\n') {
        break;
    }
    name[i] = c;
    i = i + 1;
}
name[i] = 0;  // null-терминатор

// Вывод приветствия
print("Hello, ");
// Печать строки из массива символов
int j = 0;
while (name[j] != 0) {
    print(name[j]);
    j = j + 1;
}
print("!");
