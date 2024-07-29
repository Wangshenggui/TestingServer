const WebSocket = require('ws');

const connectedClients = new Set();

const handleClient = (ws) => {
    connectedClients.add(ws);
    const addr = ws._socket.remoteAddress + ":" + ws._socket.remotePort;
    console.log(`客户端 ${addr} 连接成功`);

    try {
        // 发送连接成功消息
        ws.send(JSON.stringify({ message: "连接成功！" }));

        // 新客户端连接时广播经纬度信息
        //broadcastMessage({ lng: 106.621903, lat: 26.382418 });

        ws.on('message', (message) => {
            console.log(`收到来自客户端 ${addr} 的消息: ${message}`);
            try {
                const parsedMessage = JSON.parse(message);
                broadcastMessage(parsedMessage);
            } catch (error) {
                console.error(`解析客户端 ${addr} 的消息时出错: ${error}`);
            }
        });
    } catch (error) {
        console.error(`客户端 ${addr} 连接错误: ${error}`);
    }

    ws.on('close', () => {
        console.log(`客户端 ${addr} 断开连接`);
        // 客户端断开连接时移除其 WebSocket 连接
        connectedClients.delete(ws);
    });
};

const broadcastMessage = (message) => {
    // 广播消息给所有客户端
    for (const client of connectedClients) {
        client.send(JSON.stringify(message));
        console.log(`广播消息: ${JSON.stringify(message)}`);
    }
};

const wss = new WebSocket.Server({ port: 8880 });

wss.on('connection', handleClient);

console.log("WebSocket 服务器已启动，监听在 172.29.103.118:8880");
