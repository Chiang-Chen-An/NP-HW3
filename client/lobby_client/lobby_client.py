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
    T_DOWNLOAD_GAME_INIT,
    T_DOWNLOAD_GAME_CHUNK,
    T_DOWNLOAD_GAME_FINISH,
    T_START_GAME,
    T_JOIN_ROOM,
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
from common.Packet.game_extra import (
    DownloadGameInitPacket,
    StartGamePacket,
    JoinRoomPacket,
)
from common.log_utils import setup_logger
from pathlib import Path
import os
import os
import sys
import json
import select
import subprocess
import threading
from common.Packet.game_extra import StartGamePacket


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
                    self.logger.info(f"Logged in as: {self.user_context.username}")
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

        if reply.type == T_GET_GAME_DETAIL and reply.data.get("success", True):
            game = reply.data["game_info"]

            while True:
                print("=" * 50)
                print(f"Game: {game['game_name']} (v{game['game_version']})".center(50))
                print("=" * 50)
                print(f"Author: {game['game_author']}")
                print(f"Description: {game['game_description']}")
                print(f"Max Players: {game.get('max_players', 'N/A')}")
                print(f"Downloads: {game.get('download_count', 0)}")
                
                # Calculate and show average rating
                avg_rating = game.get('average_rating', 0)
                if avg_rating > 0:
                    stars = "★" * int(avg_rating) + "☆" * (5 - int(avg_rating))
                    print(f"Rating: {stars} ({avg_rating:.1f}/5.0)")
                else:
                    print("Rating: No ratings yet")
                
                print("\nReviews:")
                if game["comments"]:
                    for i, comment in enumerate(game["comments"][:5], 1):  # Show latest 5
                        print(f"  {i}. {comment['username']} ({comment['rating']}/5): {comment['comment']}")
                    if len(game["comments"]) > 5:
                        print(f"  ... and {len(game['comments']) - 5} more reviews")
                else:
                    print("  No reviews yet. Be the first to review!")
                
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
                    print("Invalid choice. Please enter 1-4.")
        else:
            print(f"Error: {reply.data.get('message', 'Game not found')}")
            input("Press Enter to continue...")

    def handle_review_game(self, s: socket.socket, game_id: str):
        print("\n--- Write a Review ---")
        score = input("Rating (1-5): ").strip()
        comment = input("Comment: ").strip()

        if not score.isdigit() or not (1 <= int(score) <= 5):
            print("Invalid score. Must be 1-5.")
            return

        packet = GameReviewPacket(game_id, int(score), comment, self.user_context.username)
        s.sendall(packet.to_bytes())

        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return
        if reply.type == T_GAME_REVIEW:
            print("Review submitted successfully!")
        else:
            print(f"Failed: {reply.data.get('message', 'Unknown error')}")

    def handle_personal_center(self, s: socket.socket):
        """Display user's downloaded games and account info"""
        while True:
            print("=" * 50)
            print("PERSONAL CENTER".center(50))
            print("=" * 50)
            print(f"Username: {self.user_context.username}")
            print(f"Downloaded Games: {len(self.users_game)}")
            print("-" * 50)
            
            if len(self.users_game) == 0:
                print("No games downloaded yet.")
                print("\nTip: Go to 'List the available games' to download games!")
            else:
                print(f"{'Game ID':<20} {'Name':<25} {'Version':<10}")
                print("-" * 50)
                for game in self.users_game:
                    print(f"{game['id']:<20} {game['name']:<25} {game['version']:<10}")
            
            print("=" * 50)
            print("1. Back to Main Menu")
            cmd = input("Choose action: ").strip()
            
            if cmd == "1":
                break
            else:
                print("Invalid choice. Press 1 to go back.")

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
        while True:
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
                break

    def handle_create_room(self, s: socket.socket, game_id: str = None):
        if len(self.users_game) == 0 and game_id is None:
            print("=" * 50)
            print("ERROR: No available games".center(50))
            print("=" * 50)
            print("You need to download a game before creating a room.")
            print("Go to 'List the available games' to download.")
            print("=" * 50)
            input("Press Enter to continue...")
            return
        
        print("=" * 50)
        print("CREATE ROOM".center(50))
        print("=" * 50)
        
        # 如果指定了 game_id，檢查是否已下載以及版本
        if game_id is not None:
            local_game = next((g for g in self.users_game if g["id"] == game_id), None)
            
            if not local_game:
                # 遊戲未下載，提示用戶
                print(f"⚠ Game ID '{game_id}' is not downloaded yet.")
                print("\nYou need to download the game before creating a room.")
                choice = input("Download now? (y/n): ").strip().lower()
                
                if choice == 'y':
                    print("\nDownloading game...")
                    self.handle_download_game(s, game_id)
                    
                    # 強制刷新遊戲列表
                    self.users_game = get_games_metadata_json(self.user_context.username)
                    
                    # 重新檢查是否下載成功
                    local_game = next((g for g in self.users_game if g["id"] == game_id), None)
                    
                    if not local_game:
                        print("\n❌ Download failed or cancelled. Cannot create room.")
                        input("Press Enter to continue...")
                        return
                    
                    print("\n✓ Game downloaded successfully!")
                else:
                    print("\n❌ Cannot create room without downloading the game.")
                    input("Press Enter to continue...")
                    return
            
            # 檢查版本是否為最新
            from common.Packet.game import GetGameDetailPacket
            detail_packet = GetGameDetailPacket(game_id)
            s.sendall(detail_packet.to_bytes())
            detail_reply = Packet.receive(s)
            
            if detail_reply and detail_reply.data.get("success"):
                server_version = detail_reply.data.get("game_info", {}).get("game_version")
                local_version = local_game["version"]
                
                if server_version and server_version != local_version:
                    print(f"\n⚠️  Your game version ({local_version}) is outdated!")
                    print(f"   Server version: {server_version}")
                    print(f"   Please update the game to create a room.\n")
                    update_choice = input("Do you want to update now? (y/n): ").strip().lower()
                    if update_choice == 'y':
                        self.handle_download_game(s, game_id)
                        # 重新載入遊戲列表
                        self.users_game = get_games_metadata_json(self.user_context.username)
                        print("\n✓ Game updated!")
                        # 遞迴重新嘗試創建房間
                        return self.handle_create_room(s, game_id)
                    else:
                        print("\n❌ Cannot create room with outdated game version.")
                        input("Press Enter to continue...")
                        return
        
        # 顯示已下載的遊戲列表
        if len(self.users_game) > 0:
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
            
            print("=" * 50)
        
        if game_id is None:
            game_id = input("Enter Game ID (or 'c' to cancel): ").strip()
            if game_id.lower() == 'c':
                return
            
            # Validate game_id
            local_game = None
            for game in self.users_game:
                if game["id"] == game_id:
                    local_game = game
                    break
            
            if not local_game:
                print("=" * 50)
                print(f"ERROR: Game ID '{game_id}' not found in your downloaded games.")
                print("=" * 50)
                input("Press Enter to continue...")
                return
            
            # 檢查版本是否為最新（當從選單輸入 game_id 時）
            from common.Packet.game import GetGameDetailPacket
            detail_packet = GetGameDetailPacket(game_id)
            s.sendall(detail_packet.to_bytes())
            detail_reply = Packet.receive(s)
            
            if detail_reply and detail_reply.data.get("success"):
                server_version = detail_reply.data.get("game_info", {}).get("game_version")
                local_version = local_game["version"]
                
                if server_version and server_version != local_version:
                    print(f"\n⚠️  Your game version ({local_version}) is outdated!")
                    print(f"   Server version: {server_version}")
                    print(f"   Please update the game to create a room.\n")
                    update_choice = input("Do you want to update now? (y/n): ").strip().lower()
                    if update_choice == 'y':
                        self.handle_download_game(s, game_id)
                        # 重新載入遊戲列表
                        self.users_game = get_games_metadata_json(self.user_context.username)
                        print("\n✓ Game updated!")
                        # 遞迴重新嘗試創建房間
                        return self.handle_create_room(s, game_id)
                    else:
                        print("\n❌ Cannot create room with outdated game version.")
                        input("Press Enter to continue...")
                        return
        
        packet = CreateRoomPacket(game_id, self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            print("ERROR: No response from server")
            input("Press Enter to continue...")
            return
        if reply.type == T_CREATE_ROOM and reply.data["success"]:
            self.logger.info("Room created successfully")
            room_id = reply.data["room_id"]
            print(f"\n✓ Room {room_id} created successfully!")
            self.handle_room_loop(s, room_id, is_owner=True)
        else:
            print(f"ERROR: {reply.data.get('message', 'Failed to create room')}")
            input("Press Enter to continue...")

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

            while True:
                print("\n[Room List Menu]")
                print("1. Join Room (Enter ID)")
                print("2. Back to Main Menu")
                choice = input("Select: ").strip()

                if choice == "1":
                    room_id = input("Enter Room ID: ").strip()
                    # 傳遞房間列表給 handle_join_room 以便檢查
                    self.handle_join_room(s, room_id, reply.data["rooms"])
                elif choice == "2":
                    break
                else:
                    print("Invalid choice.")
        else:
            self.logger.info(reply.data["message"])

    def handle_join_room(self, s: socket.socket, room_id: str, rooms_list=None):
        # 檢查是否已下載該房間的遊戲，以及版本是否為最新（client端檢查）
        if rooms_list:
            target_room = next((r for r in rooms_list if r["room_id"] == room_id), None)
            if target_room:
                game_id = target_room["game_id"]
                game_name = target_room.get('game_name', 'Unknown')
                
                # 檢查本地是否已下載該遊戲
                local_game = next((g for g in self.users_game if g["id"] == game_id), None)
                
                if not local_game:
                    print(f"\n❌ You must download game {game_id} ({game_name}) before joining this room.")
                    print(f"Please go to 'List the available games' menu and download game {game_id} first.\n")
                    return
                
                # 檢查版本是否為最新
                # 獲取伺服器上的最新版本資訊
                from common.Packet.game import GetGameDetailPacket
                detail_packet = GetGameDetailPacket(game_id)
                s.sendall(detail_packet.to_bytes())
                detail_reply = Packet.receive(s)
                
                if detail_reply and detail_reply.data.get("success"):
                    server_version = detail_reply.data.get("game_info", {}).get("game_version")
                    local_version = local_game["version"]
                    
                    if server_version and server_version != local_version:
                        print(f"\n⚠️  Your game version ({local_version}) is outdated!")
                        print(f"   Server version: {server_version}")
                        print(f"   Please update game {game_id} ({game_name}) to the latest version.\n")
                        update_choice = input("Do you want to update now? (y/n): ").strip().lower()
                        if update_choice == 'y':
                            self.handle_download_game(s, game_id)
                            # 重新載入遊戲列表
                            self.users_game = get_games_metadata_json(self.user_context.username)
                            print("\n✓ Game updated! You can now join the room.")
                            # 遞迴調用以重新檢查
                            return self.handle_join_room(s, room_id, rooms_list)
                        else:
                            print("\n❌ Cannot join room with outdated game version.\n")
                            return
        
        packet = JoinRoomPacket(room_id, self.user_context.username)
        s.sendall(packet.to_bytes())

        reply = Packet.receive(s)
        if not reply:
            self.logger.error("Failed to receive response")
            return

        if reply.type == T_JOIN_ROOM and reply.data["success"]:
            self.logger.info("Joined room successfully")
            self.handle_room_loop(s, room_id, is_owner=False)
        else:
            self.logger.info(
                f"Join failed: {reply.data.get('message', 'Unknown error')}"
            )

    def handle_download_game(self, s: socket.socket, game_id: str):
        import base64
        import hashlib
        import zipfile
        import shutil

        print("=" * 50)
        print("DOWNLOAD GAME".center(50))
        print("=" * 50)

        # 1. Send Init
        packet = DownloadGameInitPacket(game_id, self.user_context.username)
        s.sendall(packet.to_bytes())

        # 2. Receive Init Reply
        reply = Packet.receive(s)
        if not reply or reply.type != T_DOWNLOAD_GAME_INIT:
            self.logger.error("Failed to receive download init response")
            return

        if not reply.data["success"]:
            self.logger.error(
                f"Download failed: {reply.data.get('message', 'Unknown error')}"
            )
            return

        file_size = reply.data["file_size"]
        game_version = reply.data["game_version"]
        upload_id = reply.data["upload_id"]

        print(
            f"Downloading Game {game_id} (v{game_version})... Size: {file_size} bytes"
        )

        # Prepare download path
        download_dir = os.path.join(
            os.path.dirname(__file__),
            f"download/{self.user_context.username}/{game_id}/v{game_version}",
        )
        self.logger.info(f"Download dir: {download_dir}")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        temp_zip_path = os.path.join(download_dir, "download.zip")

        received_bytes = 0
        with open(temp_zip_path, "wb") as f:
            while received_bytes < file_size:
                packet = Packet.receive(s)
                if not packet:
                    self.logger.error("Connection lost during download")
                    return

                if packet.type == T_DOWNLOAD_GAME_CHUNK:
                    chunk_data = base64.b64decode(packet.data["chunk_data"])
                    f.write(chunk_data)
                    received_bytes += len(chunk_data)
                    self._print_progress_bar(received_bytes, file_size)
                elif packet.type == T_DOWNLOAD_GAME_FINISH:
                    # Premature finish?
                    break
                else:
                    self.logger.error(f"Unexpected packet type: {packet.type}")
                    return

        # Receive Finish Packet (if not already received in loop? Wait, loop condition is size)
        # If we received exactly file_size, the next packet should be FINISH.
        packet = Packet.receive(s)
        if not packet or packet.type != T_DOWNLOAD_GAME_FINISH:
            self.logger.error("Missing finish packet")
            return

        server_checksum = packet.data["checksum"]

        # Verify Checksum
        with open(temp_zip_path, "rb") as f:
            local_checksum = hashlib.md5(f.read()).hexdigest()

        if server_checksum != local_checksum:
            self.logger.error("Checksum mismatch!")
            return

        print("Download complete. Extracting...")

        # Extract
        try:
            with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                zip_ref.extractall(download_dir)
            print("Installation successful!")
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
        finally:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

        # Refresh metadata
        self.users_game = get_games_metadata_json(self.user_context.username)

    def handle_room_loop(self, s: socket.socket, room_id: str, is_owner: bool):
        print("=" * 50)
        print(f"ROOM {room_id}".center(50))
        print("=" * 50)
        print("Waiting for game to start...")
        if is_owner:
            print("Press 's' to start game, 'q' to leave.")
        else:
            print("Press 'q' to leave.")

        while True:
            # Check for input or socket data
            inputs = [s, sys.stdin]
            readable, _, _ = select.select(inputs, [], [])

            for r in readable:
                if r is s:
                    # Receive packet
                    packet = Packet.receive(s)
                    if not packet:
                        print("Connection lost.")
                        return

                    if packet.type == T_START_GAME:
                        # 檢查是否成功
                        if packet.data.get("success") == False:
                            print(f"\n❌ Cannot start game: {packet.data.get('message', 'Unknown error')}\n")
                            continue
                        
                        print("Game Starting!")
                        self._launch_game_client(packet)
                        return  # Exit room loop after game starts? Or stay?
                        # Usually game client takes over screen.
                        # After game, we might return here.
                        # For now, let's return to lobby after game launch.
                    elif packet.type == T_LIST_ROOMS:  # Ignore or handle updates
                        pass
                    else:
                        # Handle other packets (chat?)
                        pass
                elif r is sys.stdin:
                    cmd = sys.stdin.readline().strip()
                    if cmd == "q":
                        # Leave room
                        from common.Packet.game_extra import LeaveRoomPacket
                        leave_packet = LeaveRoomPacket(room_id, self.user_context.username)
                        s.sendall(leave_packet.to_bytes())
                        reply = Packet.receive(s)
                        if reply and reply.data.get("success"):
                            print("✓ Left room successfully")
                        else:
                            print(f"✗ Failed to leave room: {reply.data.get('message', 'Unknown error')}")
                        return
                    if is_owner and cmd == "s":
                        # Start Game
                        packet = Packet(
                            T_START_GAME,
                            {
                                "room_id": room_id,
                                "username": self.user_context.username,
                            },
                        )
                        s.sendall(packet.to_bytes())
                        print("Start request sent...")

    def _launch_game_client(self, packet: StartGamePacket):
        game_id = packet.data["game_id"]
        server_ip = "140.113.17.13"  # 使用伺服器提供的 IP
        server_port = packet.data["server_port"]

        # Find local game path
        # We need to find the version.
        # The packet doesn't contain version.
        # We should assume we have the latest or check metadata.
        # Let's check `self.users_game` to find the version for `game_id`.

        game_meta = next((g for g in self.users_game if g["id"] == game_id), None)
        if not game_meta:
            print(f"Error: Game {game_id} not found locally. Please download it.")
            return

        game_version = game_meta["version"]

        game_dir = os.path.join(
            os.path.dirname(__file__),
            f"download/{self.user_context.username}/{game_id}/v{game_version}",
        )

        client_dir = os.path.join(game_dir, "client")

        # Command
        # Similar to server, check for client.py or main.py
        if os.path.exists(os.path.join(client_dir, "client.py")):
            cmd = ["python3", "client.py", server_ip, str(server_port)]
        elif os.path.exists(os.path.join(client_dir, "main.py")):
            cmd = ["python3", "main.py", server_ip, str(server_port)]
        else:
            print("Error: Game client script not found.")
            return

        print(f"Launching game client: {cmd}")
        print("Waiting for game server to be ready...")
        
        # Give game server time to start
        # 注意：不能連接測試，否則會佔用玩家槽位！
        # 只能等待伺服器啟動
        import time
        time.sleep(2)  # 等待遊戲伺服器啟動
        print("✓ Launching game client...")
        
        try:
            subprocess.run(cmd, cwd=client_dir)
        except Exception as e:
            print(f"Error running game client: {e}")

        print("Game finished.")

    def _print_progress_bar(self, current, total, length=50):
        percent = float(current) * 100 / total
        arrow = "-" * int(percent / 100 * length - 1) + ">"
        spaces = " " * (length - len(arrow))
        print(f"\rProgress: [{arrow}{spaces}] {percent:.2f}%", end="")
        if current >= total:
            print()


def get_games_metadata_json(username):
    base_path = Path(f"./client/lobby_client/download/{username}")
    games_data = []

    if not base_path.exists():
        os.makedirs(base_path)
        return []

    for game_dir in base_path.iterdir():
        if game_dir.is_dir():
            # 使用目錄名稱作為真實的 game_id（數字 ID）
            real_game_id = game_dir.name

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
                    "id": real_game_id,  # 使用目錄名稱（真實的數字 ID）
                    "name": data.get("game_name"),
                    "version": latest_ver_name.lstrip("v"),  # 使用目錄名稱作為版本號（移除 'v' 前綴）
                    "max_players": data.get("max_players", 0),
                }

                games_data.append(game_info)

            except json.JSONDecodeError:
                print(f"錯誤: {config_path} 格式不正確 (不是有效的 JSON)")
            except Exception as e:
                print(f"讀取失敗: {e}")

    return games_data
