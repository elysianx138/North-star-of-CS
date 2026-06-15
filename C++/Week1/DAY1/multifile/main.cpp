#include <iostream>

void greet();  // 声明：这个函数在另一个文件里

int main() {
    std::cout << "main: 调用 greet 之前" << std::endl;
    greet();
    std::cout << "main: 调用 greet 之后" << std::endl;
    return 0;
}
