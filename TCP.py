import socket

def start_server(host='8.137.81.229', port=8000):
    # 创建一个TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 绑定socket到地址和端口
    server_socket.bind((host, port))
    
    # 启动监听
    server_socket.listen(5)
    print(f"Server started at {host}:{port}")
    
    while True:
        # 等待连接
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")
        
        # 处理连接
        handle_client(client_socket)

def handle_client(client_socket):
    try:
        while True:
            # 接收数据
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Received: {data.decode()}")
            
            # 发送响应
            response = b"Data received"
            client_socket.sendall(response)
    finally:
        # 关闭连接
        client_socket.close()
        print("Connection closed")

if __name__ == "__main__":
    start_server()
