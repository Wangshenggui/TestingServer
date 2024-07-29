import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"客户端 {addr} 连接成功")

    try:
        while True:
            data = await reader.read(100)  # 从客户端读取数据
            if not data:
                break  # 如果没有数据，则断开连接

            message = data.decode()  # 解码接收到的数据
            print(f"收到来自 {addr} 的消息: {message}")

            # 可选：你可以在这里处理收到的数据或向客户端发送响应
            response = f"消息 '{message}' 已收到"
            writer.write(response.encode())
            await writer.drain()  # 确保消息被发送
    except Exception as e:
        print(f"处理客户端 {addr} 时发生错误: {e}")
    finally:
        print(f"客户端 {addr} 断开连接")
        writer.close()
        await writer.wait_closed()

async def main():
    # 设置服务器监听所有接口的端口8881
    server = await asyncio.start_server(handle_client, '0.0.0.0',8000)

    addr = server.sockets[0].getsockname()
    print(f"服务器已启动，监听在 {addr}")

    async with server:
        await server.serve_forever()

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())
