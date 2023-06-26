# one_line.py

把你的python程序变成一行（有可能正确的）代码

## 使用方式

python one_line.py [source_file_name]

可以使用 python one_line.py one_line.py套娃生成只有一行代码的one_line.py（one_line_py_in_one_line.py）

## 暂时不支持的代码

1. while，try，break，continue，match 等语句

2. 部分复杂的赋值语句。

    例如 (a,b) , (c,d) = (1,2), (3,4)，暂时需要分开写成 

    ``` python
    x,y = (1,2),(3,4)
    (a,b) = x
    (c,d) = y
    ```
3. for循环或者函数体内对外部变量直接赋值
    例如下面的代码
    ``` python
    s = 0
    for i in range(100):
        s = s + i
    print(s)
    ```
    需要改写为
    ``` python
    class Context():
        def __init__(self):
            self.s = 0
    ctx = Context()
    for i in range(100):
        ctx.s = ctx.s + i
    print(ctx.s)
    ```

4. 使用非__init__方法初始化类的属性