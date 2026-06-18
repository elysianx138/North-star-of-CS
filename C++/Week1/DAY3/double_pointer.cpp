#include <iostream>
void setToNull(int*& p){
    p = nullptr;
}
int main(){
    int a = 42;
    int* ptr = &a;
    std::cout<<"ptr指向的值是:"<<*ptr<<std::endl;
    std::cout<<"ptr的地址是"<<&ptr<<std::endl;

    setToNull(ptr);

    std::cout<<(ptr==nullptr? "null":"not null")<<std::endl;
    return 0;
}