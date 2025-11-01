import socket
import threading
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
    
    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"[CONNECTED] Connected to server at {self.host}:{self.port}")
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Start sending messages
            self.send_messages()
            
        except Exception as e:
            print(f"[ERROR] Could not connect to server: {e}")
            print("Make sure the server is running!")
            sys.exit(1)
    
    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    print(message, end='')
                else:
                    break
            except:
                break
        
        print("\n[DISCONNECTED] Connection to server lost.")
        self.running = False
    
    def send_messages(self):
        try:
            while self.running:
                message = input()
                if message.lower() == '/quit':
                    self.client_socket.send(message.encode())
                    print("[INFO] Leaving chat room...")
                    break
                elif message:
                    self.client_socket.send(message.encode())
        except KeyboardInterrupt:
            print("\n[INFO] Exiting...")
        finally:
            self.client_socket.close()
            self.running = False

if __name__ == "__main__":
    print("=" * 40)
    print("    COMMAND LINE CHAT CLIENT")
    print("=" * 40)
    
    # Ask for server details
    host = input("Enter server IP (press Enter for localhost): ").strip()
    if not host:
        host = '127.0.0.1'
    
    port_input = input("Enter server port (press Enter for 5555): ").strip()
    port = int(port_input) if port_input else 5555
    
    print(f"\n[CONNECTING] Connecting to {host}:{port}...")
    
    client = ChatClient(host, port)
    client.connect()