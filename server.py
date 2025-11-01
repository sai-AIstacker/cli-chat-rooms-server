import socket
import threading
import sys

class ChatRoom:
    def __init__(self, room_id, room_name):
        self.room_id = room_id
        self.room_name = room_name
        self.clients = []
        self.lock = threading.Lock()
    
    def add_client(self, client_socket, username):
        with self.lock:
            self.clients.append((client_socket, username))
    
    def remove_client(self, client_socket):
        with self.lock:
            self.clients = [(sock, user) for sock, user in self.clients if sock != client_socket]
    
    def broadcast(self, message, sender_socket=None):
        with self.lock:
            for client_socket, username in self.clients:
                if client_socket != sender_socket:
                    try:
                        client_socket.send(message.encode())
                    except:
                        pass

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rooms = {}
        self.rooms_lock = threading.Lock()
        
    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[SERVER STARTED] Server is listening on {self.host}:{self.port}")
            print("[INFO] Waiting for connections...")
            
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"[NEW CONNECTION] {address} connected")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\n[SERVER SHUTDOWN] Shutting down server...")
            self.server_socket.close()
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] Server error: {e}")
            self.server_socket.close()
    
    def handle_client(self, client_socket, address):
        try:
            # Get username
            client_socket.send("Enter your username: ".encode())
            username = client_socket.recv(1024).decode().strip()
            
            if not username:
                username = f"User_{address[1]}"
            
            print(f"[USERNAME] {address} set username to '{username}'")
            
            # Show menu and handle room selection
            room = None
            while room is None:
                self.send_menu(client_socket)
                choice = client_socket.recv(1024).decode().strip()
                
                if choice == '1':
                    room = self.list_rooms(client_socket)
                elif choice == '2':
                    room = self.create_room(client_socket)
                elif choice == '3':
                    room = self.join_room(client_socket)
                elif choice == '4':
                    client_socket.send("Goodbye!\n".encode())
                    client_socket.close()
                    return
                else:
                    client_socket.send("Invalid choice. Try again.\n".encode())
            
            # Add client to room
            room.add_client(client_socket, username)
            welcome_msg = f"\n[SYSTEM] {username} joined the room!\n"
            room.broadcast(welcome_msg, client_socket)
            client_socket.send(f"[SYSTEM] Welcome to {room.room_name}! Start chatting...\n".encode())
            
            # Handle messages
            while True:
                message = client_socket.recv(1024).decode().strip()
                if not message:
                    break
                
                if message.lower() == '/quit':
                    break
                
                formatted_msg = f"[{username}]: {message}\n"
                print(f"[ROOM {room.room_id}] {formatted_msg.strip()}")
                room.broadcast(formatted_msg, client_socket)
                
        except Exception as e:
            print(f"[ERROR] Error handling client {address}: {e}")
        finally:
            if room:
                room.remove_client(client_socket)
                leave_msg = f"[SYSTEM] {username} left the room.\n"
                room.broadcast(leave_msg)
            client_socket.close()
            print(f"[DISCONNECTED] {address} disconnected")
    
    def send_menu(self, client_socket):
        menu = """
========== CHAT ROOM MENU ==========
1. List all chat rooms
2. Create a new chat room
3. Join an existing chat room
4. Exit
====================================
Enter your choice (1-4): """
        client_socket.send(menu.encode())
    
    def list_rooms(self, client_socket):
        with self.rooms_lock:
            if not self.rooms:
                client_socket.send("\nNo chat rooms available. Create one!\n".encode())
            else:
                room_list = "\n===== Available Chat Rooms =====\n"
                for room_id, room in self.rooms.items():
                    room_list += f"Room ID: {room_id} | Name: {room.room_name} | Users: {len(room.clients)}\n"
                room_list += "================================\n"
                client_socket.send(room_list.encode())
        return None
    
    def create_room(self, client_socket):
        client_socket.send("Enter new room ID (e.g., 101): ".encode())
        room_id = client_socket.recv(1024).decode().strip()
        
        with self.rooms_lock:
            if room_id in self.rooms:
                client_socket.send(f"Room {room_id} already exists. Try joining it.\n".encode())
                return None
            
            client_socket.send("Enter room name: ".encode())
            room_name = client_socket.recv(1024).decode().strip()
            
            if not room_name:
                room_name = f"Room_{room_id}"
            
            new_room = ChatRoom(room_id, room_name)
            self.rooms[room_id] = new_room
            print(f"[NEW ROOM] Room '{room_name}' (ID: {room_id}) created")
            client_socket.send(f"Room '{room_name}' created successfully!\n".encode())
            return new_room
    
    def join_room(self, client_socket):
        client_socket.send("Enter room ID to join: ".encode())
        room_id = client_socket.recv(1024).decode().strip()
        
        with self.rooms_lock:
            if room_id in self.rooms:
                return self.rooms[room_id]
            else:
                client_socket.send(f"Room {room_id} does not exist. Try creating it.\n".encode())
                return None

if __name__ == "__main__":
    server = ChatServer()
    server.start()