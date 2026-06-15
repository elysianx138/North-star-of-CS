# C++ DAY1 — 编译流水线

> **阅读前提：** 本章不讲任何 C++ 语法基础，你需要有基本的编程语言经验（C / Python 均可）。
>
> **核心主题：** 一个 `.cpp` 文件到底经历了什么，才变成能跑的程序？

---

## 环境准备

本章所有操作在 **WSL（Ubuntu）** 下完成，VS Code 需要安装相应插件。

```bash
# 进入 WSL 环境
wsl
cd /your/project/path
```

---

## 一、写一个 Hello World

```cpp
// hello.cpp
#include <iostream>
int main() {
    int a = 42;
    std::cout << a << std::endl;
    return 0;
}
```

**编译运行：**

```bash
g++ hello.cpp -o hello && ./hello
# 输出：42
```

---

## 二、预处理 — 看看 `#include` 的真面目

```bash
g++ -E hello.cpp -o hello.i
```

- `-E`：只做预处理，不做别的
- `hello.i` 里 iostream 头文件被**原地展开**，你 7 行代码 → **约 37,000 行**

```
Q：打开 hello.i 后看到什么？
A：几万行展开代码。翻到底，能看到你的 main 函数还在。
```

**本质：** `#include` = 字面意义的复制粘贴，没有 Python 的 import 机制。

---

## 三、编译为汇编 — CPU 眼中的代码

```bash
g++ -S hello.i -o hello.s
```

查看汇编内容：

```bash
cat hello.s
```

**关键一行：**

```asm
movl	$42, -4(%rbp)    ← 把 42 存到栈上（一条 CPU 指令）
```

```
        movl	-4(%rbp), %eax
        leaq	_ZSt4cout(%rip), %rdx
        movl	%eax, %esi
        movq	%rdx, %rdi
        call	_ZNSolsEi@PLT    ← 调用 cout（地址待定）
```

> 💡 这里不讲汇编语法，但要知道：你的 C++ 代码经过编译器翻译后，**直接变成了 CPU 指令**，没有运行时解释器——这就是 C/C++ 快的原因。

---

## 四、汇编为机器码 — 生成二进制

```bash
g++ -c hello.s -o hello.o
```

- `-c`：汇编完就停，**不链接**
- `hello.o` 是二进制文件（ELF 格式）

```bash
file hello.o
# 输出：ELF 64-bit LSB relocatable, x86-64, ...
```

**重点——relocatable（可重定位）：**

你的 `movl`、`leave`、`ret` 已经变成二进制了。但 `call _ZNSolsEi@PLT`（调用 `cout`）还空着——因为这个函数在标准库里，**地址还没确定**。

---

## 五、链接 — 填坑

```bash
g++ hello.o -o hello
```

链接器的作用：**把 .o 文件里空着的函数地址，从标准库中找到并填上。**

```bash
./hello
# 输出：42
```

---

## 六、链接有什么用？（多文件编译演示）

当你的项目有多个文件时，链接的优势就体现出来了。

### 准备两个文件

```cpp
// main.cpp
#include <iostream>
void greet();  // 声明 greet 在另一个文件

int main() {
    std::cout << "main: 调用 greet 之前" << std::endl;
    greet();
    return 0;
}
```

```cpp
// greet.cpp
#include <iostream>
void greet() {
    long long sum = 0;
    for (int i = 0; i < 100000000; i++) { sum += i; }
    std::cout << "greet: 计算完毕, sum = " << sum << std::endl;
}
```

### 分步编译 + 链接

```bash
# 1. 分别编译成 .o
g++ -c main.cpp -o main.o
g++ -c greet.cpp -o greet.o

# 2. 链接两个 .o 成可执行文件
g++ main.o greet.o -o program

# 3. 运行
./program
```

### 修改 greet.cpp 后

```bash
# 只重新编译改过的 greet.cpp
g++ -c greet.cpp -o greet.o

# main.o 没变，不用重编，直接重新链接
g++ main.o greet.o -o program

# 运行
./program
```

