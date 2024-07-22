import socket

def start_server(host='8.137.81.229', port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Server listening on {host}:{port}")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f"Received data: {data.decode()}")
                    conn.sendall(b'Received: ' + data)

if __name__ == "__main__":
    start_server()

