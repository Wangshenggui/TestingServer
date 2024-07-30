const WebSocket = require('ws'); // 引入 WebSocket 库
const fs = require('fs'); // 引入 fs 模块用于文件操作
const path = require('path'); // 引入 path 模块用于路径操作

const connectedClients = new Set(); // 创建一个集合，用于存储所有已连接的客户端

// 获取运行文件的目录路径
const getScriptDirectory = () => {
    return __dirname; // 使用 __dirname 获取当前脚本所在的目录路径
};

// 处理新连接的客户端
const handleClient = (ws) => {
    connectedClients.add(ws); // 将新客户端添加到已连接客户端集合中
    const addr = ws._socket.remoteAddress + ":" + ws._socket.remotePort; // 获取客户端的 IP 地址和端口
    console.log(`客户端 ${addr} 连接成功`); // 打印客户端连接成功的信息

    try {
        // 发送连接成功消息给客户端
        ws.send(JSON.stringify({ message: "连接成功！" })); // 发送 JSON 格式的连接成功消息

        // 监听客户端发送的消息
        ws.on('message', (message) => {
            console.log(`收到来自客户端 ${addr} 的消息: ${message}`); // 打印收到的消息
            try {
                const parsedMessage = JSON.parse(message); // 尝试解析收到的 JSON 消息

                // 检查消息是否以 'read' 开头
                if (parsedMessage.command && parsedMessage.command === 'read') {
                    // 如果消息的 'command' 字段是 'read'，则读取文件并广播
                    readDataAndBroadcast();
                } else {
                    // 处理普通消息
                    broadcastMessage(parsedMessage); // 广播解析后的消息给所有客户端
                    //解析JSON数据
                    const dataArray = Object.values(parsedMessage);
                    //合并数据
                    combinedData = dataArray[0] + ',' +dataArray[1];
                    // 将解析后的消息保存到文件
                    saveDataToTextFile(combinedData);
                }
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
        if (client.readyState === WebSocket.OPEN) { // 确保客户端连接处于打开状态
            client.send(JSON.stringify(message)); // 发送消息给客户端
            console.log(`广播消息: ${JSON.stringify(message)}`); // 打印广播的消息
        }
    }
};

// 保存数据到文本文件
const saveDataToTextFile = (data) => {
    const scriptDirectory = getScriptDirectory(); // 获取脚本所在目录路径
    const directoryPath = path.join(scriptDirectory, 'Data'); // 构建 Data 文件夹的路径
    const filePath = path.join(directoryPath, 'data.csv'); // 文本文件路径

    // 确保文件夹存在
    fs.mkdir(directoryPath, { recursive: true }, (err) => {
        if (err) {
            console.error('创建文件夹失败:', err);
            return;
        }

        // 将 JSON 数据转换为字符串格式
        const textData = JSON.stringify(data, null, 2);

        // 将数据追加到文本文件
        fs.appendFile(filePath, textData + '\n', (err) => {
            if (err) {
                console.error(`写入文件 ${filePath} 时出错:`, err);
            } else {
                console.log(`数据已保存到文件: ${filePath}`);
            }
        });
    });
};

// 读取数据文件并广播到所有客户端
const readDataAndBroadcast = () => {
    const scriptDirectory = getScriptDirectory(); // 获取脚本所在目录路径
    const filePath = path.join(scriptDirectory, 'Data', 'data.txt'); // 构建文件路径

    fs.readFile(filePath, 'utf-8', (err, data) => {
        if (err) {
            console.error('读取文件时出错:', err);
            return;
        }

        // 使用正则表达式分割 JSON 对象
        const jsonStrings = data.match(/{[^}]+}/g); // 匹配每个 JSON 对象
        if (jsonStrings) {
            jsonStrings.forEach((jsonString) => {
                const jsonObject = JSON.parse(jsonString); // 解析 JSON 字符串
                broadcastMessage(jsonObject); // 广播 JSON 对象给所有客户端
            });
            console.log('文件中的 JSON 对象已广播给所有客户端');
        } else {
            console.log('文件中没有找到有效的 JSON 对象');
        }
    });
};

// 创建一个 WebSocket 服务器，监听在端口 8001
const wss = new WebSocket.Server({ port: 8001 });

// 监听新的客户端连接事件
wss.on('connection', handleClient);

console.log("WebSocket 服务器已启动，监听在 172.29.103.118:8001"); // 打印服务器启动信息
