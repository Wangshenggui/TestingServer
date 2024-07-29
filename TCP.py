import asyncio
import websockets
from websockets import ConnectionClosed
import json
import threading

# 用于跟踪已连接的 TCP 客户端的列表
connected_clients = []
# WebSocket 连接实例
websocket_connection = None
# 发送心跳消息的间隔时间
heartbeat_interval = 0.9  # 设置心跳包发送间隔为1秒

# 全局变量，用于存储从 TCP 客户端接收到的数据
global_data = None
# 全局变量，用于存储包含 "lon" 的消息
lon_message = None

mutex = threading.Lock()  # 创建一个锁

# 处理 TCP 客户端连接
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"客户端 {addr} 连接成功")

    # 将新客户端添加到已连接客户端列表
    connected_clients.append(writer)

    try:
        while True:
            # 从 TCP 客户端读取数据
            data = await reader.read(100)
            if not data:
                break

            global global_data
            global_data = data.decode()  # 将接收到的数据存储到全局变量中
            message = global_data
            print(f"收到来自客户端 {addr} 的消息: {message}")

            # 发送消息到 WebSocket 服务器
            await send_message_to_websocket(message)

            await writer.drain()
    except (ConnectionResetError, ConnectionError) as e:
        print(f"客户端 {addr} 连接错误: {e}")
    except Exception as e:
        print(f"处理客户端 {addr} 消息时发生错误: {e}")
    finally:
        # 从列表中移除客户端并关闭连接
        if writer in connected_clients:
            connected_clients.remove(writer)
        print(f"客户端 {addr} 断开连接")
        writer.close()

# 向所有已连接的 TCP 客户端广播消息
async def broadcast_message_tcp(message):
    for client_writer in connected_clients:
        try:
            print(f"向 TCP 客户端发送消息: {message}")
            client_writer.write(message.encode())
            await client_writer.drain()
        except (ConnectionResetError, ConnectionError) as e:
            print(f"向 TCP 客户端发送消息时发生连接错误: {e}")
            if client_writer in connected_clients:
                connected_clients.remove(client_writer)
            client_writer.close()
        except Exception as e:
            print(f"向 TCP 客户端发送消息时发生错误: {e}")

# 发送消息到 WebSocket 服务器
async def send_message_to_websocket(message):
    if websocket_connection:
        try:
            print(f"发送消息到 WebSocket 服务器: {message}")
            await websocket_connection.send(message)
        except Exception as e:
            print(f"发送消息到 WebSocket 服务器时发生错误: {e}")

# 处理从 WebSocket 服务器接收到的消息
async def handle_websocket_message(message):
    #print(f"收到来自 WebSocket 服务器的消息: {message}")
    try:
        json_message = json.loads(message)
        # 检查消息中是否包含特定键，如果包含则广播到 TCP 客户端
        if "n1" in json_message or "lte" in json_message or "rtk" in json_message:
            # 使用 with 语句自动获取和释放锁
            with mutex:
                await broadcast_message_tcp(message)
        # 如果消息中包含 "lon" 键，保存消息到全局变量
        elif "lon" in json_message:
            global lon_message
            lon_message = message
    except json.JSONDecodeError as e:
        print(f"解析 WebSocket 消息时发生错误: {e}")

# WebSocket 客户端连接和消息处理
async def websocket_client():
    global websocket_connection
    uri = "ws://8.137.81.229:8000"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                websocket_connection = websocket
                while True:
                    message = await websocket.recv()
                    await handle_websocket_message(message)
        except (ConnectionClosed, ConnectionResetError, ConnectionError) as e:
            print(f"WebSocket 连接错误: {e}")
            websocket_connection = None
            await asyncio.sleep(5)  # 等待几秒钟再尝试重新连接

# 向所有已连接的 TCP 客户端发送心跳消息
async def send_heartbeat():
    global global_data
    global lon_message
    while True:
        await asyncio.sleep(heartbeat_interval)
        message = global_data if global_data is not None else "s"  # 使用全局数据或默认值
        print(f"发送心跳包: {message}")
        await broadcast_message_tcp(message)
        #await asyncio.sleep(0.1)
        #await broadcast_message_tcp(lon_message)

# 主函数，启动 TCP 服务器和其他任务
async def main():
    server = await asyncio.start_server(
        handle_client, '172.29.103.118', 8881)

    addr = server.sockets[0].getsockname()
    print(f"服务器已启动，监听在 {addr}")

    # 启动 WebSocket 客户端和心跳任务
    asyncio.create_task(websocket_client())
    asyncio.create_task(send_heartbeat())

    # 运行 TCP 服务器
    async with server:
        await server.serve_forever()

# 运行主函数
asyncio.run(main())
