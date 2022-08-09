import socket
import threading
import json
import os
from cmd import Cmd
import sys
import re
from time import sleep

ids = []
id_of = {}
name_of = {}

version='1.0.0'

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

class ProgressBar(object):
    DEFAULT = 'Progress: %(bar)s %(percent)3d%% '
    FULL = '%(bar)s %(current)d/%(total)d (%(percent)3d%%) %(remaining)d to go'

    def __init__(self, total, width=40, fmt=DEFAULT, symbol='=',
                 output=sys.stderr):
        assert len(symbol) == 1

        self.total = total
        self.width = width
        self.symbol = symbol
        self.output = output
        self.fmt = re.sub(r'(?P<name>%\(.+?\))d',
            r'\g<name>%dd' % len(str(total)), fmt)

        self.current = 0

    def __call__(self):
        percent = self.current / float(self.total)
        size = int(self.width * percent)
        remaining = self.total - self.current
        if self.current!=self.total:
            bar = '[' + self.symbol * size + '>' + ' ' * (self.width - size) + ']'
        else:
            bar = '[' + self.symbol * size + ']'

        args = {
            'total': self.total,
            'bar': bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining
        }
        print('\r' + self.fmt % args, file=self.output, end='')

    def done(self):
        self.current = self.total
        self()
        print('', file=self.output)

