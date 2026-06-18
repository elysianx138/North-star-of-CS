#include <iostream>
int main(){
    int a = 42;
    //指针
    int* p = &a;
    *p = 100; //手动解引用

    //引用
    int& r = a;
    r = 200;//自动解引用

    std::cout<<"a的值"<<a<<std::endl;
    std::cout<<"p的值"<<p<<std::endl;
    std::cout<<"*p的值"<<*p<<std::endl;
    std::cout<<"r的值"<<r<<std::endl;
    std::cout<<"&r的值"<<&r<<std::endl;
    return 0;
}