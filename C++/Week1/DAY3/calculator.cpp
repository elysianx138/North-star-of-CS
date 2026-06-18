#include<iostream>
int main(){
    int arr[] = {10,20,30,40};
    int* p = arr;
    std::cout<<"arr[0]的地址:"<<&arr[0]<<std::endl;
    std::cout<<"arr[1]的地址:"<<&arr[1]<<std::endl;
    std::cout<<"arr[2]的地址:"<<&arr[2]<<std::endl;
    std::cout<<"arr[3]的地址:"<<&arr[3]<<std::endl;

    std::cout<<std::endl;

    std::cout<<"p的值:"<<p<<std::endl;
    std::cout<<"p+1的值"<<p+1<<std::endl;
    std::cout<<"p+2的值"<<p+2<<std::endl;

    std::cout<<std::endl;

    std::cout<<"*p的值"<<*p<<std::endl;
    std::cout<<"*(p+1)的值"<<*(p+1)<<std::endl;
    std::cout<<"*(p+2)的值"<<*(p+2)<<std::endl;
    return 0;
}