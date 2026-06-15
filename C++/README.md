# C++ 学习路线（AI Infra 方向）

> **定位：** 每天 1 小时，70% Python 后端 + 30% C++ 打底
> **最终目标：** AI Infra — 推理加速 / 模型部署 / 推理框架源码理解

---

## 一、目标 / Goal

能看懂推理框架（vLLM、llama.cpp、TensorRT-LLM）的 C++ 核心逻辑，理解底层原理：

- 内存布局 & 指针 → 理解显存管理、KVCache
- 编译 & 链接 → 理解算子编译、CUDA 代码编译流程
- STL & 数据结构 → 理解框架中的数据结构设计
- 性能意识 → Cache 友好、零拷贝、连续内存

---

## 二、当前情况 / Current Status

| 项目 | 情况 |
|:----|:----|
| Python 后端 | ✅ FastAPI + MySQL + Redis + Docker 项目经验 |
| C++ 基础 | ❌ 零基础 |
| 编程经验 | 了解变量/循环/函数等通用概念 |
| 学习时间 | 每天 ≈1 小时，不赶进度 |

---

## 三、规划 / Roadmap

### 阶段一：语法基础（2 周）

```
Day 1    环境搭建（推荐 WSL2 + g++） + Hello World + 编译流程
Day 2-3  基本语法：变量/循环/函数/输入输出（和 Python 对比学）
Day 4-6  指针 & 引用 ← 最核心，画图理解
Day 7-9  class & 对象 + 构造/析构（理解生命周期）
Day 10   运算符重载（浅尝辄止）
Day 11-12  const / static / 命名空间
Day 13-14 复盘 + 小练习
```

### 阶段二：STL — 标准模板库（1 周）

```
vector          ← Python list 的底层实现
string          ← 字符串操作
unordered_map   ← Python dict（哈希表实现）
map             ← 红黑树，有序字典
unordered_set / set
stack / queue / deque
algorithm 库    ← sort / lower_bound / max_element
```

**重点：** 理解每个容器的**内存布局**和**时间复杂度**，这是 AI infra 性能分析的基础。

### 阶段三：LeetCode 刷题（长期）

策略：同一道题，Python 过 → C++ 再过一遍

- Easy：熟悉 STL API + 指针操作
- Medium：锻炼算法思维 + 边界处理
- 不强行追求 Hard，重点是每种数据结构都会 C++ 版本

### 阶段四：进阶（实习 / 大二后可选）

```
智能指针 (unique_ptr / shared_ptr)   ← 理解资源管理
多线程 (thread / mutex / atomic)     ← 推理框架中的并发
RAII 设计模式                          ← C++ 独有，Python 没有
移动语义 & 完美转发                    ← 性能关键
CUDA C++ 基础                          ← 推理加速核心
```

---

## 四、学习资源

| 资源 | 用途 | 链接 |
|:----|:----|:----|
| LearnCPP | 零基础教程 | https://www.learncpp.com/ |
| cppreference | API 查询 | https://en.cppreference.com/ |
| LeetCode | 刷题 | https://leetcode.com/ |
| 《Effective Modern C++》 | 进阶 | Scott Meyers |

---

## 五、给未来对话的提示词

```
我是大一 CS 学生，Python 基础不错（FastAPI + MySQL + Redis + Docker 项目经验），
最终目标是 AI Infra（推理加速 / 模型部署）。

C++ 对我来说不是刷题工具，而是理解推理框架（vLLM、llama.cpp）底层的基础。
学 C++ 时请多讲性能、内存、编译相关知识，少讲纯语法糖。

当前规划：
  阶段一（2周）— 语法 + 指针/引用 + 内存布局
  阶段二（1周）— STL，重点理解内存连续性和 cache 友好
  阶段三（长期）— LeetCode 刷题 + 看框架源码

今天第一天任务：
  1. 推荐 Windows 上 C++ 开发环境（WSL2 / MSYS2 / MinGW？为什么？）
  2. Hello World + g++ 编译流程
  3. 编译流程和 python xxx.py 有什么本质区别

教学风格：
  - 每个概念先和 Python 对比
  - 指针/内存相关画图解释
  - 给我代码让我自己敲，别替我写
  - 每天 1 小时内容，不贪多
```

---

## 六、总原则

1. **不赶进度** — C++ 学得慢是正常的，指针卡一周都正常
2. **STL 是第一生产力** — 不要手写红黑树，会用就行
3. **C++ 让 Python 更好** — 理解了底层，写 Python 时才会知道为什么有的写法快、有的慢
4. **70/30 不破** — 主力还是 Python 后端，C++ 是内力，不是主业

> C++ 是 AI Infra 的地基，现在每天挖一点，毕业时就能盖楼。
