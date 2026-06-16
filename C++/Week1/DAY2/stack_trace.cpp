#include<iostream>
void func2(){
    int c = 3;
    std::cout<<"func2:&c = "<<&c<<std::endl;
}

void func1(){
    int b = 2;
    std::cout<<"func1:&b = "<<&b<<std::endl;
    func2();
}
int main(){
    int a = 1;
    std::cout<<"main:&a = "<<&a<<std::endl;
    func1();
    return 0;
}