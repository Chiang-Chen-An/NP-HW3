import socket
from common.packet import Packet
from common.type import (
    T_LOGIN,
    T_REGISTER,
    T_LOGOUT,
    T_LIST_GAMES,
    T_GET_GAME_DETAIL,
    T_GAME_REVIEW,
    T_LIST_ONLINE_USERS,
    T_LIST_ROOMS,
    T_CREATE_ROOM,
)
from common.Packet.user import (
    LoginPacket,
    RegisterPacket,
    LogoutPacket,
    ListOnlineUsersPacket,
)
from common.Packet.game import (
    ListGamesPacket,
    GetGameDetailPacket,
    GameReviewPacket,
    ListRoomsPacket,
    CreateRoomPacket,
)
from common.log_utils import setup_logger
from pathlib import Path
import os
import json


class UserContext:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class LobbyClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.user_context = None
        self.users_game = {}
        self.logger = setup_logger("LobbyClient", "./logs/lobby_client.log")

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
                packet = LoginPacket(username, password)
                s.sendall(packet.to_bytes())
                reply = Packet.receive(s)
                if reply is None:
                    self.logger.error("Failed to receive response from server")
                    return
                if reply.type == T_LOGIN and reply.data["success"]:
                    self.logger.info(reply.data["message"])
                    self.user_context = UserContext(username, password)
                    self.users_game = get_games_metadata_json(username)

                    return
                else:
                    self.logger.info(reply.data["message"])
            elif command == "2":
                print("=" * 50)
                print("REGISTER".center(50))
                print("=" * 50)
                username = input("Username: ").strip()
                password = input("Password: ").strip()
                packet = RegisterPacket(username, password)
                s.sendall(packet.to_bytes())
                reply = Packet.receive(s)
                if reply is None:
                    self.logger.error("Failed to receive response from server")
                    return
                if reply.type == T_REGISTER and reply.data["success"]:
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
            print(f"Welcome to the Lobby! {self.user_context.username}".center(50))
            print("=" * 50)
            print("1. List the available games")
            print("2. List online users")
            print("3. Play game")
            print("4. Personal center")
            print("5. Logout")
            command = input("Enter command (1 ~ 5): ").strip()
            if command == "1":
                self.handle_list_games(s)
            elif command == "2":
                self.handle_list_online_users(s)
            elif command == "3":
                self.handle_play_game(s)
            elif command == "4":
                self.handle_personal_center(s)
            elif command == "5":
                if self.handle_logout(s):
                    break
            else:
                self.logger.info("Invalid command")

    def handle_list_games(self, s: socket.socket):
        packet = ListGamesPacket()
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return

        if reply.type == T_LIST_GAMES:
            games = reply.data["games"]
            print("=" * 50)
            if not games:
                print("No games available.")
                print("=" * 50)
                return

            print(f"{'ID':<5} {'Name':<20} {'Author':<15} {'Rating':<5}")
            print("-" * 50)
            for game in games:
                rating = game.get("average_rating", "N/A")
                print(
                    f"{game['game_id']:<5} {game['game_name']:<20} {game['game_author']:<15} {rating:<5}"
                )
                print("-" * 50)
            print("=" * 50)

            while True:
                print("\n[Game List Menu]")
                print("1. View Game Details (Enter ID)")
                print("2. Back to Main Menu")
                choice = input("Select: ").strip()

                if choice == "1":
                    game_id = input("Enter Game ID: ").strip()
                    self.handle_game_detail(s, game_id)
                elif choice == "2":
                    break
                else:
                    print("Invalid choice.")
        else:
            self.logger.info(reply.data["message"])

    def handle_game_detail(self, s: socket.socket, game_id: str):
        packet = GetGameDetailPacket(game_id)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return

        if reply.type == T_GET_GAME_DETAIL:
            game = reply.data["game_info"]

            while True:
                print("=" * 50)
                print(f"Game: {game['game_name']} (v{game['game_version']})")
                print(f"Description: {game['game_description']}")
                print("Comments: ")
                for comment in game["comments"]:
                    print(
                        f"  {comment['username']} {comment['rating']}/5: {comment['comment']}"
                    )
                print("=" * 50)
                print("1. Download Game")
                print("2. Create Room (Play)")
                print("3. Write a Review / Rate")
                print("4. Back to List")

                cmd = input("Choose action: ").strip()

                if cmd == "1":
                    self.handle_download_game(s, game_id)
                elif cmd == "2":
                    self.handle_create_room(s, game_id)
                elif cmd == "3":
                    self.handle_review_game(s, game_id)
                elif cmd == "4":
                    break
        else:
            print(f"Error: {reply.data.get('message', 'Game not found')}")

    def handle_review_game(self, s: socket.socket, game_id: str):
        print("\n--- Write a Review ---")
        score = input("Rating (1-5): ").strip()
        comment = input("Comment: ").strip()

        if not score.isdigit() or not (1 <= int(score) <= 5):
            print("Invalid score. Must be 1-5.")
            return

        packet = ReviewGamePacket(game_id, int(score), comment)
        s.sendall(packet.to_bytes())

        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return
        if reply.type == T_GAME_REVIEW:
            print("Review submitted successfully!")
        else:
            print(f"Failed: {reply.data['message']}")

    def handle_list_online_users(self, s: socket.socket):
        packet = ListOnlineUsersPacket()
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return
        if reply.type == T_LIST_ONLINE_USERS:
            self.logger.info("List Online Users")
            if len(reply.data["online_users"]) == 0:
                print("=" * 50)
                print("No online users")
                print("=" * 50)
                return
            print("=" * 50)
            for user in reply.data["online_users"]:
                print(f"User: {user}")
                print("=" * 50)
        else:
            self.logger.info(reply.data["message"])

    def handle_logout(self, s: socket.socket):
        packet = LogoutPacket(self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return False
        if reply.type == T_LOGOUT:
            self.logger.info("Logout successful")
            self.user_context = None
            return True
        else:
            self.logger.info(reply.data["message"])
            return False

    def handle_play_game(self, s: socket.socket):
        print("=" * 50)
        print("PLAY GAME".center(50))
        print("=" * 50)
        print("1. Create Room")
        print("2. List All Rooms")
        print("3. Back to Main Menu")
        cmd = input("Choose action: ").strip()
        if cmd == "1":
            self.handle_create_room(s)
        elif cmd == "2":
            self.handle_list_rooms(s)
        elif cmd == "3":
            return

    def handle_create_room(self, s: socket.socket):
        if len(self.users_game) == 0:
            print("=" * 50)
            print("No available games, please download games first")
            print("=" * 50)
            return
        print("=" * 50)
        print("CREATE ROOM".center(50))
        print("=" * 50)
        print(
            f"{'ID':^{5}} | "
            f"{'Name':^{15}} | "
            f"{'Ver.':^{10}} | "
            f"{'Max Players':^{11}}"
        )

        print("-" * 50)

        for game in self.users_game:
            name = game["name"]
            if len(name) > 20:
                name = name[: 20 - 2] + ".."

            print(
                f"{game['id']:^{5}} | "
                f"{name:^{15}} | "
                f"{game['version']:^{10}} | "
                f"{str(game['max_players']):^{11}}",
                sep="",
            )
        game_id = input("Enter Game ID: ").strip()
        for game in self.users_game:
            if game["id"] == game_id:
                break
        else:
            print("Invalid game ID")
            return
        packet = CreateRoomPacket(game_id, self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return
        if reply.type == T_CREATE_ROOM and reply.data["success"]:
            self.logger.info("Room created successfully")
        else:
            self.logger.info(reply.data["message"])

    def handle_list_rooms(self, s: socket.socket):
        packet = ListRoomsPacket()
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return
        if reply.type == T_LIST_ROOMS and reply.data["success"]:
            self.logger.info("List Rooms")
            if len(reply.data["rooms"]) == 0:
                print("=" * 50)
                print("No rooms".center(50))
                print("=" * 50)
                return
            print("=" * 50)
            print(
                f"{'ID':^{3}} | "
                f"{'Game':^{11}} | "
                f"{'Owner':^{8}} | "
                f"{'Players':^{8}} | "
                f"{'Status':^{8}}"
            )
            print("-" * 50)

            for room in reply.data["rooms"]:

                g_name = room["game_name"]
                if len(g_name) > 11:
                    g_name = g_name[: 11 - 2] + ".."

                current_players = len(room["players"])
                p_count_str = f"{current_players}/{room['max_players']}"

                status_str = "Running" if room["is_started"] else "Waiting"

                print(
                    f"{room['room_id']:^{3}} | "
                    f"{g_name:^{11}} | "
                    f"{room['room_owner']:^{8}} | "
                    f"{p_count_str:^{8}} | "
                    f"{status_str:^{8}}"
                )
            print("=" * 50)
            # TODO: add join room
        else:
            self.logger.info(reply.data["message"])


def get_games_metadata_json(username):
    base_path = Path(f"./client/lobby_client/download/{username}")
    games_data = []

    if not base_path.exists():
        os.makedirs(base_path)
        return []

    for game_dir in base_path.iterdir():
        if game_dir.is_dir():

            parsed_versions = []
            for ver_dir in game_dir.iterdir():
                if ver_dir.is_dir():
                    dirname = ver_dir.name
                    try:
                        clean_name = dirname.lstrip("v")
                        parts = [int(p) for p in clean_name.split(".")]
                        parsed_versions.append((tuple(parts), dirname, ver_dir))
                    except ValueError:
                        continue

            if not parsed_versions:
                continue
            _, latest_ver_name, latest_ver_path = max(
                parsed_versions, key=lambda x: x[0]
            )

            config_path = latest_ver_path / "config.json"

            if not config_path.exists():
                print(f"警告: 在 {latest_ver_name} 中找不到 config.json")
                continue

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                game_info = {
                    "id": data.get("game_id"),
                    "name": data.get("game_name"),
                    "version": data.get("game_version", latest_ver_name),
                    "max_players": data.get("max_players", 0),
                }

                games_data.append(game_info)

            except json.JSONDecodeError:
                print(f"錯誤: {config_path} 格式不正確 (不是有效的 JSON)")
            except Exception as e:
                print(f"讀取失敗: {e}")

    return games_data
