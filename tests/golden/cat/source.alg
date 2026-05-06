// Cat - эхо ввода (бесконечный поток)
char c;
while (true) {
    read(c);
    if (c == 0) {
        return;
    }
    print(c);
}
