from common.log_utils import setup_logger
from common.packet import Packet
from common.type import (
    T_DEVELOPER_LOGIN,
    T_DEVELOPER_REGISTER,
    T_DEVELOPER_LOGOUT,
    T_LIST_DEVELOPER_GAMES,
)
from ..database_server.database_server import DatabaseServer
import socket


class DeveloperServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.logger = setup_logger("developer_server", "logs/developer_server.log")
        self.user_context = []
        self.database_server = DatabaseServer()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        self.logger.info(f"Developer server started on {self.host}:{self.port}")
        while True:
            client, addr = server.accept()
            self._handle_client(client, addr)
        server.close()
        # logout all users

    def _handle_client(self, client: socket.socket, addr: tuple[str, int]):
        self.logger.info(f"Client connected: {addr}")
        while True:
            packet = Packet.receive(client)
            if packet is None:
                self.logger.info(f"Client disconnected: {addr}")
                break
            self._handle_packet(client, addr, packet)
        client.close()
        self.logger.info(f"Client disconnected: {addr}")

    def _handle_packet(
        self, client: socket.socket, addr: tuple[str, int], packet: Packet
    ):
        if packet.type == T_DEVELOPER_LOGIN:
            reply = self.database_server.handle_developer_login(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_DEVELOPER_REGISTER:
            reply = self.database_server.handle_developer_register(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_DEVELOPER_LOGOUT:
            reply = self.database_server.handle_developer_logout(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_LIST_DEVELOPER_GAMES:
            reply = self.database_server.handle_list_developer_games(packet)
            client.sendall(reply.to_bytes())
