import socket


class UserContext:
    def __init__(self, username: str, socket: socket.socket):
        self.username = username
        self.socket = socket
