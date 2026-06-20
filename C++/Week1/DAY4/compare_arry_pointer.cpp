#include <iostream>
int main(){
    int arr[4] = {10,20,30,40};
    std::cout<<"arr = "<<arr<<std::endl;
    std::cout<<"&arr[0] = "<<&arr[0]<<std::endl;
    std::cout<<"&arr = "<<&arr<<std::endl;

    std::cout<<"sizeof(arr) = "<<sizeof(arr)<<std::endl;
    std::cout<<"sizeof(&arr[0]) = "<<sizeof(&arr[0])<<std::endl;

    std::cout<<"arr + 1 = "<<arr + 1<<std::endl;
    std::cout<<"&arr + 1 = "<<&arr + 1<<std::endl;
    return 0;
}