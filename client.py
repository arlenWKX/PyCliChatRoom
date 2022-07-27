import socket
import threading
import json
from cmd import Cmd
from os import getcwd, system
from time import sleep

ids = []
id_of = {}
name_of = {}


class Client(Cmd):
    """
    客户端
    """
    prompt = getcwd()+'>'
    use_rawinput = False
    intro = '[Welcome] 简易聊天室客户端(Cli版)\n' + '[Welcome] 输入help来获取帮助\n' + \
        '[Welcome] 本程序伪装为CMD，请不时cls一下\n'

    def __init__(self):
        """
        构造
        """
        super().__init__()
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__id = None
        self.__nickname = None
        self.__isLogin = False

    def __receive_message_function(self):
        """
        接受消息线程
        """
        while self.__isLogin:
            try:
                buffer = self.__socket.recv(1024).decode()
                obj = json.loads(buffer)
                if obj['type'] == 0:
                    print('\n[' + str(obj['sender_nickname']) + '(' + str(obj['sender_id']
                                                                          ) + ')' + '] ' + obj['message'] + '\n' + self.prompt, end='')
                elif obj['type'] == 1:
                    user_name = obj['message'].split(' ')[0]
                    user_id = int(obj['message'].split(' ')[1])
                    ids.append(user_id)
                    id_of[user_name] = user_id
                    name_of[user_id] = user_name
                    print('\n[System(0)] 用户' + user_name + '(' +
                          str(user_id) + ') 加入了聊天室 ' + '\n' + self.prompt, end='')
                elif obj['type'] == 2:
                    user_name = obj['message'].split(' ')[0]
                    user_id = int(obj['message'].split(' ')[1])
                    ids.remove(user_id)
                    id_of.pop(user_name)
                    name_of.pop(user_id)
                    print('\n[System(0)] 用户' + user_name + '(' +
                          str(user_id) + ') 退出了聊天室 ' + '\n' + self.prompt, end='')

            except Exception as e:
                print('[Client] 无法从服务器获取数据', e)

    def __send_message_thread(self, message, recv_id=None):
        """
        发送消息线程
        :param message: 消息内容
        """
        if recv_id == None:
            self.__socket.send(json.dumps({
                'type': 'broadcast',
                'sender_id': self.__id,
                'message': message
            }).encode())
        else:
            self.__socket.send(json.dumps({
                'type': 'p2p',
                'sender_id': self.__id,
                'message': message,
                'recv_id': recv_id
            }).encode())

    def start(self):
        """
        启动客户端
        """
        self.__ip_addr = '127.0.0.1'
        self.__port = 8888
        self.cmdloop()

    def default(self, args):
        system(args)

    def connect_to_server(self):
        try:
            self.__socket.connect((self.__ip_addr, self.__port))
        except Exception as e:
            print(f'[Client] 无法连接到{self.__ip_addr}:{self.__port}:', e)
            return False

        return True

    def do_switchserver(self, args):
        """
        切换聊天室
        :param args: 参数
        """
        self.__ip_addr = args.split(' ')[0]
        self.__port = 8888
        if len(args.split(' ')) > 1:
            self.__port = args.split(' ')[1]

    def do_login(self, args):
        """
        登录聊天室
        :param args: 参数
        """
        if self.__id != None:
            print('[Client] 您已登录')
            return
        print('[Client] 连接到服务器……')
        res = self.connect_to_server()
        if res != True:
            return
        nickname = args.split(' ')[0]
        print('[Client] 登录中……')
        # 将昵称发送给服务器，获取用户id
        self.__socket.send(json.dumps({
            'type': 'login',
            'nickname': nickname
        }).encode())
        # 尝试接受数据
        try:
            buffer = self.__socket.recv(1024).decode()
            obj = json.loads(buffer)
            if obj['id']:
                self.__nickname = nickname
                self.__id = obj['id']
                self.__isLogin = True
                print('[Client] 成功登录到聊天室')
                # 开启子线程用于接受数据
                self.__receive_message_thread = threading.Thread(
                    target=self.__receive_message_function, daemon=True)
                self.__receive_message_thread.start()
            else:
                print('[Client] 无法登录到聊天室')
        except Exception as e:
            print('[Client] 无法从服务器获取数据', e)

    def do_send(self, args):
        """
        发送消息
        :param args: 参数
        """
        if self.__id == None:
            print('[Client] 您还未登录')
            return
        message = args
        # 显示自己发送的消息
        print('[' + str(self.__nickname) +
              '(' + str(self.__id) + ')' + ']', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(
            target=self.__send_message_thread, args=(message,), daemon=True)
        thread.start()

    # def do_sendto(self, args):
    #     """
    #     单发消息
    #     :param args: 参数
    #     """
    #     if self.__id == None:
    #         print('[Client] 您还未登录')
    #         return

    #     recv_id = 0
    #     recv_name = ''

    #     if args.split(' ')[0] == 'id':
    #         recv_id = int(args.split(' ')[1])
    #         print('recvid', recv_id )
    #         if recv_id not in ids:
    #             print('[Client] 未找到用户')
    #             return
    #         recv_name = name_of [ recv_id ]
    #     elif args.split(' ')[0] == 'name':
    #         if not args.split(' ')[1] in id_of:
    #             print('[Client] 未找到用户')
    #             return
    #         recv_id = id_of[args.split(' ')[2]]
    #         recv_name = args.split(' ')[1]

    #     # 显示自己发送的消息
    #     print('[' + str(self.__nickname) + '(' + str(self.__id) + ')' + '] 对 ' + recv_name + '(' + str(recv_id) + ') 悄悄说' + message)
    #     # 开启子线程用于发送数据
    #     thread = threading.Thread(target=self.__send_message_thread, args=(message, recv_id),daemon=True)
    #     thread.start()

    def do_logout(self, args=None):
        """
        登出
        :param args: 参数
        """
        print('[Client] 登出中……')
        if self.__id == None:
            print('[Client] 您还未登录')
            return
        self.__socket.send(json.dumps({
            'type': 'logout',
            'sender_id': self.__id
        }).encode())
        self.__isLogin = False
        self.__receive_message_thread.join()
        self.__socket.close()
        self.__id = None
        self.__nickname = None
        print('[Client] 已登出')

    def do_exit(self, args=None):
        """
        安全退出
        :param args: 参数
        """
        if args == None or args != None and args != '/?':
            self.do_logout(self)
            return True
        else:
            system('exit ' + args)

    def do_help(self, arg):
        """
        帮助
        :param arg: 参数
        """
        command = arg.split(' ')[0]
        if command == 'all':
            print('[Help] connect ipaddress (port) - 连接到服务器，ipaddress是服务器的IP地址，port是端口')
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
            print('[Help] send message - 发送消息，message是你输入的消息')
            print('[Help] logout - 退出聊天室')
        elif command == 'login':
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
        elif command == 'send':
            print('[Help] send message - 发送消息，message是你输入的消息')
        elif command == 'logout':
            print('[Help] logout - 退出聊天室')
        elif command == 'switchserver':
            print(
                '[Help] switchserver ipaddress (port) - 切换到服务器，ipaddress是服务器的IP地址，port是端口')
        else:
            system('help ' + arg)


client = Client()
client.start()
