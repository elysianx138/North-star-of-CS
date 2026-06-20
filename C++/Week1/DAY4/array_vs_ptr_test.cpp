#include <iostream>
using namespace std;

int main() {
    int arr[4] = {10, 20, 30, 40};
    int* p = arr;  // decay 发生

    cout << "========== 第一组：地址值 ==========" << endl;
    cout << "arr         = " << arr         << endl;  // decay 成指针
    cout << "&arr[0]     = " << &arr[0]     << endl;  // 首元素地址
    cout << "&arr        = " << &arr        << endl;  // 整个数组地址
    cout << endl;

    cout << "========== 第二组：sizeof 揭露真相 ==========" << endl;
    cout << "sizeof(arr) = " << sizeof(arr) << endl;   // 16
    cout << "sizeof(p)   = " << sizeof(p)   << endl;   // 8
    cout << endl;

    cout << "========== 第三组：步长实验 ==========" << endl;
    cout << "arr + 1     = " << arr + 1     << endl;   // +4 字节
    cout << "&arr + 1    = " << &arr + 1    << endl;   // +16 字节
    cout << "p + 1       = " << p + 1       << endl;   // +4 字节
    cout << endl;

    // 算一下实际跳了多少字节
    long long step_arr   = (long long)(arr + 1) - (long long)arr;
    long long step_and   = (long long)(&arr + 1) - (long long)(&arr);
    long long step_p     = (long long)(p + 1) - (long long)p;

    cout << "arr+1 - arr     = " << step_arr << " 字节" << endl;
    cout << "&arr+1 - &arr   = " << step_and << " 字节" << endl;
    cout << "p+1 - p        = " << step_p   << " 字节" << endl;
    cout << endl;

    cout << "========== 第四组：能否++？ ==========" << endl;
    // arr++;  // 这行编译报错，你取消注释试试
    p++;         // ✅ 指针可以++
    cout << "p++ 之后, *p = " << *p << " (arr[1])" << endl;
    // 恢复 p
    p = arr;

    return 0;
}