class Client(Cmd):
    """
    客户端
    """
    prompt = os.getcwd()+'>'
    use_rawinput = False
    intro = '[Welcome] 欢迎来到Python命令行聊天室客户端\n' + '[Welcome] 输入help all来获取帮助\n'


    def __init__(self):
        """
        构造
        """
        super().__init__()
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
                output = ''
                if obj['type'] == 0:
                    output = '[' + str(obj['sender_nickname']) + '(' + str(obj['sender_id']) + ')' + '] ' + obj['message']
                elif obj['type'] == 1:
                    user_name = obj['message'].split(' ')[0]
                    user_id = int(obj['message'].split(' ')[1])
                    ids.append(user_id)
                    id_of[user_name] = user_id
                    name_of[user_id] = user_name
                    output = '[System(0)] 用户' + user_name + '(' + str(user_id) + ') 加入了聊天室'
                elif obj['type'] == 2:
                    user_name = obj['message'].split(' ')[0]
                    user_id = int(obj['message'].split(' ')[1])
                    ids.remove(user_id)
                    id_of.pop(user_name)
                    name_of.pop(user_id)
                    output = '[System(0)] 用户' + user_name + '(' + str(user_id) + ') 退出了聊天室'
                
                print ( '\n' + output + '\n' + self.prompt, end='' )

            except Exception as e:
                print('[Client] 无法从服务器获取数据', e)
                break


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
                'type': 'single',
                'sender_id': self.__id,
                'message': message,
                'recv_id': recv_id
            }).encode())

    def start(self):
        """
        启动客户端
        """
        self.__ip_addr = self.__port = None
        self.cmdloop()


    def default(self, args):
        os.system(args)

    def do_userlist(self, args):
        """
        输出在线用户列表
        """
        if self.__isLogin:
            for id in ids:
                print(name_of[id]+' '+str(id))
        else:
            print ( '[Client] 您还未登陆' )

    def connect_to_server(self):
        """
        连接到服务器
        """
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__socket.connect((self.__ip_addr, self.__port))
        except Exception as e:
            print(f'[Client] 无法连接到{self.__ip_addr}:{self.__port}:', e)
            return False
        return True

    def testserver(self, ip, port):
        """
        测试服务器
        :param ip: 服务器IP
        :param port: 服务器端口
        """
        tsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tsocket.settimeout(1)
        if ip == 'local':
            ip = '127.0.0.1'
        print(f'[Client] 测试服务器{ip}:{port}')
        print('[Client] 测试连接中……')
        try:
            tsocket.connect((ip, port))
        except Exception as e:
            print(f'[Client] 无法连接至服务器:', e)
            tsocket.close()
            return False
        
        print('[Client] 测试数据传输与版本中中……')
        tsocket.send(json.dumps({
            'type': 'test_connect',
            'version': version,
            'message': 'azAZ09+-*/_'
        }).encode())
        try:
            buffer = tsocket.recv(1024).decode()
            obj = json.loads(buffer)
        except Exception as e:
            print('[Client] 服务器错误')
            tsocket.close()
            return False
        if obj['message'] == 'ok':
            print('[Client] OK')
            tsocket.close()
            return True
        elif obj['version'] != version:
            print('[Client] 服务器版本不匹配')
            tsocket.close()
            return False
        else:
            print('[Client] 网络不稳定')
            tsocket.close()
            return False

    def scan_func(self,ip,port,lst):
        """
        扫描服务器线程
        :param ip: 服务器IP
        :param port: 服务器端口
        :param lst: 返回结果的列表
        """
        if self.testserver(ip, port):
            lst.append(ip)
        return

    def do_server(self, args):
        """
        切换服务器或在局域网内扫描
        :param args: 参数
        """
        args=args.split(' ')

        if args[0]=="search":
            port = 8888
            if len(args) > 1:
                port=int(args[1])
            print(f'[Client] 在局域网中扫描端口为{port}的服务器……')

            ip_prefix=socket.gethostbyname(socket.gethostname())
            for i in range(len(ip_prefix)-1,-1,-1):
                if ip_prefix[i] == '.':
                    ip_prefix=ip_prefix[0:i+1]
                    break
            ips = ['local']
            with os.popen("arp.exe -a") as res:
                for line in res:
                    line = line.strip()
                    if line and line.startswith(ip_prefix):
                        ips.append(line.split()[0])

            progress = ProgressBar(len(ips)*2+8, 30, fmt=ProgressBar.DEFAULT)
            servs = []
            scan_thread=[]
            save_stdout = sys.stdout
            sys.stdout = DummyFile()
            for ip in ips:
                scan_thread.append( threading.Thread(target=self.scan_func, args=(ip,port,servs)))
                progress.current += 1
                progress()
                sleep(0.01)
            if len ( ips ) >= 8:
                for i in range(0,8):
                    scan_thread[i].start()
                    progress.current += 1
                    progress()
                    sleep(0.01)
                for i in range(0,len(scan_thread)-8):
                    progress.current += 1
                    progress()
                    scan_thread[i].join()
                    scan_thread[i+8].start()
                    sleep(0.01)
                for i in range(len(scan_thread)-8,len(scan_thread)):
                    scan_thread[i].join()
                    progress.current += 1
                    progress()
                    sleep(0.01)
            else:
                for i in scan_thread:
                    i.start()
                    progress.current += 1
                    i.join()
                    progress.current += 1
                    progress()
                    sleep(0.01)            
            sys.stdout = save_stdout
            print('')
            if len(servs) > 0:
                for i in servs:
                    print(f"[Client] 发现服务器：{i}:{port}")
            else:
                print('[Client] 未发现服务器')
            return

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if args[0] == 'local':
            self.__ip_addr = '127.0.0.1'
            self.__port = 8888
        else:
            self.__ip_addr = args[0]
            self.__port = 8888
            if len(args) > 1:
                self.__port = int(args[1])
        print(f'[Client] 切换服务器到{self.__ip_addr}:{self.__port}')
        if not self.testserver(self.__ip_addr, self.__port):
            self.__ip_addr = self.__port = None


    def do_login(self, args):
        """
        登录聊天室
        :param args: 参数
        """
        if self.__id != None:
            print('[Client] 您已登录')
            return
        if self.__ip_addr == None:
            print('[Client] 请先选择服务器')
            return
        print('[Client] 连接到服务器……')
        res = self.connect_to_server()
        if res != True:
            return
        nickname = args.split(' ')[0]
        if ( nickname.isdigit ( ) ):
            print('[Client] 用户名不能为数字')
            return
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
                lst=obj['userlist'].split('\n')
                #print(lst)
                for i in range(0,len(lst)):
                    #print(i)
                    if lst[i] != '' and i != self.__id:
                        ids.append(i)
                        id_of[lst[i]] = i
                        name_of[i] = lst[i]
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

    def do_sendto(self, args):
        """
        单发消息
        :param args: 参数
        """
        if self.__id == None:
            print('[Client] 您还未登录')
            return

        argss = args.split(' ')

        if len(argss) < 2:
            print ( '[Client] 请输入发送对象和消息' )
            return

        recvs=argss[0].split(',')
        message=args[len(argss[0])+1:]

        for x in recvs:
            if x.isdigit():
                if int(x) in ids:
                    thread = threading.Thread(
                        target=self.__send_message_thread, args=(self.__nickname + '(' + str(self.__id) + ') 对你说' + message,int(x)), daemon=True)
                    thread.start()
                else:
                    recvs.remove ( x )
            else:
                if x in id_of.keys ( ):
                    thread = threading.Thread(
                        target=self.__send_message_thread, args=(self.__nickname + '(' + str(self.__id) + ') 对你说' + message,id_of[x]), daemon=True)
                    thread.start()
                else:
                    recvs.remove ( x )

        # 显示自己发送的消息
        print('[' + str(self.__nickname) + '(' + str(self.__id) + ')' + '] 对 ' + ",".join(map(str,recvs)) + ' 说' + message)
        # 开启子线程用于发送数据

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
        ids.clear()
        id_of.clear()
        name_of.clear()
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
            os.system('exit ' + args)

    def do_help(self, arg):
        """
        帮助
        :param arg: 参数
        """

        help_str = {
            'help'    : 'help    <command> | all 查看该命令的帮助或查看所有帮助',
            'server'  : 'server  <host> [<port>] 切换到服务器，会自动测试网络\n'+
                        '        search [<port>] 搜索局域网上所有服务器（默认端口：8888）',
            'login'   : 'login   <nickname>      登录到服务器',
            'send'    : 'send    <message>       群发消息',
            'sendto'  : 'sendto  <users> <msg>   向users发送消息，可以是用户id或用户名，用逗号分隔',
            'userlist': 'userlist                输出所有在线用户',
            'logout'  : 'logout                  登出',
            'exit'    : 'exit                    登出并退出程序\n' + 
                        '   Warning：直接关闭可能会导致不可预料的结果'
        }

        command = arg.split(' ')[0]
        if command == 'all':
            for i in help_str:
                print ( i )
        elif command in help_str.keys:
            print ( '[Help] ' + help_str [ command ] )
        else:
            os.system('help ' + arg)

client = Client()
client.start()
