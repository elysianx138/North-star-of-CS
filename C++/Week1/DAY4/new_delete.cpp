#include <iostream>
#include <cstdlib>
class Test{
public:
    Test(){
        std::cout<<"构造函数被调用了!"<<std::endl;
    }
    ~Test(){
        std::cout<<"析构函数被调用了!"<<std::endl;
    }
};

int main(){
    std::cout<<"=== new 一个对象 ==="<<std::endl;
    Test* t1 = new Test();
    delete t1;

    std::cout<<"=== malloc 一个对象 ==="<<std::endl;
    Test* t2 = (Test*)malloc(sizeof(Test));
    free(t2);
    return 0;
}