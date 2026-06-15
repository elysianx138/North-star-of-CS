#include <iostream>

void greet() {
    // 假装这里有一大堆运算
    long long sum = 0;
    for (int i = 0; i < 100; i++) {
        sum += i;
    }
    std::cout << "greet: 计算完毕, sum = " << sum << std::endl;
}
