import socket
from common.packet import Packet
from common.type import T_LOGIN, T_REGISTER, T_LOGOUT
from common.Packet.auth import LoginPacket, RegisterPacket, LogoutPacket
from common.log_utils import setup_logger


class LobbyClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.logger = setup_logger("LobbyClient", "./logs/lobby_client.log")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            self.logger.info(f"Connected to lobby server at {self.host}:{self.port}")
            while True:
                self.logger.info("Enter command (login/register/logout/exit):")
                command = input().strip()
                if command == "login":
                    username = input("Username: ").strip()
                    password = input("Password: ").strip()
                    packet = LoginPacket(username, password)
                    s.sendall(packet.to_bytes())
                    reply = Packet.receive(s)
                    if reply.type == T_LOGIN:
                        self.logger.info(reply.data["message"])
                    else:
                        self.logger.info(reply.data["message"])
                elif command == "register":
                    username = input("Username: ").strip()
                    password = input("Password: ").strip()
                    packet = RegisterPacket(username, password)
                    s.sendall(packet.to_bytes())
                    reply = Packet.receive(s)
                    if reply.type == T_REGISTER:
                        self.logger.info(reply.data["message"])
                    else:
                        self.logger.info(reply.data["message"])
                elif command == "logout":
                    packet = LogoutPacket()
                    s.sendall(packet.to_bytes())
                    reply = Packet.receive(s)
                    if reply.type == T_LOGOUT:
                        self.logger.info(reply.data["message"])
                    else:
                        self.logger.info(reply.data["message"])
                elif command == "exit":
                    break
                else:
                    self.logger.info("Invalid command")
