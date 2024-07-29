# -*- coding: utf-8
import socket
import threading

def connTCP():
    global tcp_client_socket
    # 创建socket
    tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # IP 和端口
    server_ip = 'bemfa.com'
    server_port = 8344
    try:
        # 连接服务器
        tcp_client_socket.connect((server_ip, server_port))
        #发送订阅指令
        substr = 'cmd=1&uid=7413cbb074d088ee0cedc516fa1d9e71&topic=test\r\n'
        tcp_client_socket.send(substr.encode("utf-8"))
    except:
        time.sleep(2)
        connTCP()

#心跳
def Ping():
    # 发送心跳
    try:
        keeplive = 'nimade'
        tcp_client_socket.send(keeplive.encode("utf-8"))
    except:
        time.sleep(2)
        connTCP()
    #开启定时，30秒发送一次心跳
    t = threading.Timer(3,Ping)
    t.start()

    
connTCP()
Ping()

while True:
    # 接收服务器发送过来的数据
    recvData = tcp_client_socket.recv(1024)
    if len(recvData) != 0:
        print('recv:', recvData.decode('utf-8'))
    else:
        print("conn err")
        connTCP()
