import threading
import socket
import argparse
import os

from tools.toolkit import Tools as t

logging = t.all.logging_config_screen()
logging = logging.getLogger(__name__)


class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.connections = []
        self.host = host
        self.port = port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen(1)
        print(f"Listening at", sock.getsockname())

        while True:
            # Accepting new connection
            sc, sockname = sock.accept()
            print(
                f"Accepting a new connection from {sc.getpeername()} to {sc.getsockname()}"
            )

            # Create a new thread
            server_socket = ServerSocket(sc, sockname, self)
            server_socket.start()

            # Add thread to active connection
            self.connections.append(server_socket)
            print(f"Ready to receive messages from {sc.getpeername()}")

    def broadcast(self, message, source):
        for connection in self.connections:
            # Send all connected clients accept the source client
            if connection.sockname != source:
                connection.send(message)

    def remove_connection(self, connection):
        self.connections.remove(connection)


class ServerSocket(threading.Thread):
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server

    def run(self):
        while True:
            message = self.sc.recv(1024).decode("ascii")
            if message:
                print(f"{self.sockname} says {message}")
                self.server.broadcast(message, self.sockname)
            else:
                print(f"{self.sockname} has closed the connection")
                self.sc.close()
                self.server.remove_connection(self)

    def send(self, message):

        self.sc.sendall(message.encode("ascii"))

    def exit(self, server):
        while True:
            ipt = input("")
            if ipt == "q":
                print("Closing all connections...")
                for connection in server.connections:
                    connection.sc.close()

                print("Shutting down the server...")
                os._exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatroom Server")
    parser.add_argument("host", help="Interface the server listen at ")
    parser.add_argument(
        "-p", metavar="PORT", type=int, default=1060, help="TCP port(default 1060)"
    )

    args = parser.parse_args()

    # Create and start server thread
    server = Server(args.host, args.p)
    server.start()

    exit = threading.Thread(target=exit, args=(server,))
    exit.start()