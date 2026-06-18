#include <iostream>
void foo(const int* p){
    std::cout<<"恭喜你成功调用foo函数"<<std::endl;
}
void bar(int* const p){
    std::cout<<"恭喜你成功调用bar函数"<<std::endl;
}
int const_main(){
    int a = 42;
    const int b = 100;
    
    const int* p1 = &a;
    int* const p2 = &a;
    p1 = &b;
    *p2 = 200;
    return 0;
}

int main(){
    int a = 42;
    const int b = 100;
    foo(&a);
    foo(&b);
    bar(&a);
    return 0;
}