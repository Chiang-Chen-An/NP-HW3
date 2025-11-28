from common.Packet.developer import (
    DeveloperLoginPacket,
    DeveloperRegisterPacket,
    DeveloperLogoutPacket,
    ListDeveloperGamesPacket,
    UploadGamePacket,
)
from common.type import (
    T_DEVELOPER_LOGIN,
    T_DEVELOPER_REGISTER,
    T_DEVELOPER_LOGOUT,
    T_LIST_DEVELOPER_GAMES,
    T_UPLOAD_GAME,
)
from common.log_utils import setup_logger
from common.packet import Packet
from pathlib import Path
import os
import json
import socket


class UserContext:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class DeveloperClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.logger = setup_logger("developer_client", "logs/developer_client.log")
        self.user_context = None

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            self.logger.info(f"Connected to lobby server at {self.host}:{self.port}")
            print("=" * 50)
            print("WELCOME TO THE LOBBY!".center(50))
            print("=" * 50)
            while True:
                self.handle_auth(s)
                if self.user_context is None:
                    break
                self.handle_lobby(s)

    def handle_auth(self, s: socket.socket):
        while True:
            print("1. Login")
            print("2. Register")
            print("3. Exit")
            command = input("Enter command (1 ~ 3): ").strip()
            if command == "1":
                print("=" * 50)
                print("LOGIN".center(50))
                print("=" * 50)
                username = input("Username: ").strip()
                password = input("Password: ").strip()
                packet = DeveloperLoginPacket(username, password)
                print("DEBUG")
                s.sendall(packet.to_bytes())
                print("DEBUG")
                reply = Packet.receive(s)
                if reply is None:
                    self.logger.error("Failed to receive response from server")
                    return
                if reply.type == T_DEVELOPER_LOGIN and reply.data["success"]:
                    self.logger.info(reply.data["message"])
                    self.user_context = UserContext(username, password)
                    return
                else:
                    self.logger.info(reply.data["message"])
            elif command == "2":
                print("=" * 50)
                print("REGISTER".center(50))
                print("=" * 50)
                username = input("Username: ").strip()
                password = input("Password: ").strip()
                packet = DeveloperRegisterPacket(username, password)
                s.sendall(packet.to_bytes())
                reply = Packet.receive(s)
                if reply is None:
                    self.logger.error("Failed to receive response from server")
                    return
                if reply.type == T_DEVELOPER_REGISTER and reply.data["success"]:
                    self.logger.info(reply.data["message"])
                else:
                    self.logger.info(reply.data["message"])
            elif command == "3":
                break
            else:
                self.logger.info("Invalid command")

    def handle_lobby(self, s: socket.socket):
        while True:
            print("=" * 50)
            print(
                f"Welcome to the Developer Lobby! {self.user_context.username}".center(
                    50
                )
            )
            print("=" * 50)
            print("1. List my games")
            print("2. Upload a new game")
            print("3. Logout")
            command = input("Enter command (1 ~ 3): ").strip()
            if command == "1":
                self.handle_list_games(s)
            elif command == "2":
                self.handle_upload_game(s)
            elif command == "3":
                if self.handle_logout(s):
                    break
            else:
                self.logger.info("Invalid command")

    def handle_list_games(self, s: socket.socket):
        packet = ListDeveloperGamesPacket(self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return
        if reply.type == T_LIST_DEVELOPER_GAMES and reply.data["success"]:
            games = reply.data["games"]
            for game in games:
                print(f"Game ID: {game['game_id']}")
                print(f"Game Name: {game['game_name']}")
                print(f"Game Description: {game['game_description']}")
                print(f"Game Version: {game['game_version']}")
                print(f"Game Author: {game['game_author']}")
                print(f"Download Count: {game['download_count']}")
                print(f"Comments: {game['comments']}")
                print(f"Game Created At: {game['game_created_at']}")
                print("-" * 50)
            # TODO: Update a Game
        else:
            self.logger.info(reply.data["message"])
