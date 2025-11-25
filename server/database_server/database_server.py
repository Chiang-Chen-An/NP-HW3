import json
import os
from datetime import datetime
import socket
from common.packet import Packet
from common.type import T_LOGIN, T_REGISTER, T_LOGOUT
from common.Packet.db import DBLoginPacket, DBRegisterPacket, DBLogoutPacket
from common.log_utils import setup_logger


class DatabaseServer:
    def __init__(self, port: int, host: str):
        self.port = port
        self.host = host
        self.database = {
            "user": os.path.join(os.path.dirname(__file__), "data/users.json")
        }
        self.logger = setup_logger("DatabaseServer", "./logs/database_server.log")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            self.logger.info(f"Database server listening on {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                with conn:
                    self.logger.info(f"Connected by {addr}")
                    while True:
                        packet = Packet.receive(conn)
                        if not packet:
                            break
                        reply = self.handle_packet(packet)
                        conn.sendall(reply.to_bytes())

    def handle_packet(self, packet: Packet):
        if packet.type == T_LOGIN:
            return self.handle_login(packet)
        elif packet.type == T_REGISTER:
            return self.handle_register(packet)
        elif packet.type == T_LOGOUT:
            return self.handle_logout(packet)

    def handle_login(self, packet: Packet):
        username = packet.data["username"]
        password = packet.data["password"]
        if not username or not password:
            self.logger.info("Username or password is empty")
            return DBLoginPacket(False, "Username or password is empty")
        with open(self.database["user"], "r") as f:
            users = json.load(f)

        for user in users:
            if user["username"] == username and user["password"] == password:
                user["is_online"] = True
                user["last_login"] = datetime.now().isoformat()
                with open(self.database["user"], "w") as f:
                    json.dump(users, f, indent=2)
                self.logger.info("Login successful")
                return DBLoginPacket(True, "Login successful")

        self.logger.info("Login failed")
        return DBLoginPacket(False, "Login failed")

    def handle_register(self, packet: Packet):
        username = packet.data["username"]
        password = packet.data["password"]
        if not username or not password:
            self.logger.info("Username or password is empty")
            return DBRegisterPacket(False, "Username or password is empty")
        with open(self.database["user"], "r") as f:
            users = json.load(f)

        for user in users:
            if user["username"] == username:
                self.logger.info("Username already exists")
                return DBRegisterPacket(False, "Username already exists")

        new_user = {
            "username": username,
            "password": password,
            "is_online": False,
            "last_login": "",
            "created_at": datetime.now().isoformat(),
            "role": "user",
        }
        users.append(new_user)

        with open(self.database["user"], "w") as f:
            json.dump(users, f, indent=2)
        self.logger.info("Register successful")
        return DBRegisterPacket(True, "Register successful")

    def handle_logout(self, packet: Packet):
        username = packet.data["username"]
        with open(self.database["user"], "r") as f:
            users = json.load(f)

        for user in users:
            if user["username"] == username:
                user["is_online"] = False
                with open(self.database["user"], "w") as f:
                    json.dump(users, f, indent=2)
                self.logger.info("Logout successful")
                return DBLogoutPacket(True, "Logout successful")

        self.logger.info("Username not found")
        return DBLogoutPacket(False, "Username not found")
