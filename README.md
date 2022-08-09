<div align="center">
    <h1>PyCliChatRoom</h1>
    <h6>一个 Python Socket 实现的纯命令行聊天室</h6>
    <h6>修改自<a href='https://github.com/FlyAndNotDown/ChatRoom'>FlyAndNotDown/ChatRoom</a></h6>
</div>

# 特性
* 与命令行集成，CLI交互
* 仅依赖自带的基本库，开箱即用
* 可自动搜索局域网上的服务器
* 自带网络检测
* 群发和私聊
* ……

# 运行需求
* Python 3+
* 没有了

# 运行方法
进入项目根目录，执行命令：
```shell
python3 ./server.py
```
来启动服务端，执行命令：
```shell
python3 ./client.py
```
来启动客户端

# 使用方法
```
help    <command> | all 查看该命令的帮助或查看所有帮助
server  <host> [<port>] 切换到服务器（默认端口：8888）
        search [<port>] 搜索局域网上所有服务器（默认端口：8888）
login   <nickname>      登录到服务器
send    <message>       群发消息
sendto  <users> <msg>   [实验功能!] 向users发送消息，可以是用户id或用户名，用逗号分隔
userlist                [实验功能!] 输出所有在线用户
logout                  登出
```
