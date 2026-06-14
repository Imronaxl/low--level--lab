// Hello User Name - запрос имени и приветствие
print("What is your name?\n");
char c;
print("Hello, ");
while (true) {
    read(c);
    if (c == 0) {
        break;
    }
    if (c == 10) {
        break;
    }
    print(c);
}
print("!\n");
