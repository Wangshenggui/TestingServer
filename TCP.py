import asyncio
import websockets
from websockets import ConnectionClosed
import json
import threading

# 用于跟踪已连接的 TCP 客户端的列表
connected_clients = []  # 存储已连接的TCP客户端的列表

# WebSocket 连接实例
websocket_connection = None  # 用于存储WebSocket连接

# 发送心跳消息的间隔时间
heartbeat_interval = 0.9  # 设置心跳包发送间隔为0.9秒

# 全局变量，用于存储从 TCP 客户端接收到的数据
global_data = None  # 用于存储最新的TCP客户端数据

# 全局变量，用于存储包含 "lon" 的消息
lon_message = None  # 用于存储包含"lon"键的WebSocket消息

global addr  # 全局变量，用于存储客户端地址信息

mutex = threading.Lock()  # 创建一个线程锁，用于保护全局资源

# 处理 TCP 客户端连接
async def handle_client(reader, writer):
    global addr  # 使用全局变量存储客户端地址
    addr = writer.get_extra_info('peername')  # 获取客户端地址信息
    print(f"客户端 {addr} 连接成功")  # 打印客户端连接成功的信息

    # 将新客户端添加到已连接客户端列表
    connected_clients.append(writer)  # 将新连接的客户端写入器加入列表

    try:
        while True:
            # 从 TCP 客户端读取数据
            data = await reader.read(100)  # 读取来自客户端的数据，最大读取100字节
            if not data:
                break  # 如果没有数据，断开循环

            global global_data
            global_data = data.decode()  # 将接收到的数据解码并存储到全局变量中
            message = global_data  # 设置message为全局数据
            print(f"收到来自客户端 {addr} 的消息: {message}")  # 打印接收到的消息

            # 发送消息到 WebSocket 服务器
            await send_message_to_websocket(message)  # 将消息发送到WebSocket服务器

            await writer.drain()  # 确保数据已被发送
    except (ConnectionResetError, ConnectionError) as e:
        print(f"客户端 {addr} 连接错误: {e}")  # 打印连接错误信息
    except Exception as e:
        print(f"处理客户端 {addr} 消息时发生错误: {e}")  # 打印处理消息时的错误信息
    finally:
        # 从列表中移除客户端并关闭连接
        if writer in connected_clients:
            connected_clients.remove(writer)  # 从已连接客户端列表中移除客户端
        print(f"客户端 {addr} 断开连接")  # 打印客户端断开连接的信息
        writer.close()  # 关闭客户端连接

# 向所有已连接的 TCP 客户端广播消息
async def broadcast_message_tcp(message):
    for client_writer in connected_clients:  # 遍历所有已连接的客户端
        try:
            print(f"向 TCP 客户端{addr}发送消息: {message}")  # 打印发送消息的信息
            client_writer.write(message.encode())  # 将消息编码并写入客户端
            await client_writer.drain()  # 确保数据已被发送
        except (ConnectionResetError, ConnectionError) as e:
            print(f"向 TCP 客户端{addr}发送消息时发生连接错误: {e}")  # 打印连接错误信息
            if client_writer in connected_clients:
                connected_clients.remove(client_writer)  # 从列表中移除出错的客户端
            client_writer.close()  # 关闭出错的客户端连接
        except Exception as e:
            print(f"向 TCP 客户端{addr}发送消息时发生错误: {e}")  # 打印发送消息时的其他错误信息

# 发送消息到 WebSocket 服务器
async def send_message_to_websocket(message):
    if websocket_connection:  # 检查WebSocket连接是否存在
        try:
            print(f"发送消息到 WebSocket 服务器: {message}")  # 打印发送到WebSocket服务器的消息
            await websocket_connection.send(message)  # 通过WebSocket连接发送消息
        except Exception as e:
            print(f"发送消息到 WebSocket 服务器时发生错误: {e}")  # 打印发送消息到WebSocket服务器时的错误信息

# 处理从 WebSocket 服务器接收到的消息
async def handle_websocket_message(message):
    # print(f"收到来自 WebSocket 服务器的消息: {message}")  # 打印收到的WebSocket消息
    try:
        json_message = json.loads(message)  # 尝试解析JSON消息
        # 检查消息中是否包含特定键，如果包含则广播到 TCP 客户端
        if "n1" in json_message or "lte" in json_message or "rtk" in json_message:
            # 使用 with 语句自动获取和释放锁
            with mutex:  # 使用锁来保护对全局资源的访问
                await broadcast_message_tcp(message)  # 广播消息到所有TCP客户端
        # 如果消息中包含 "lon" 键，保存消息到全局变量
        elif "lon" in json_message:
            global lon_message
            lon_message = message  # 存储包含"lon"的消息到全局变量
    except json.JSONDecodeError as e:
        print(f"解析 WebSocket 消息时发生错误: {e}")  # 打印解析JSON消息时的错误信息

# WebSocket 客户端连接和消息处理
async def websocket_client():
    global websocket_connection
    uri = "ws://8.137.81.229:8001"  # WebSocket服务器的URI
    while True:
        try:
            # 连接到WebSocket服务器
            async with websockets.connect(uri) as websocket:
                websocket_connection = websocket  # 存储WebSocket连接实例
                while True:
                    message = await websocket.recv()  # 接收来自WebSocket服务器的消息
                    await handle_websocket_message(message)  # 处理收到的WebSocket消息
        except (ConnectionClosed, ConnectionResetError, ConnectionError) as e:
            print(f"WebSocket 连接错误: {e}")  # 打印WebSocket连接错误信息
            websocket_connection = None  # 重置WebSocket连接
            await asyncio.sleep(5)  # 等待5秒后重试连接

# 向所有已连接的 TCP 客户端发送心跳消息
async def send_heartbeat():
    global global_data
    global lon_message
    while True:
        await asyncio.sleep(heartbeat_interval)  # 等待心跳间隔
        message = global_data if global_data is not None else "s"  # 使用全局数据或默认值作为心跳消息
        print(f"发送心跳包: {message}")  # 打印发送的心跳包
        await broadcast_message_tcp(message)  # 广播心跳消息到所有TCP客户端

# 主函数，启动 TCP 服务器和其他任务
async def main():
    server = await asyncio.start_server(
        handle_client, '172.29.103.118', 8000)  # 启动TCP服务器

    addr = server.sockets[0].getsockname()  # 获取服务器的监听地址
    print(f"服务器已启动，监听在 {addr}")  # 打印服务器启动信息

    # 启动 WebSocket 客户端和心跳任务
    asyncio.create_task(websocket_client())  # 创建WebSocket客户端任务
    asyncio.create_task(send_heartbeat())  # 创建心跳任务

    # 运行 TCP 服务器
    async with server:
        await server.serve_forever()  # 启动TCP服务器的无限循环

# 运行主函数
asyncio.run(main())  # 执行主函数
