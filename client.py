import threading
import socket
import argparse
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt


class Send(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name

    def run(self):
        while True:
            print("{}: ".format(self.name), end="")
            sys.stdout.flush()
            message = sys.stdin.readline()[:-1]

            if message == "quit".capitalize():
                self.sock.sendall(
                    "Server: {} has left the chat.".format(self.name).encode("ascii")
                )
                break
            else:
                self.sock.sendall("{}: {}".format(self.name, message).encode("ascii"))

        print("Quitting...")
        self.sock.close()
        sys.exit(0)


class Receive(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name
        self.messages = None

    def run(self):
        while True:
            message = self.sock.recv(1024).decode("ascii")
            if message:
                if self.messages:
                    self.messages.addItem(message)
                    print("\r{}\n{}: ".format(message, self.name), end="")
                else:
                    print("\r{}\n{}: ".format(message, self.name), end="")
            else:
                print("\nConnection lost to the server!")
                print("Quitting...")
                self.sock.close()
                sys.exit(0)


class ChatClient(QMainWindow):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None

        self.messages = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Encrypted Chat v1.0")

        # Main layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Chat message display
        self.messages = QListWidget()
        layout.addWidget(self.messages)

        # Input area
        input_layout = QHBoxLayout()
        self.text_input = QLineEdit()
        self.text_input.returnPressed.connect(self.send_message)
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.text_input)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_client(self):
        print("Connecting to {}:{}...".format(self.host, self.port))
        self.sock.connect((self.host, self.port))
        print("Connected to {}:{}".format(self.host, self.port))
        print()

        self.name = input("Your name: ")
        print(
            "Welcome, {}! Preparing to send and receive messages...".format(self.name)
        )
        self.text_input.setPlaceholderText(f"Hi, {self.name}! Write your message here.")

        # Start threads for sending and receiving
        send = Send(self.sock, self.name)
        receive = Receive(self.sock, self.name)

        receive.messages = self.messages
        send.start()
        receive.start()

        self.sock.sendall(
            "Server: {} has joined the chat.".format(self.name).encode("ascii")
        )

        print("Ready! Type 'QUIT' to leave the chatroom.")
        print("{}: ".format(self.name), end="")

    def send_message(self):
        message = self.text_input.text()
        self.text_input.clear()
        self.messages.addItem(f"{self.name}: {message}")

        if message.upper() == "QUIT":
            self.sock.sendall(
                "Server: {} has left the chat.".format(self.name).encode("ascii")
            )
            print("Quitting...")
            self.sock.close()
            sys.exit(0)
        else:
            self.sock.sendall("{}: {}".format(self.name, message).encode("ascii"))


def main(host, port):
    app = QApplication(sys.argv)
    client = ChatClient(host, port)
    client.start_client()
    client.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatroom Client")
    parser.add_argument("host", help="Server address to connect to")
    parser.add_argument(
        "-p", metavar="PORT", type=int, default=1060, help="TCP port (default 1060)"
    )

    args = parser.parse_args()

    main(args.host, args.p)
