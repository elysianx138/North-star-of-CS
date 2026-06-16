#include <iostream>
#include <chrono>

int main(){
    const int N = 1000000;

    // === 栈:连续分配int ===
    auto start = std::chrono::steady_clock::now();
    int arr[N]; //声明栈
    for(int i = 0;i<N;i++) arr[i] = i;
    auto end = std::chrono::steady_clock::now();
    std::cout<<"栈:"<<std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()<<"ms"<<std::endl;

    // === 堆:手动new int ===
    start = std::chrono::steady_clock::now();
    int* arr2 = new int[N]; //声明堆
    for(int i = 0;i<N;i++) arr2[i] = i;
    
    end = std::chrono::steady_clock::now();
    std::cout<<"堆:"<<std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()<<"ms"<<std::endl;
    delete[] arr2;
    return 0;
}