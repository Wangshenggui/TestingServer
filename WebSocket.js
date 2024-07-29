const WebSocket = require('ws'); // 引入 WebSocket 库

const connectedClients = new Set(); // 创建一个集合，用于存储所有已连接的客户端

// 处理新连接的客户端
const handleClient = (ws) => {
    connectedClients.add(ws); // 将新客户端添加到已连接客户端集合中
    const addr = ws._socket.remoteAddress + ":" + ws._socket.remotePort; // 获取客户端的 IP 地址和端口
    console.log(`客户端 ${addr} 连接成功`); // 打印客户端连接成功的信息

    try {
        // 发送连接成功消息给客户端
        ws.send(JSON.stringify({ message: "连接成功！" })); // 发送 JSON 格式的连接成功消息

        // 新客户端连接时广播经纬度信息（如果需要可以解注）
        //broadcastMessage({ lng: 106.621903, lat: 26.382418 });

        // 监听客户端发送的消息
        ws.on('message', (message) => {
            console.log(`收到来自客户端 ${addr} 的消息: ${message}`); // 打印收到的消息
            try {
                const parsedMessage = JSON.parse(message); // 尝试解析收到的 JSON 消息
                broadcastMessage(parsedMessage); // 广播解析后的消息给所有客户端
            } catch (error) {
                console.error(`解析客户端 ${addr} 的消息时出错: ${error}`); // 打印解析消息时的错误信息
            }
        });
    } catch (error) {
        console.error(`客户端 ${addr} 连接错误: ${error}`); // 打印客户端连接时的错误信息
    }

    // 监听客户端断开连接事件
    ws.on('close', () => {
        console.log(`客户端 ${addr} 断开连接`); // 打印客户端断开连接的信息
        // 客户端断开连接时移除其 WebSocket 连接
        connectedClients.delete(ws); // 从集合中移除已断开的客户端
    });
};

// 广播消息给所有已连接的客户端
const broadcastMessage = (message) => {
    for (const client of connectedClients) { // 遍历所有已连接的客户端
        client.send(JSON.stringify(message)); // 发送消息给客户端
        console.log(`广播消息: ${JSON.stringify(message)}`); // 打印广播的消息
    }
};

// 创建一个 WebSocket 服务器，监听在端口 8001
const wss = new WebSocket.Server({ port: 8001 });

// 监听新的客户端连接事件
wss.on('connection', handleClient);

console.log("WebSocket 服务器已启动，监听在 172.29.103.118:8001"); // 打印服务器启动信息
