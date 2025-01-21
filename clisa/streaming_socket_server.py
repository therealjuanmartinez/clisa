import socket
import threading
import struct
import queue
import time  # Import time for sleep functionality

class StreamingSocketServer:
    _instance = None

    def __new__(cls, port):
        if cls._instance is None:
            if not isinstance(port, int) or not (1024 <= port <= 65535):
                raise ValueError("Port must be an integer between 1024 and 65535.")
            cls._instance = super(StreamingSocketServer, cls).__new__(cls)
            cls._instance.initialized = False
            cls._instance.port = port
            cls._instance.host = '0.0.0.0'  # Specify host to bind to all interfaces
            cls._instance.buffered_data = []
            cls._instance.data_queue = queue.Queue()
            cls._instance.stop_event = threading.Event()
            cls._instance.server_thread = None
            cls._instance.client_thread = None
            cls._instance.client_connected = False
        return cls._instance

    def start(self):
        if not self.initialized:
            self.initialized = True
            self.stop_event.clear()
            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.server_thread:
            self.server_thread.join()
        if self.client_thread:
            self.client_thread.join()

    def run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server_socket:
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable address reuse
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1)  # Set a timeout of 1 second

            while not self.stop_event.is_set():
                try:
                    self.client_socket, addr = self.server_socket.accept()
                    with self.client_socket:
                        self.client_connected = True
                        self.send_buffered_data()
                        self.handle_client_connection()
                except socket.timeout:
                    continue  # Timeout occurred, continue checking for stop event
                except OSError:
                    # Handle any socket error (e.g., if the server is stopped)
                    break

    def handle_client_connection(self):
        while self.client_connected and not self.stop_event.is_set():
            try:
                data = self.client_socket.recv(1024)  # Adjust buffer size as needed
                if not data:
                    break  # Client disconnected
            except ConnectionResetError:
                break  # Handle disconnection gracefully

        self.client_connected = False

    def send_buffered_data(self):
        while self.buffered_data:
            data = self.buffered_data.pop(0)
            self.send_data(data)

    def send_data(self, data):
        if isinstance(data, str):
            data = data.encode()  # Convert string to bytes if needed

        if self.client_connected:
            # Prepend the length of the data as a 4-byte integer
            length_prefix = struct.pack('!I', len(data))
            self.client_socket.sendall(length_prefix + data)
        else:
            # Buffer the data if no client is connected
            self.buffered_data.append(data)

    def clear_buffer(self):
        self.buffered_data.clear()

# Example usage
if __name__ == "__main__":
    port = 5000  # Specify the port you want to use
    server = StreamingSocketServer(port)  # Create server instance
    server.start()  # Start the server

    try:
        # Example of sending data to clients
        for i in range(10):
            message = f"Message {i}"  # Create data to send (string)
            server.send_data(message)  # Send data to connected clients
            time.sleep(2)  # Simulate doing other work in the main thread
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()  # Ensure the server is stopped
