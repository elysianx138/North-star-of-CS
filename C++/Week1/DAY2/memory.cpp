#include<iostream>
int global_var = 999; // 数据段
void stackFunc(){
    int localA = 42; //栈
    int localB = 100; //栈->位于localA旁边
    std::cout<<"栈上变量localA的地址:"<<&localA<<std::endl;
    std::cout<<"栈上变量localB的地址:"<<&localB<<std::endl;
}

int main(){
    int* p = new int(777); // p在栈上,但是777存在堆上
    std::cout<<"全局变量global_var的地址:"<<&global_var<<std::endl;
    std::cout<<"栈上指针p的地址:"<<&p<<std::endl;
    std::cout<<"堆上变量777的地址:"<<p<<std::endl;
    stackFunc();
    delete p;
    return 0;

}