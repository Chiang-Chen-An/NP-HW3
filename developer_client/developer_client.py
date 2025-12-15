from common.Packet.developer import (
    DeveloperLoginPacket,
    DeveloperRegisterPacket,
    DeveloperLogoutPacket,
    ListDeveloperGamesPacket,
    UploadGameInitPacket,
    UploadGameChunkPacket,
    UploadGameFinishPacket,
    UpdateGameInitPacket,
    UpdateGameChunkPacket,
    UpdateGameFinishPacket,
)
from common.type import (
    T_DEVELOPER_LOGIN,
    T_DEVELOPER_REGISTER,
    T_DEVELOPER_LOGOUT,
    T_LIST_DEVELOPER_GAMES,
    T_UPLOAD_GAME_INIT,
    T_UPLOAD_GAME_FINISH,
    T_UPDATE_GAME_INIT,
    T_UPDATE_GAME_FINISH,
    T_DELETE_GAME,
)
from common.Packet.developer_extra import DeleteGamePacket
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
            print("3. Update a game")
            print("4. Delete a game")
            print("5. Logout")
            command = input("Enter command (1 ~ 5): ").strip()
            if command == "1":
                self.handle_list_games(s)
            elif command == "2":
                self.handle_upload_game(s)
            elif command == "3":
                self.handle_update_game(s)
            elif command == "4":
                self.handle_delete_game(s)
            elif command == "5":
                if self.handle_logout(s):
                    break
            else:
                self.logger.info("Invalid command")
                print("Invalid command. Please enter 1-5.")

    def handle_list_games(self, s: socket.socket):
        packet = ListDeveloperGamesPacket(self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            print("ERROR: Failed to receive response from server")
            input("Press Enter to continue...")
            return
        if reply.type == T_LIST_DEVELOPER_GAMES and reply.data["success"]:
            games = reply.data["games"]
            print("=" * 50)
            print("MY GAMES".center(50))
            print("=" * 50)
            
            if not games:
                print("You haven't uploaded any games yet.")
                print("\nTip: Select 'Upload a new game' to add your first game!")
                print("=" * 50)
            else:
                for i, game in enumerate(games, 1):
                    print(f"\n[Game {i}]")
                    print(f"Game ID: {game['game_id']}")
                    print(f"Game Name: {game['game_name']}")
                    print(f"Description: {game['game_description']}")
                    print(f"Version: {game['game_version']}")
                    print(f"Downloads: {game['download_count']}")
                    
                    # Calculate average rating if comments exist
                    if game['comments']:
                        avg_rating = sum(c['rating'] for c in game['comments']) / len(game['comments'])
                        print(f"Rating: {avg_rating:.1f}/5.0 ({len(game['comments'])} reviews)")
                    else:
                        print(f"Rating: No reviews yet")
                    
                    print(f"Created: {game['game_created_at']}")
                    print("-" * 50)
                print(f"\nTotal: {len(games)} game(s)")
                print("=" * 50)
            
            input("Press Enter to continue...")
        else:
            self.logger.info(reply.data.get("message", "Failed to list games"))
            print(f"ERROR: {reply.data.get('message', 'Failed to list games')}")
            input("Press Enter to continue...")

    def handle_upload_game(self, s: socket.socket):
        print("=" * 50)
        print("UPLOAD GAME".center(50))
        print("=" * 50)
        game_name = " "
        game_description = " "
        game_file_path = input("Game File Path: ").strip()

        if not self._validate_game_folder(game_file_path):
            return

        zip_path = self._zip_game_folder(game_file_path)
        if not zip_path:
            return

        try:
            file_size = os.path.getsize(zip_path)

            # 1. Send Init Packet
            packet = UploadGameInitPacket(
                self.user_context.username, game_name, game_description, file_size
            )
            s.sendall(packet.to_bytes())

            reply = Packet.receive(s)
            if (
                not reply
                or reply.type != T_UPLOAD_GAME_INIT
                or not reply.data["success"]
            ):
                self.logger.error(
                    f"Upload init failed: {reply.data.get('message', 'Unknown error')}"
                )
                return

            upload_id = reply.data["upload_id"]

            # 2. Send Chunks
            self._send_file_chunks(s, zip_path, upload_id, file_size, is_update=False)

            # 3. Send Finish Packet
            import hashlib

            with open(zip_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            packet = UploadGameFinishPacket(upload_id, file_hash)
            s.sendall(packet.to_bytes())

            reply = Packet.receive(s)
            self.logger.info(
                f"Received reply: {reply.type if reply else 'None'} - {reply.data if reply else 'None'}"
            )
            if reply and reply.type == T_UPLOAD_GAME_FINISH and reply.data["success"]:
                self.logger.info(reply.data["message"])
                game_id = reply.data.get("game_id", "N/A")
                print("\n" + "=" * 50)
                print("✓ UPLOAD SUCCESSFUL".center(50))
                print("=" * 50)
                print(f"Game '{game_name}' has been uploaded successfully!")
                print(f"System assigned Game ID: {game_id}")
                print("Players can now download and play your game.")
                print("=" * 50)
            else:
                self.logger.error(
                    f"Upload finish failed: {reply.data.get('message', 'Unknown error') if reply else 'No reply'}"
                )
                print(f"\nERROR: {reply.data.get('message', 'Unknown error') if reply else 'No reply'}")
            input("Press Enter to continue...")

        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def handle_update_game(self, s: socket.socket):
        print("=" * 50)
        print("UPDATE GAME".center(50))
        print("=" * 50)
        
        # 先列出開發者的遊戲
        packet = ListDeveloperGamesPacket(self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        
        if not reply or reply.type != T_LIST_DEVELOPER_GAMES or not reply.data["success"]:
            print("ERROR: Failed to retrieve your games")
            input("Press Enter to continue...")
            return
        
        my_games = reply.data["games"]
        
        if not my_games:
            print("You haven't uploaded any games yet.")
            print("Upload a game first before trying to update.")
            input("Press Enter to continue...")
            return
        
        # 顯示開發者的遊戲列表
        print("\nYour Games:")
        for i, game in enumerate(my_games, 1):
            print(f"{i}. ID: {game['game_id']} | Name: {game['game_name']} | Version: {game['game_version']}")
        print()
        
        game_id = input("Game ID to update: ").strip()
        
        # 驗證 game_id 是否屬於該開發者
        current_game = None
        for game in my_games:
            if game['game_id'] == game_id:
                current_game = game
                break
        
        if not current_game:
            print(f"\n❌ ERROR: Game ID '{game_id}' does not exist or does not belong to you.")
            print("You can only update games that you have uploaded.")
            input("Press Enter to continue...")
            return
        
        game_file_path = input("Game File Path: ").strip()

        if not self._validate_game_folder(game_file_path):
            return
        
        # 從 config.json 讀取新版本
        config_path = os.path.join(game_file_path, "config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            game_version = config.get("game_version")
            if not game_version:
                print("\n❌ ERROR: 'game_version' field not found in config.json")
                input("Press Enter to continue...")
                return
        except Exception as e:
            print(f"\n❌ ERROR: Failed to read config.json: {e}")
            input("Press Enter to continue...")
            return
        
        # 檢查版本是否不同且更新
        current_version = current_game['game_version']
        if game_version == current_version:
            print(f"\n❌ ERROR: New version ({game_version}) is the same as current version ({current_version})")
            print("Please update the version in config.json before uploading.")
            input("Press Enter to continue...")
            return
        
        # 簡單的版本比較（假設使用語義版本 x.y.z）
        if not self._is_version_newer(game_version, current_version):
            print(f"\n❌ ERROR: New version ({game_version}) is not newer than current version ({current_version})")
            print("The new version must be greater than the current version.")
            input("Press Enter to continue...")
            return
        
        print(f"\n✓ Version check passed: {current_version} → {game_version}")

        zip_path = self._zip_game_folder(game_file_path)
        if not zip_path:
            return

        try:
            file_size = os.path.getsize(zip_path)

            # 1. Send Init Packet
            packet = UpdateGameInitPacket(
                self.user_context.username, game_id, game_version, file_size
            )
            s.sendall(packet.to_bytes())

            reply = Packet.receive(s)
            if (
                not reply
                or reply.type != T_UPDATE_GAME_INIT
                or not reply.data["success"]
            ):
                self.logger.error(
                    f"Update init failed: {reply.data.get('message', 'Unknown error')}"
                )
                return

            upload_id = reply.data["upload_id"]

            # 2. Send Chunks
            self._send_file_chunks(s, zip_path, upload_id, file_size, is_update=True)

            # 3. Send Finish Packet
            import hashlib

            with open(zip_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            packet = UpdateGameFinishPacket(upload_id, file_hash)
            s.sendall(packet.to_bytes())

            reply = Packet.receive(s)
            if reply and reply.type == T_UPDATE_GAME_FINISH and reply.data["success"]:
                self.logger.info(reply.data["message"])
                print("\n" + "=" * 50)
                print("✓ UPDATE SUCCESSFUL".center(50))
                print("=" * 50)
                print(f"Game '{game_id}' updated to version {game_version}!")
                print("Players will be prompted to update when they next launch the game.")
                print("=" * 50)
            else:
                self.logger.error(
                    f"Update finish failed: {reply.data.get('message', 'Unknown error')}"
                )
                print(f"\nERROR: {reply.data.get('message', 'Unknown error')}")
            input("Press Enter to continue...")

        except Exception as e:
            self.logger.error(f"Update failed: {e}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def _validate_game_folder(self, path: str) -> bool:
        if not os.path.isdir(path):
            self.logger.error("Path is not a directory")
            print(f"ERROR: '{path}' is not a valid directory")
            input("Press Enter to continue...")
            return False

        required_items = ["config.json", "client", "server"]
        for item in required_items:
            if not os.path.exists(os.path.join(path, item)):
                self.logger.error(f"Missing required item: {item}")
                print(f"ERROR: Missing required item: {item}")
                print("\nGame folder must contain:")
                print("  - config.json")
                print("  - client/ (directory)")
                print("  - server/ (directory)")
                input("Press Enter to continue...")
                return False
        return True
    
    def _is_version_newer(self, new_version: str, current_version: str) -> bool:
        """
        比較兩個版本號，判斷 new_version 是否比 current_version 新
        支援格式：x.y.z (例如: 1.0.0, 1.2.3)
        """
        try:
            # 將版本號分割成數字列表
            new_parts = [int(x) for x in new_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]
            
            # 補齊長度
            max_len = max(len(new_parts), len(current_parts))
            new_parts += [0] * (max_len - len(new_parts))
            current_parts += [0] * (max_len - len(current_parts))
            
            # 逐位比較
            for i in range(max_len):
                if new_parts[i] > current_parts[i]:
                    return True
                elif new_parts[i] < current_parts[i]:
                    return False
            
            # 完全相同
            return False
        except (ValueError, AttributeError):
            # 如果無法解析版本號，使用字串比較
            return new_version > current_version

    def _zip_game_folder(self, path: str) -> str:
        import shutil

        try:
            # Create a temporary zip file
            base_name = os.path.join(os.getcwd(), "temp_game_upload")
            zip_path = shutil.make_archive(base_name, "zip", path)
            return zip_path
        except Exception as e:
            self.logger.error(f"Failed to zip folder: {e}")
            return ""

    def _send_file_chunks(
        self,
        s: socket.socket,
        file_path: str,
        upload_id: str,
        file_size: int,
        is_update: bool,
    ):
        import base64
        import math

        chunk_size = 4096  # 4KB chunks
        total_chunks = math.ceil(file_size / chunk_size)
        sent_bytes = 0

        with open(file_path, "rb") as f:
            for i in range(total_chunks):
                chunk = f.read(chunk_size)
                encoded_chunk = base64.b64encode(chunk).decode("utf-8")

                if is_update:
                    packet = UpdateGameChunkPacket(upload_id, encoded_chunk)
                else:
                    packet = UploadGameChunkPacket(upload_id, encoded_chunk)

                s.sendall(packet.to_bytes())

                sent_bytes += len(chunk)
                self._print_progress_bar(sent_bytes, file_size)

    def _print_progress_bar(self, current, total, length=50):
        percent = float(current) * 100 / total
        arrow = "-" * int(percent / 100 * length - 1) + ">"
        spaces = " " * (length - len(arrow))
        print(f"\rProgress: [{arrow}{spaces}] {percent:.2f}%", end="")
        if current >= total:
            print()

    def handle_delete_game(self, s: socket.socket):
        print("=" * 50)
        print("DELETE GAME".center(50))
        print("=" * 50)
        game_id = input("Game ID: ").strip()

        packet = DeleteGamePacket(game_id, self.user_context.username)
        s.sendall(packet.to_bytes())

        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return

        if reply.type == T_DELETE_GAME and reply.data["success"]:
            self.logger.info(reply.data["message"])
            print(f"✓ {reply.data['message']}")
        else:
            self.logger.error(
                f"Delete failed: {reply.data.get('message', 'Unknown error')}"
            )
            print(f"ERROR: {reply.data.get('message', 'Unknown error')}")
        input("Press Enter to continue...")

    def handle_logout(self, s: socket.socket):
        packet = DeveloperLogoutPacket(self.user_context.username)
        s.sendall(packet.to_bytes())
        reply = Packet.receive(s)
        if reply is None:
            self.logger.error("Failed to receive response from server")
            return False
        if reply.type == T_DEVELOPER_LOGOUT and reply.data.get("success", False):
            self.logger.info("Logout successful")
            print("✓ Logged out successfully")
            self.user_context = None
            return True
        else:
            self.logger.info(reply.data.get("message", "Logout failed"))
            return False
