import json
import os
from datetime import datetime
import socket
from common.packet import Packet
from common.type import (
    T_LOGIN,
    T_REGISTER,
    T_LOGOUT,
    T_LIST_ONLINE_USERS,
    T_LIST_GAMES,
    T_GET_GAME_DETAIL,
    T_GAME_REVIEW,
)
from common.Packet.db import (
    DBLoginPacket,
    DBRegisterPacket,
    DBLogoutPacket,
    DBListGamesPacket,
    DBListOnlineUsersPacket,
    DBGameReviewPacket,
    DBGetGameDetailPacket,
    DBDeveloperLoginPacket,
    DBDeveloperRegisterPacket,
    DBDeveloperLogoutPacket,
    ListDeveloperGamesPacket,
)
from common.log_utils import setup_logger


class DatabaseServer:
    def __init__(self, port: int = 12345, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.database = {
            "user": os.path.join(os.path.dirname(__file__), "data/users.json"),
            "game": os.path.join(os.path.dirname(__file__), "data/games.json"),
            "developer": os.path.join(
                os.path.dirname(__file__), "data/developers.json"
            ),
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
        elif packet.type == T_LIST_ONLINE_USERS:
            return self.handle_list_online_users(packet)
        elif packet.type == T_LIST_GAMES:
            return self.handle_list_games(packet)
        elif packet.type == T_GET_GAME_DETAIL:
            return self.handle_get_game_detail(packet)
        elif packet.type == T_GAME_REVIEW:
            return self.handle_game_review(packet)
        elif packet.type == T_DEVELOPER_LOGIN:
            return self.handle_developer_login(packet)
        elif packet.type == T_DEVELOPER_REGISTER:
            return self.handle_developer_register(packet)
        elif packet.type == T_DEVELOPER_LOGOUT:
            return self.handle_developer_logout(packet)
        elif packet.type == T_LIST_DEVELOPER_GAMES:
            return self.handle_list_developer_games(packet)
        # elif packet.type == T_UPLOAD_GAME:
        #     return self.handle_upload_game(packet)
        # elif packet.type == T_UPDATE_GAME:
        #     return self.handle_update_game(packet)

    # Handle Auth Packets

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

    # Handle Game Packets

    def handle_list_games(self, packet: Packet):
        with open(self.database["game"], "r") as f:
            games = json.load(f)
        for game in games:
            if not game["comments"]:
                game["average_rating"] = 0
            else:
                game["average_rating"] = sum(
                    comment["rating"] for comment in game["comments"]
                ) / len(game["comments"])
        return DBListGamesPacket(True, games)

    def handle_get_game_detail(self, packet: Packet):
        game_id = packet.data["game_id"]
        with open(self.database["game"], "r") as f:
            games = json.load(f)
        for game in games:
            if game["game_id"] == game_id:
                return DBGetGameDetailPacket(True, game)
        return DBGetGameDetailPacket(False, "Game not found")

    def handle_game_review(self, packet: Packet):
        game_id = packet.data["game_id"]
        score = packet.data["score"]
        comment = packet.data["comment"]
        with open(self.database["game"], "r") as f:
            games = json.load(f)
        for game in games:
            if game["game_id"] == game_id:
                game["comments"].append(
                    {"username": "user", "rating": score, "comment": comment}
                )
                with open(self.database["game"], "w") as f:
                    json.dump(games, f, indent=2)
                return DBGameReviewPacket(True, "Review submitted successfully")
        return DBGameReviewPacket(False, "Game not found")

    # Query

    def handle_list_online_users(self, packet: Packet):
        with open(self.database["user"], "r") as f:
            users = json.load(f)
        online_users = [user["username"] for user in users if user["is_online"]]
        return DBListOnlineUsersPacket(True, online_users)

    # Room handler
    # def handle_create_room(self, packet: Packet):
    #     return DBCreateRoomPacket(True, "Room created successfully")

    def get_game_max_players(self, game_id: str):
        with open(self.database["game"], "r") as f:
            games = json.load(f)
        for game in games:
            if game["game_id"] == game_id:
                return game["max_players"]
        return 0

    def get_game_name(self, game_id: str):
        self.logger.info(f"Get game name: {game_id}")
        with open(self.database["game"], "r") as f:
            games = json.load(f)
        for game in games:
            self.logger.info(f"Game id: {game['game_id']}")
            if game["game_id"] == game_id:
                self.logger.info(f"Game name: {game['game_name']}")
                return game["game_name"]
        return ""

    # handle developer auth
    def handle_developer_login(self, packet: Packet):
        username = packet.data["username"]
        password = packet.data["password"]
        with open(self.database["developer"], "r") as f:
            developers = json.load(f)
        for developer in developers:
            if developer["username"] == username and developer["password"] == password:
                developer["is_online"] = True
                developer["last_login"] = datetime.now().isoformat()
                with open(self.database["developer"], "w") as f:
                    json.dump(developers, f, indent=2)
                self.logger.info("Login successful")
                return DBDeveloperLoginPacket(True, "Login successful")

        self.logger.info("Login failed")
        return DBDeveloperLoginPacket(False, "Login failed")

    def handle_developer_register(self, packet: Packet):
        username = packet.data["username"]
        password = packet.data["password"]
        with open(self.database["developer"], "r") as f:
            developers = json.load(f)
        for developer in developers:
            if developer["username"] == username:
                self.logger.info("Username already exists")
                return DBDeveloperRegisterPacket(False, "Username already exists")

        new_developer = {
            "username": username,
            "password": password,
            "is_online": False,
            "last_login": "",
            "created_at": datetime.now().isoformat(),
            "role": "developer",
        }
        developers.append(new_developer)

        with open(self.database["developer"], "w") as f:
            json.dump(developers, f, indent=2)
        self.logger.info("Register successful")
        return DBDeveloperRegisterPacket(True, "Register successful")

    def handle_developer_logout(self, packet: Packet):
        username = packet.data["username"]
        with open(self.database["developer"], "r") as f:
            developers = json.load(f)
        for developer in developers:
            if developer["username"] == username:
                developer["is_online"] = False
                with open(self.database["developer"], "w") as f:
                    json.dump(developers, f, indent=2)
                self.logger.info("Logout successful")
                return DBDeveloperLogoutPacket(True, "Logout successful")

        self.logger.info("Username not found")
        return DBDeveloperLogoutPacket(False, "Username not found")

    def handle_list_developer_games(self, packet: Packet):
        username = packet.data["username"]
        developer_games = []
        with open(self.database["game"], "r") as f:
            games = json.load(f)
        for game in games:
            if game["game_author"] == username:
                developer_games.append(game)
        return ListDeveloperGamesPacket(True, developer_games)
