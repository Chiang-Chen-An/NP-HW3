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
    T_END_GAME,
    T_LIST_ROOMS,
    T_DOWNLOAD_GAME_INIT,
    T_DOWNLOAD_GAME_CHUNK,
    T_DOWNLOAD_GAME_FINISH,
)
from common.Packet.game import ListRoomsPacketReply, CreateRoomPacketReply
from common.Packet.game_extra import (
    DownloadGameInitPacket,
    DownloadGameChunkPacket,
    DownloadGameFinishPacket,
    StartGamePacket,
    JoinRoomPacket,
    LeaveRoomPacket,
)
from ..database_server.database_server import DatabaseServer
import socket
import threading
import os
import subprocess
import json
import base64
import hashlib
import math


class LobbyServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.logger = setup_logger("lobby_server", "logs/lobby_server.log")
        self.user_context = []  # List of UserContext
        self.room_context = []  # List of RoomContext
        self.database_server = DatabaseServer()
        self.game_servers = {}  # {room_id: subprocess.Popen}

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        self.logger.info(f"Lobby server started on {self.host}:{self.port}")
        try:
            while True:
                client, addr = server.accept()
                threading.Thread(target=self._handle_client, args=(client, addr)).start()
        finally:
            # 服務器關閉時登出所有用戶
            self.logger.info("Server shutting down, logging out all users...")
            for user in self.user_context[:]:
                try:
                    from common.Packet.user import LogoutPacket
                    logout_packet = LogoutPacket(user.username)
                    self.database_server.handle_logout(logout_packet)
                    self.logger.info(f"Logged out user: {user.username}")
                except Exception as e:
                    self.logger.error(f"Failed to logout user {user.username}: {e}")
            self.user_context.clear()
            self.room_context.clear()
            server.close()
            self.logger.info("Server shutdown complete")

    def _handle_client(self, client: socket.socket, addr: tuple[str, int]):
        self.logger.info(f"Client connected: {addr}")
        current_username = None
        try:
            while True:
                packet = Packet.receive(client)
                if packet is None:
                    self.logger.info(f"Client disconnected: {addr}")
                    break
                
                # 記錄當前用戶名（用於斷線時登出）
                if packet.type == T_LOGIN and packet.data.get("username"):
                    current_username = packet.data["username"]
                
                self._handle_packet(client, addr, packet)
        finally:
            # 用戶斷線時自動登出
            if current_username:
                self._handle_user_disconnect(current_username)
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
            self.logger.info(f"Game detail: {reply.data['game_info']}")
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
        elif packet.type == T_DOWNLOAD_GAME_INIT:
            self._handle_download_game(client, addr, packet)
        elif packet.type == T_START_GAME:
            self._handle_start_game(client, addr, packet)
        elif packet.type == T_JOIN_ROOM:
            self._handle_join_room(client, addr, packet)
        elif packet.type == T_LEAVE_ROOM:
            self._handle_leave_room(client, addr, packet)
        else:
            self.logger.info(f"Invalid packet type: {packet.type}")

    def _handle_create_room(
        self, client: socket.socket, addr: tuple[str, int], packet: Packet
    ):
        self.logger.info(f"Client {addr} created a room")
        username = packet.data["username"]
        game_id = packet.data["game_id"]
        room_id = (
            str(int(self.room_context[-1].room_id) + 1) if self.room_context else "1"
        )
        max_players = self.database_server.get_game_max_players(game_id)
        new_room_context = RoomContext(room_id, game_id, max_players, username)
        self.room_context.append(new_room_context)
        reply = CreateRoomPacketReply(True, room_id)
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

    def _handle_download_game(self, client, addr, packet):
        import os
        import zipfile
        import shutil

        game_id = packet.data["game_id"]
        username = packet.data["username"]

        # 1. Find game path
        # We need to find the latest version of the game.
        # Query DB for version?
        # self.database_server.handle_get_game_detail returns game info.
        # Let's use that.
        # But we need to construct a packet to call it, or just access DB directly?
        # Accessing DB directly is easier since we have the instance.

        # Helper to get game info
        game_info = None
        with open(self.database_server.database["game"], "r") as f:
            import json

            games = json.load(f)
            for game in games:
                if game["game_id"] == game_id:
                    game_info = game
                    break

        if not game_info:
            reply = Packet(
                T_DOWNLOAD_GAME_INIT, {"success": False, "message": "Game not found"}
            )
            client.sendall(reply.to_bytes())
            return

        game_version = game_info["game_version"]

        # Path to storage
        storage_dir = os.path.join(
            os.path.dirname(__file__), f"../storage/{game_id}/{game_version}"
        )

        if not os.path.exists(storage_dir):
            reply = Packet(
                T_DOWNLOAD_GAME_INIT,
                {"success": False, "message": "Game files not found on server"},
            )
            client.sendall(reply.to_bytes())
            return

        # Zip the folder to send it
        # We create a temp zip
        temp_zip_path = os.path.join(
            os.path.dirname(__file__), f"temp_download_{game_id}_{username}.zip"
        )
        try:
            shutil.make_archive(temp_zip_path.replace(".zip", ""), "zip", storage_dir)

            if not os.path.exists(temp_zip_path):
                # make_archive might append .zip if not present in base_name, but I handled it?
                # shutil.make_archive("foo", "zip") -> foo.zip
                pass

            file_size = os.path.getsize(temp_zip_path)

            # Send Init
            reply = Packet(
                T_DOWNLOAD_GAME_INIT,
                {
                    "success": True,
                    "file_size": file_size,
                    "game_version": game_version,
                    "upload_id": "download_session",  # Dummy
                },
            )
            client.sendall(reply.to_bytes())

            # Send Chunks
            chunk_size = 4096
            total_chunks = math.ceil(file_size / chunk_size)

            with open(temp_zip_path, "rb") as f:
                for i in range(total_chunks):
                    chunk = f.read(chunk_size)
                    encoded_chunk = base64.b64encode(chunk).decode("utf-8")
                    chunk_packet = DownloadGameChunkPacket(
                        "download_session", encoded_chunk
                    )
                    client.sendall(chunk_packet.to_bytes())

            # Calculate Checksum
            with open(temp_zip_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # Send Finish
            finish_packet = DownloadGameFinishPacket("download_session", file_hash)
            client.sendall(finish_packet.to_bytes())
            
            # 增加下載計數
            self.database_server.increment_download_count(game_id)
            self.logger.info(f"Download count incremented for game {game_id}")

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            # Try to send error if possible, but stream might be broken
        finally:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

    def _handle_start_game(self, client, addr, packet):
        room_id = packet.data.get("room_id")
        username = packet.data.get("username")

        # Find room
        room = next((r for r in self.room_context if r.room_id == room_id), None)
        if not room:
            # Send error
            error_packet = Packet(
                T_START_GAME,
                {"success": False, "message": "Room not found"}
            )
            client.sendall(error_packet.to_bytes())
            return

        if room.room_owner != username:
            # Not owner
            error_packet = Packet(
                T_START_GAME,
                {"success": False, "message": "Only room owner can start the game"}
            )
            client.sendall(error_packet.to_bytes())
            return

        # 檢查玩家人數是否足夠
        if len(room.players) < room.max_players:
            error_packet = Packet(
                T_START_GAME,
                {
                    "success": False, 
                    "message": f"Not enough players. Need {room.max_players} players, currently have {len(room.players)}"
                }
            )
            client.sendall(error_packet.to_bytes())
            self.logger.info(f"Game start denied: room {room_id} has {len(room.players)}/{room.max_players} players")
            return

        # Launch Game Server
        # We need to find the game path.
        game_id = room.game_id

        # Get version from DB or assume latest?
        # We should store version in RoomContext?
        # RoomContext currently: room_id, game_id, max_players, room_owner.
        # It doesn't have version.
        # Let's query DB for latest version.
        game_version = "1.0.0"  # Default
        with open(self.database_server.database["game"], "r") as f:
            games = json.load(f)
            for game in games:
                if game["game_id"] == game_id:
                    game_version = game["game_version"]
                    break

        storage_dir = os.path.join(
            os.path.dirname(__file__), f"../storage/{game_id}/{game_version}"
        )

        server_executable = os.path.join(
            storage_dir, "server/server"
        )  # Assuming binary name?
        # Or read config.json to find start command.
        config_path = os.path.join(storage_dir, "config.json")
        server_cmd = []

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                # config.json spec? "server": "python server.py" or similar?
                # Let's assume standard: "server_script": "server.py" or similar.
                # Spec says: "統一的遊戲規格（例如檔案結構、啟動方式...）"
                # Let's assume `server/main.py` or similar and we run it with python?
                # Or `server/server` executable.
                # Let's look at `config.json` structure if possible.
                # I don't have a sample config.json.
                # I'll assume `server/server.py` and run with python3.
                pass

        # For now, let's assume we run `python3 server/server.py` in the game directory.
        # And we need to pass a port.
        # We need to allocate a port.
        import socket

        def get_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                return s.getsockname()[1]

        game_port = get_free_port()

        # Command to run
        # We should run it in the `server` directory of the game.
        game_server_dir = os.path.join(storage_dir, "server")

        # Check if python file exists
        # 使用 0.0.0.0 讓遊戲伺服器監聽所有網路介面
        game_server_host = "0.0.0.0"
        if os.path.exists(os.path.join(game_server_dir, "server.py")):
            cmd = ["python3", "server.py", game_server_host, str(game_port)]
        elif os.path.exists(os.path.join(game_server_dir, "main.py")):
            cmd = ["python3", "main.py", game_server_host, str(game_port)]
        else:
            # Fallback or error
            self.logger.error("Game server script not found")
            return

        try:
            self.logger.info(f"Starting game server: {cmd} at {game_server_dir}")
            game_proc = subprocess.Popen(cmd, cwd=game_server_dir)
            
            # 追蹤遊戲伺服器進程
            self.game_servers[room_id] = game_proc
            
            # 啟動監控線程，當遊戲結束時刪除房間
            threading.Thread(
                target=self._monitor_game_server,
                args=(room_id, game_proc),
                daemon=True
            ).start()

            # Give the game server time to start listening
            import time
            time.sleep(2)  # 增加等待時間，確保遊戲伺服器完全啟動

            room.is_started = True

            # Notify all players
            # 創建啟動封包
            start_packet = StartGamePacket(room_id, game_id, self.host, game_port)
            
            # 記錄房間玩家資訊
            self.logger.info(f"Room {room_id} has {len(room.players)} players: {room.players}")

            # 發送給房主（使用當前連接的 client socket）
            try:
                client.sendall(start_packet.to_bytes())
                self.logger.info(f"Sent start packet to room owner {username}")
            except Exception as e:
                self.logger.error(f"Failed to send start packet to {username}: {e}")
            
            # 發送給其他玩家（從 user_context 查找）
            for player_name in room.players:
                if player_name != username:  # 跳過房主，已經發送過了
                    user_ctx = next(
                        (u for u in self.user_context if u.username == player_name), None
                    )
                    if user_ctx:
                        try:
                            user_ctx.socket.sendall(start_packet.to_bytes())
                            self.logger.info(f"Sent start packet to player {player_name}")
                        except Exception as e:
                            self.logger.error(
                                f"Failed to send start packet to {player_name}: {e}"
                            )

        except Exception as e:
            self.logger.error(f"Failed to launch game server: {e}")

    def _monitor_game_server(self, room_id: str, game_proc):
        """監控遊戲伺服器進程，遊戲結束後刪除房間"""
        try:
            # 等待遊戲伺服器進程結束
            game_proc.wait()
            self.logger.info(f"Game server for room {room_id} has ended")
            
            # 從追蹤列表移除
            if room_id in self.game_servers:
                del self.game_servers[room_id]
            
            # 刪除房間
            room = next((r for r in self.room_context if r.room_id == room_id), None)
            if room:
                self.room_context.remove(room)
                self.logger.info(f"Room {room_id} deleted after game ended")
            
        except Exception as e:
            self.logger.error(f"Error monitoring game server for room {room_id}: {e}")

    def _handle_join_room(self, client, addr, packet):
        room_id = packet.data["room_id"]
        username = packet.data["username"]

        room = next((r for r in self.room_context if r.room_id == room_id), None)
        if not room:
            reply = Packet(T_JOIN_ROOM, {"success": False, "message": "Room not found"})
            client.sendall(reply.to_bytes())
            return

        if len(room.players) >= room.max_players:
            reply = Packet(T_JOIN_ROOM, {"success": False, "message": "Room full"})
            client.sendall(reply.to_bytes())
            return

        if username in room.players:
            reply = Packet(
                T_JOIN_ROOM, {"success": False, "message": "Already in room"}
            )
            client.sendall(reply.to_bytes())
            return

        room.players.append(username)
        self.logger.info(f"Player {username} joined room {room_id} (now {len(room.players)}/{room.max_players} players)")
        reply = Packet(
            T_JOIN_ROOM, {"success": True, "message": "Joined room successfully"}
        )
        client.sendall(reply.to_bytes())

    def _handle_leave_room(self, client, addr, packet):
        """處理玩家離開房間"""
        room_id = packet.data["room_id"]
        username = packet.data["username"]

        room = next((r for r in self.room_context if r.room_id == room_id), None)
        if not room:
            reply = Packet(T_LEAVE_ROOM, {"success": False, "message": "Room not found"})
            client.sendall(reply.to_bytes())
            return

        if username not in room.players:
            reply = Packet(T_LEAVE_ROOM, {"success": False, "message": "You are not in this room"})
            client.sendall(reply.to_bytes())
            return

        # 移除玩家
        room.players.remove(username)
        self.logger.info(f"Player {username} left room {room_id} (now {len(room.players)}/{room.max_players} players)")

        # 如果房間空了，刪除房間
        if len(room.players) == 0:
            self.room_context.remove(room)
            self.logger.info(f"Room {room_id} deleted (no players)")
        # 如果房主離開，轉移房主權限給第一個玩家
        elif room.room_owner == username and len(room.players) > 0:
            room.room_owner = room.players[0]
            self.logger.info(f"Room {room_id} owner changed to {room.room_owner}")

        reply = Packet(T_LEAVE_ROOM, {"success": True, "message": "Left room successfully"})
        client.sendall(reply.to_bytes())

    def _handle_user_disconnect(self, username: str):
        """處理用戶斷線：登出並從所有房間移除"""
        self.logger.info(f"Handling disconnect for user: {username}")
        
        # 1. 從 user_context 移除
        self.user_context = [u for u in self.user_context if u.username != username]
        
        # 2. 從所有房間移除
        for room in self.room_context[:]:  # 使用副本遍歷，因為可能會刪除房間
            if username in room.players:
                room.players.remove(username)
                self.logger.info(f"Removed {username} from room {room.room_id}")
                
                # 如果房間空了，刪除房間
                if len(room.players) == 0:
                    self.room_context.remove(room)
                    self.logger.info(f"Room {room.room_id} deleted (no players after disconnect)")
                # 如果房主離開，轉移房主權限
                elif room.room_owner == username and len(room.players) > 0:
                    room.room_owner = room.players[0]
                    self.logger.info(f"Room {room.room_id} owner changed to {room.room_owner}")
        
        # 3. 從數據庫登出
        try:
            from common.Packet.user import LogoutPacket
            logout_packet = LogoutPacket(username)
            self.database_server.handle_logout(logout_packet)
            self.logger.info(f"User {username} logged out from database")
        except Exception as e:
            self.logger.error(f"Failed to logout user {username}: {e}")
