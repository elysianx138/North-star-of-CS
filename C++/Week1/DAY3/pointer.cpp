#include <iostream>
int main(){
    int a = 42;
    // *的第一种身份:声明指针
    int* p = &a; //p是指向a的指针

    // *的第二种身份:解引用(读)
    int value = *p; //取p指向的值
    std::cout<<"读取*p:"<<value<<std::endl;

    // *的第三种身份:解引用(写)
    *p = 100;
    std::cout<<"修改后的a值"<<a<<std::endl;
    std::cout<<"修改后的*p值"<<*p<<std::endl;

    return 0;
}