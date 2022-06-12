import socket
import threading
import json


class Server:
    """
    服务器类
    """

    def __init__(self):
        """
        构造
        """
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__connections = list()
        self.__nicknames = list()

    def __user_thread(self, user_id):
        """
        用户子线程
        :param user_id: 用户id
        """
        connection = self.__connections[user_id]
        nickname = self.__nicknames[user_id]
        print('[Server] 用户', user_id, nickname, '加入聊天室')
        self.__broadcast(user_id=0, message=str(nickname)+' '+str(user_id), type=1)

        # 侦听
        while True:
            # noinspection PyBroadException
            try:
                buffer = connection.recv(1024).decode()
                # 解析成json数据
                obj = json.loads(buffer)
                if obj['type'] == 'broadcast':
                    self.__broadcast(user_id=obj['sender_id'], type=0, message=obj['message'])
                elif obj['type'] == 'logout':
                    print('[Server] 用户', user_id, nickname, '退出聊天室')
                    self.__broadcast(user_id=0, message=str(nickname)+' '+str(user_id), type=2)
                    self.__connections[user_id] = None
                    break
                elif obj['type'] == 'exit':
                    self.__nicknames.pop(user_id)
                    self.__connections[user_id] = None
                    break
                else:
                    print('[Server] 无法解析json数据包:', connection.getsockname(), connection.fileno())
            except Exception as e:
                print('[Server] 连接失效:', connection.getsockname(), connection.fileno(), e)
                break

    # def __send2p(self, client_id, user_id=0, message=''):
    #     """
    #     单发
    #     :param client_id: 接受消息的客户端id
    #     :param user_id: 用户id(0为系统)
    #     :param message: 广播内容
    #     """
    #     for i in range(1, len(self.__connections)):
    #         if client_id == i and self.__connections[i]:
    #             self.__connections[i].send(json.dumps({
    #                 'sender_id': user_id,
    #                 'sender_nickname': self.__nicknames[user_id],
    #                 'message': message
    #             }).encode())

    def __broadcast(self, user_id=0, type=0, message=''):
        """
        广播
        :param user_id: 用户id(0为系统)
        :param message: 广播内容
        """
        for i in range(1, len(self.__connections)):
            if user_id != i and self.__connections[i]:
                self.__connections[i].send(json.dumps({
                    'type': type,
                    'sender_id': user_id,
                    'sender_nickname': self.__nicknames[user_id],
                    'message': message
                }).encode())

    def __waitForLogin(self, connection):
        # 尝试接受数据
        # noinspection PyBroadException
        try:
            buffer = connection.recv(1024).decode()
            # 解析成json数据
            obj = json.loads(buffer)
            # 如果是连接指令，那么则返回一个新的用户编号，接收用户连接
            if obj['type'] == 'login':
                id = len(self.__connections) - 1
                if obj['nickname'] in self.__nicknames:
                    id = self.__nicknames.index(obj['nickname'])
                    self.__connections[id] = connection
                    print ( "[Server] 用户已存在 " + obj['nickname'] + '(' + str ( id ) + ')' )
                else:
                    id = id + 1
                    self.__nicknames.append(obj['nickname'])
                    self.__connections.append(connection)
                    print ( "[Server] 新增用户 " + obj['nickname'] + '(' + str ( id ) + ')' )
                connection.send(json.dumps({
                    'id': id
                }).encode())

                # 开辟一个新的线程
                thread = threading.Thread(target=self.__user_thread, args=(id,),daemon=True)
                thread.start()
            else:
                print('[Server] 无法解析json数据包:', connection.getsockname(), connection.fileno())
        except Exception as e:
            print('[Server] 无法接受数据:', connection.getsockname(), connection.fileno(), e)

    def start(self):
        """
        启动服务器
        """
        # 绑定端口
        self.__socket.bind(('0.0.0.0', 8888))
        # 启用监听
        self.__socket.listen(10)
        print('[Server] 服务器正在运行......')

        # 清空连接
        self.__connections.clear()
        self.__nicknames.clear()
        self.__connections.append(None)
        self.__nicknames.append('System')

        # 开始侦听
        while True:
            connection, address = self.__socket.accept()
            print('[Server] 收到一个新连接', connection.getsockname(), connection.fileno())

            thread = threading.Thread(target=self.__waitForLogin, args=(connection,),daemon=True)
            thread.start()


server = Server()
server.start()
