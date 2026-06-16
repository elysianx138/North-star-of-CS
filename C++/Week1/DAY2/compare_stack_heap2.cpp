#include <iostream>
#include <chrono>
struct Obj{
    int data;
};

int main(){
    const int N = 1000000;
    //栈:反复使用同一栈空间
    auto start = std::chrono::steady_clock::now();
    for (int i = 0;i<N;i++){
        Obj o;
        o.data = i;
    }
    auto end = std::chrono::steady_clock::now();
    std::cout<<"栈:"<<std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()<<"ms"<<std::endl;
    //堆:反复new和delete
    start = std::chrono::steady_clock::now();
    for (int i = 0;i<N;i++){
        Obj* o = new Obj();
        o->data = i;
        delete o;
    }
    end = std::chrono::steady_clock::now();
    std::cout<<"堆:"<<std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()<<"ms"<<std::endl;
    return 0;
}