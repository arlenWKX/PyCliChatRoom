<div align="center">
    <h1>PyCliChatRoom</h1>
    <h6>一个 Python Socket 实现的纯命令行聊天室</h6>
    <h6>修改自<a href='https://github.com/FlyAndNotDown/ChatRoom'>FlyAndNotDown/ChatRoom</a></h6>
</div>

# 特性
* 纯命令行实现
* 仅依赖基本库 `socket` 、 `threading` 、 `json` 、 `cmd` 、 `os` ，开箱即用
* 伪装为命令提示符
* ……

# 运行需求
* Python 3+
* 在Windows上更能体现特*特性*

# 运行方法
进入项目根目录，执行命令：
```shell
python3 ./server.py
```
来启动服务端，执行命令：
```shell
python3 ./clien.py
```
来启动客户端

**注意：一台电脑上一次只能启动一个服务端，但可以启动多个客户端**