> 💡 如果 greet.cpp 有 10 万行而 main.cpp 只有 10 行，你改 main.cpp 只需重编 main.o（10 行），不用动 greet.o（10 万行）。这就是 Makefile / CMake 的核心思想：**增量编译。**

---

## 七、动手实验

### 实验 1：改汇编，改输出

**目标：** 修改编译后的汇编代码，观察输出变化。

```bash
# 1. 打开 hello.s
vim hello.s   # 或者用 VS Code 打开

# 2. 找到这行：
#    movl	$42, -4(%rbp)
#    改成：
#    movl	$100, -4(%rbp)

# 3. 从汇编开始重新编译
g++ -c hello.s -o hello.o
g++ hello.o -o hello

# 4. 运行
./hello
# 输出：100
```

**结论：** 你跳过了预处理和编译阶段，直接改了编译器生成的汇编——绕过了 C++ 语法检查。但这也说明，**你能直接操控 CPU 要执行的指令。**

---

### 实验 2：Linux 编译的程序能在 Windows 跑吗？

**目标：** 验证"编译后的二进制"是否跨平台。

```bash
# 1. 在 WSL 中查看编译产物
cd your_path/Week1/DAY1
file hello
# 输出：hello: ELF 64-bit LSB pie executable, ... for GNU/Linux 3.2.0, not stripped
#       ^^^                                                ^^^^^^^^^^^^
#       Linux 格式                                            标记了 Linux

# 2. 打开 Git Bash（不进 WSL），切到同一目录
cd C:/Users/shiko/Desktop/North-star-of-CS/C++/Week1/DAY1
./hello
```

**结果：**
```
❌ 不能运行
—— hello 是 ELF 格式（Linux 原生），
   Windows 不认识这种文件格式。
```

**结论：** C++ 是"一次编写，到处编译"——不是"一个二进制到处跑"。你需要为每个平台分别编译一次。

---

### 实验 3：Windows 能编译 Linux 的汇编吗？

**目标：** 看看汇编语言是不是通用的。

```bash
# 1. 在 Git Bash 中确认有 hello.s（WSL 生成的）
cd C:/Users/shiko/Desktop/North-star-of-CS/C++/Week1/DAY1
ls hello.s

# 2. 用 MinGW 的 g++ 尝试编译
g++ hello.s -o hello_win.exe
```

**结果：**
```
hello.s: Error: bad register name `%rbp'
hello.s: Error: bad register name `%rsp'
hello.s: Error: no such instruction: `endbr64'
```

**原因：**
- WSL 的 g++ 是 **64 位 Linux** → 生成 64 位汇编（`%rbp`、`%rsp`、`endbr64`）
- MinGW 的 g++ **（6.3.0）** 默认 **32 位** → 不认识 64 位寄存器

**结论：** 汇编语言看起来差不多，但**不同平台的指令集和格式不同。**
- WSL 编的 `.s` → MinGW 编不了
- MinGW 编的 `.s` → WSL 也编不了（你可以试试反过来）

---

## 八、平台相关性总结

| 阶段 | 文件 | 平台相关？ |
|:----|:----|:---------|
| 源代码 | `.cpp` | ❌ 不相关（一份代码到处编） |
| 预处理 | `.i` | ❌ 不相关 |
| 编译 | `.s`（汇编） | ✅ **相关**（Linux vs Windows 指令不同） |
| 汇编 | `.o` | ✅ **相关**（ELF vs COFF 格式不同） |
| 链接 | 可执行文件 | ✅ **相关**（操作系统不同） |

---

## 九、Day 1 的核心收获

1. ✅ 知道 `.cpp → .i → .s → .o → exe` 的完整流水线
2. ✅ 理解 `#include` = 复制粘贴头文件
3. ✅ 知道 C++ 没有"运行时解释"的开销
4. ✅ 理解为什么 C++ 快：**代码直接变成 CPU 指令**
5. ✅ 理解为什么多文件项目需要"分步编译 + 链接"
6. ✅ 理解"一次编写，到处编译"≠"一个二进制到处跑"

---

## 下一步

**Day 2 → 内存布局：堆 / 栈 / 代码段**
