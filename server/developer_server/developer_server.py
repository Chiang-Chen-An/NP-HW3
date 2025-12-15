from common.log_utils import setup_logger
from common.packet import Packet
from common.type import (
    T_DEVELOPER_LOGIN,
    T_DEVELOPER_REGISTER,
    T_DEVELOPER_LOGOUT,
    T_LIST_DEVELOPER_GAMES,
    T_UPLOAD_GAME_INIT,
    T_UPLOAD_GAME_CHUNK,
    T_UPLOAD_GAME_FINISH,
    T_UPDATE_GAME_INIT,
    T_UPDATE_GAME_CHUNK,
    T_UPDATE_GAME_CHUNK,
    T_UPDATE_GAME_FINISH,
    T_DELETE_GAME,
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
        try:
            while True:
                client, addr = server.accept()
                self._handle_client(client, addr)
        finally:
            # 服務器關閉時登出所有開發者
            self.logger.info("Developer server shutting down, logging out all developers...")
            for user in self.user_context[:]:
                try:
                    from common.Packet.developer import DeveloperLogoutPacket
                    logout_packet = DeveloperLogoutPacket(user.username)
                    self.database_server.handle_developer_logout(logout_packet)
                    self.logger.info(f"Logged out developer: {user.username}")
                except Exception as e:
                    self.logger.error(f"Failed to logout developer {user.username}: {e}")
            self.user_context.clear()
            server.close()
            self.logger.info("Developer server shutdown complete")

    def _handle_client(self, client: socket.socket, addr: tuple[str, int]):
        self.logger.info(f"Client connected: {addr}")
        current_username = None
        try:
            while True:
                packet = Packet.receive(client)
                if packet is None:
                    self.logger.info(f"Client disconnected: {addr}")
                    break
                
                # 記錄當前開發者用戶名（用於斷線時登出）
                if packet.type == T_DEVELOPER_LOGIN and packet.data.get("username"):
                    current_username = packet.data["username"]
                
                self._handle_packet(client, addr, packet)
        finally:
            # 開發者斷線時自動登出
            if current_username:
                self._handle_developer_disconnect(current_username)
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
        elif packet.type == T_UPLOAD_GAME_INIT:
            reply = self._handle_upload_game_init(client, addr, packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_UPLOAD_GAME_CHUNK:
            reply = self._handle_upload_game_chunk(client, addr, packet)
            if reply:
                client.sendall(reply.to_bytes())
        elif packet.type == T_UPLOAD_GAME_FINISH:
            reply = self._handle_upload_game_finish(client, addr, packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_UPDATE_GAME_INIT:
            reply = self._handle_update_game_init(client, addr, packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_UPDATE_GAME_CHUNK:
            reply = self._handle_update_game_chunk(client, addr, packet)
            if reply:
                client.sendall(reply.to_bytes())
        elif packet.type == T_UPDATE_GAME_FINISH:
            reply = self._handle_update_game_finish(client, addr, packet)
            client.sendall(reply.to_bytes())
        elif packet.type == T_DELETE_GAME:
            reply = self._handle_delete_game(client, addr, packet)
            client.sendall(reply.to_bytes())

    def _handle_upload_game_init(self, client, addr, packet):
        import uuid
        import os

        username = packet.data["username"]
        game_name = packet.data["game_name"]
        game_description = packet.data["game_description"]
        file_size = packet.data["file_size"]

        upload_id = str(uuid.uuid4())

        # Create temp file
        temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, f"{upload_id}.zip")

        # Store upload context
        # We need to store this in self.active_uploads, but self is not persistent across requests if we don't init it.
        # Wait, DeveloperServer is a class instance, so self.active_uploads will persist.
        if not hasattr(self, "active_uploads"):
            self.active_uploads = {}

        self.active_uploads[upload_id] = {
            "username": username,
            "game_name": game_name,
            "game_description": game_description,
            "file_size": file_size,
            "temp_file_path": temp_file_path,
            "received_bytes": 0,
            "is_update": False,
        }

        # Create empty file
        with open(temp_file_path, "wb") as f:
            pass

        return Packet(T_UPLOAD_GAME_INIT, {"success": True, "upload_id": upload_id})

    def _handle_upload_game_chunk(self, client, addr, packet):
        import base64

        upload_id = packet.data["upload_id"]
        chunk_data = packet.data["chunk_data"]

        if not hasattr(self, "active_uploads") or upload_id not in self.active_uploads:
            return Packet(
                T_UPLOAD_GAME_CHUNK, {"success": False, "message": "Invalid upload ID"}
            )

        context = self.active_uploads[upload_id]

        try:
            decoded_chunk = base64.b64decode(chunk_data)
            with open(context["temp_file_path"], "ab") as f:
                f.write(decoded_chunk)

            context["received_bytes"] += len(decoded_chunk)
            return None
        except Exception as e:
            self.logger.error(f"Chunk upload failed: {e}")
            return Packet(T_UPLOAD_GAME_CHUNK, {"success": False, "message": str(e)})

    def _handle_upload_game_finish(self, client, addr, packet):
        import os
        import shutil
        import zipfile
        import json

        upload_id = packet.data["upload_id"]
        checksum = packet.data["checksum"]

        if not hasattr(self, "active_uploads") or upload_id not in self.active_uploads:
            return Packet(
                T_UPLOAD_GAME_FINISH, {"success": False, "message": "Invalid upload ID"}
            )

        context = self.active_uploads[upload_id]
        temp_file_path = context["temp_file_path"]

        try:
            # TODO: Verify checksum

            # Generate Game ID (Ask DB or generate here? Better ask DB to reserve ID, but for now let's generate or assume DB handles it)
            # Actually, we need to store files first.
            # Let's ask DB for a new Game ID first? Or just use a placeholder and let DB assign.
            # But we need to store in storage/{game_id}.
            # Let's query DB for next ID or just use UUID for game_id?
            # Spec says "game_id" is usually integer string.
            # Let's assume we can get a new ID from DB.
            # But we don't have a "get_next_game_id" packet.
            # Workaround: Generate a UUID for game_id or check existing games.
            # Let's use the DatabaseServer to handle the final metadata and ID assignment.
            # But we need to move files to storage/{game_id}.
            # So maybe we send the file *path* to DB? No, DB is on another server potentially (logical separation).
            # But here they are on same machine.
            # Let's assume DeveloperServer manages storage.
            # We need a way to get a unique Game ID.
            # Let's read games.json directly? No, that breaks separation.
            # Let's ask DB to "reserve" a game?
            # Or simpler: Just use a UUID for game_id.

            # For this homework, let's just list games to find max ID.
            # self.database_server is available.
            # But self.database_server is an instance of DatabaseServer class!
            # So we can call methods directly if it's in the same process/memory space.
            # In `developer_server.py`, `self.database_server = DatabaseServer()`.
            # This creates a NEW instance of DatabaseServer.
            # If DatabaseServer maintains state in memory (it does, `self.database` paths), it should be fine as long as they point to same files.
            # `database_server.py` uses `json.load` from files every time for some methods, but `handle_login` reads once?
            # Let's check `database_server.py`.
            # It reads from file for `handle_list_games`.
            # So it's safe to use a new instance to read/write files.

            # Get next game ID
            # We can add a helper in DatabaseServer or just read the file here (less clean).
            # Let's use `self.database_server.get_next_game_id()` if we add it, or just implement logic here.
            # I'll implement logic here to avoid modifying DB server too much if possible, or modify DB server to expose it.
            # Actually, `DatabaseServer` has `handle_upload_game` which I implemented earlier.
            # I can reuse that but pass the *path* instead of content?
            # Or I can just do the storage logic here and call `handle_upload_game_metadata`.

            # Let's implement `handle_upload_game_metadata` in DB server later.
            # For now, let's determine ID.

            # Unzip to temp dir first to read config
            temp_extract_dir = os.path.join(
                os.path.dirname(__file__), f"temp_extract_{upload_id}"
            )
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir)

            with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                zip_ref.extractall(temp_extract_dir)

            # Read config.json
            config_path = os.path.join(temp_extract_dir, "config.json")
            if not os.path.exists(config_path):
                shutil.rmtree(temp_extract_dir)
                return Packet(
                    T_UPLOAD_GAME_FINISH,
                    {"success": False, "message": "Missing config.json"},
                )

            with open(config_path, "r") as f:
                config = json.load(f)

            # 從 config.json 讀取遊戲資訊
            game_name = config.get("game_name", context["game_name"])
            game_description = config.get("game_description", context["game_description"])
            game_version = config.get("game_version", "1.0.0")
            max_players = config.get("max_players", 2)

            # 先添加遊戲到數據庫以獲取系統生成的 game_id
            # 使用上傳者的 username 作為 game_author
            try:
                self.logger.info(f"Adding game metadata to get ID")
                game_id = self.database_server.add_game_metadata(
                    context["username"],  # 使用上傳者的 username
                    game_name,  # 從 config.json 讀取
                    game_description,  # 從 config.json 讀取
                    game_version,  # 從 config.json 讀取
                    max_players,  # 從 config.json 讀取
                )
                self.logger.info(f"Generated game_id: {game_id}")
            except Exception as e:
                self.logger.error(f"DB update failed: {e}")
                shutil.rmtree(temp_extract_dir)
                return Packet(
                    T_UPLOAD_GAME_FINISH,
                    {"success": False, "message": f"Database error: {str(e)}"},
                )

            # Storage Path (使用生成的數字 ID)
            storage_dir = os.path.join(
                os.path.dirname(__file__), f"../storage/{game_id}/{game_version}"
            )
            if os.path.exists(storage_dir):
                shutil.rmtree(storage_dir)
            os.makedirs(storage_dir)

            # Move files
            for item in os.listdir(temp_extract_dir):
                s = os.path.join(temp_extract_dir, item)
                d = os.path.join(storage_dir, item)
                if os.path.isdir(s):
                    shutil.move(s, d)
                else:
                    shutil.move(s, d)

            shutil.rmtree(temp_extract_dir)

            # 元數據已經在上面添加了，這裡不需要再次添加
            self.logger.info(f"Game uploaded successfully with ID: {game_id}")

            # Cleanup
            if upload_id in self.active_uploads:
                del self.active_uploads[upload_id]

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return Packet(
                T_UPLOAD_GAME_FINISH, {
                    "success": True, 
                    "message": "Upload complete",
                    "game_id": game_id  # 返回生成的 game_id
                }
            )

        except Exception as e:
            self.logger.error(f"Finish upload failed: {e}")
            return Packet(T_UPLOAD_GAME_FINISH, {"success": False, "message": str(e)})

    def _handle_update_game_init(self, client, addr, packet):
        import uuid
        import os

        username = packet.data["username"]
        game_id = packet.data["game_id"]
        game_version = packet.data["game_version"]
        file_size = packet.data["file_size"]

        # Verify ownership? (Skip for now or check DB)

        upload_id = str(uuid.uuid4())

        temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, f"{upload_id}.zip")

        if not hasattr(self, "active_uploads"):
            self.active_uploads = {}

        self.active_uploads[upload_id] = {
            "username": username,
            "game_id": game_id,
            "game_version": game_version,
            "file_size": file_size,
            "temp_file_path": temp_file_path,
            "received_bytes": 0,
            "is_update": True,
        }

        with open(temp_file_path, "wb") as f:
            pass

        return Packet(T_UPDATE_GAME_INIT, {"success": True, "upload_id": upload_id})

    def _handle_update_game_chunk(self, client, addr, packet):
        return self._handle_upload_game_chunk(client, addr, packet)  # Reuse logic

    def _handle_update_game_finish(self, client, addr, packet):
        import os
        import shutil
        import zipfile

        upload_id = packet.data["upload_id"]

        if not hasattr(self, "active_uploads") or upload_id not in self.active_uploads:
            return Packet(
                T_UPDATE_GAME_FINISH, {"success": False, "message": "Invalid upload ID"}
            )

        context = self.active_uploads[upload_id]
        temp_file_path = context["temp_file_path"]
        game_id = context["game_id"]
        game_version = context["game_version"]

        try:
            storage_dir = os.path.join(
                os.path.dirname(__file__), f"../storage/{game_id}/{game_version}"
            )
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)

            with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                zip_ref.extractall(storage_dir)

            config_path = os.path.join(storage_dir, "config.json")
            if not os.path.exists(config_path):
                return Packet(
                    T_UPDATE_GAME_FINISH,
                    {"success": False, "message": "Missing config.json"},
                )

            # 讀取 config.json 以獲取更新的遊戲資訊
            import json
            with open(config_path, "r") as f:
                config = json.load(f)
            
            game_name = config.get("game_name", "")
            game_description = config.get("game_description", "")
            max_players = config.get("max_players", 2)

            # Update DB (包含 description 和其他資訊)
            self.database_server.update_game_metadata(
                game_id, 
                game_version,
                game_name,
                game_description,
                max_players
            )

            os.remove(temp_file_path)
            del self.active_uploads[upload_id]

            return Packet(
                T_UPDATE_GAME_FINISH, {"success": True, "message": "Update complete"}
            )

        except Exception as e:
            self.logger.error(f"Finish update failed: {e}")
            return Packet(T_UPDATE_GAME_FINISH, {"success": False, "message": str(e)})

    def _handle_delete_game(self, client, addr, packet):
        import shutil
        import os

        game_id = packet.data["game_id"]
        username = packet.data["username"]

        # 1. Update DB
        success, message = self.database_server.delete_game_metadata(game_id, username)
        if not success:
            return Packet(T_DELETE_GAME, {"success": False, "message": message})

        # 2. Delete files
        # We need to delete storage/{game_id}
        # Be careful: storage/{game_id} contains all versions.
        # If we delete the game, we should delete all versions.
        try:
            storage_dir = os.path.join(
                os.path.dirname(__file__), f"../storage/{game_id}"
            )
            if os.path.exists(storage_dir):
                shutil.rmtree(storage_dir)

            return Packet(
                T_DELETE_GAME, {"success": True, "message": "Game deleted successfully"}
            )
        except Exception as e:
            self.logger.error(f"Delete game failed: {e}")
            # DB was updated but files might remain. In a real system we might want transaction or cleanup job.
            return Packet(
                T_DELETE_GAME,
                {
                    "success": True,
                    "message": f"Game deleted from DB but file cleanup failed: {e}",
                },
            )

    def _handle_developer_disconnect(self, username: str):
        """處理開發者斷線：登出"""
        self.logger.info(f"Handling disconnect for developer: {username}")
        
        # 從 user_context 移除
        self.user_context = [u for u in self.user_context if u.username != username]
        
        # 從數據庫登出
        try:
            from common.Packet.developer import DeveloperLogoutPacket
            logout_packet = DeveloperLogoutPacket(username)
            self.database_server.handle_developer_logout(logout_packet)
            self.logger.info(f"Developer {username} logged out from database")
        except Exception as e:
            self.logger.error(f"Failed to logout developer {username}: {e}")
