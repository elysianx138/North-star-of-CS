#include <iostream>
int main(){
    //字符数组
    char str1[] = "hello";
    
    //字符指针
    const char* str2 = "hello";

    //进行修改
    std::cout<<"str1 = "<<str1<<std::endl;
    std::cout<<"str2 = "<<str2<<std::endl;
    
    str1[0] = 'H';
    // str2[0] = 'H';
    std::cout<<"str1 = "<<str1<<std::endl;
    std::cout<<"str2 = "<<str2<<std::endl;
    std::cout<<"sizeof(str1) = "<<sizeof(str1)<<std::endl;
    std::cout<<"sizeof(str2) = "<<sizeof(str2)<<std::endl;
    return 0;
}