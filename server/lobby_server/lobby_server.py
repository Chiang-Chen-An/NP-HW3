from common.context.userContext import UserContext
from common.context.roomContext import RoomContext
from common.log_utils import setup_logger
from common.packet import Packet
from common.type import (
    T_LOGIN,
    T_REGISTER,
    T_LOGOUT,
    T_LIST_ONLINE_USERS,
    T_LIST_GAMES,
    T_GET_GAME_DETAIL,
    T_GAME_REVIEW,
    T_CREATE_ROOM,
    T_JOIN_ROOM,
    T_LEAVE_ROOM,
    T_START_GAME,
    T_END_GAME,
    T_LIST_ROOMS,
)
from common.Packet.game import ListRoomsPacketReply
from ..database_server.database_server import DatabaseServer
import socket


class LobbyServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.logger = setup_logger("lobby_server", "logs/lobby_server.log")
        self.user_context = []  # List of UserContext
        self.room_context = [
            RoomContext(1, 1, 4, "user1"),
            RoomContext(2, 2, 4, "user2"),
        ]  # List of RoomContext
        self.database_server = DatabaseServer()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        self.logger.info(f"Lobby server started on {self.host}:{self.port}")
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
        if packet.type == T_LOGIN:
            reply = self.database_server.handle_login(packet)
            if reply.data["success"]:
                self.user_context.append(UserContext(packet.data["username"], client))
            client.sendall(reply.to_bytes())
        elif packet.type == T_REGISTER:
            reply = self.database_server.handle_register(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_LOGOUT:
            reply = self.database_server.handle_logout(packet)
            if reply.data["success"]:
                self.user_context.remove(
                    next(
                        (
                            user
                            for user in self.user_context
                            if user.username == packet.data["username"]
                        ),
                        None,
                    )
                )
            client.sendall(reply.to_bytes())
        elif packet.type == T_LIST_ONLINE_USERS:
            reply = self.database_server.handle_list_online_users(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_LIST_GAMES:
            reply = self.database_server.handle_list_games(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_GET_GAME_DETAIL:
            reply = self.database_server.handle_get_game_detail(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_GAME_REVIEW:
            reply = self.database_server.handle_game_review(packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_LIST_ROOMS:
            reply = self._handle_list_rooms(client, addr, packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_CREATE_ROOM:
            reply = self._handle_create_room(client, addr, packet)
            client.sendall(reply.to_bytes())
        else:
            self.logger.info(f"Invalid packet type: {packet.type}")

    def _handle_create_room(
        self, client: socket.socket, addr: tuple[str, int], packet: Packet
    ):
        self.logger.info(f"Client {addr} created a room")
        username = packet.data["username"]
        game_id = packet.data["game_id"]
        room_id = self.room_context[-1].room_id + 1 if self.room_context else 1
        max_players = self.database_server.get_game_max_players(game_id)
        new_room_context = GameContext(room_id, game_id, max_players, username)
        self.room_context.append(new_room_context)
        reply = CreateGamePacketReply(True, room_id)
        return reply

    def _handle_list_rooms(
        self, client: socket.socket, addr: tuple[str, int], packet: Packet
    ):
        self.logger.info(f"Client {addr} listed rooms")
        rooms = []
        for room_context in self.room_context:
            rooms.append(
                {
                    "room_id": room_context.room_id,
                    "game_id": room_context.game_id,
                    "game_name": self.database_server.get_game_name(
                        room_context.game_id
                    ),
                    "max_players": room_context.max_players,
                    "room_owner": room_context.room_owner,
                    "players": room_context.players,
                    "is_started": room_context.is_started,
                }
            )
        reply = ListRoomsPacketReply(True, rooms)
        return reply
