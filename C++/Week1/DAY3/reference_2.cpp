#include <iostream>
int main(){
    int a = 42;
    int* p = &a;
    // 作为取地址符!
    // 得到变量a的地址
    int& r = a;
    // r是a的引用,引用是一个别名
    return 0;
}