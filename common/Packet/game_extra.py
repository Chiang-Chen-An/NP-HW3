from ..packet import Packet
from ..type import (
    T_DOWNLOAD_GAME_INIT,
    T_DOWNLOAD_GAME_CHUNK,
    T_DOWNLOAD_GAME_FINISH,
    T_START_GAME,
    T_JOIN_ROOM,
    T_LEAVE_ROOM,
)


class DownloadGameInitPacket(Packet):
    def __init__(self, game_id: str, username: str):
        super().__init__(
            T_DOWNLOAD_GAME_INIT,
            {
                "game_id": game_id,
                "username": username,
            },
        )


class DownloadGameChunkPacket(Packet):
    def __init__(self, upload_id: str, chunk_data: str):
        super().__init__(
            T_DOWNLOAD_GAME_CHUNK,
            {
                "upload_id": upload_id,
                "chunk_data": chunk_data,
            },
        )


class DownloadGameFinishPacket(Packet):
    def __init__(self, upload_id: str, checksum: str):
        super().__init__(
            T_DOWNLOAD_GAME_FINISH,
            {
                "upload_id": upload_id,
                "checksum": checksum,
            },
        )


class StartGamePacket(Packet):
    def __init__(self, room_id: str, game_id: str, server_ip: str, server_port: int):
        super().__init__(
            T_START_GAME,
            {
                "room_id": room_id,
                "game_id": game_id,
                "server_ip": server_ip,
                "server_port": server_port,
            },
        )


class JoinRoomPacket(Packet):
    def __init__(self, room_id: str, username: str):
        super().__init__(
            T_JOIN_ROOM,
            {
                "room_id": room_id,
                "username": username,
            },
        )


class LeaveRoomPacket(Packet):
    def __init__(self, room_id: str, username: str):
        super().__init__(
            T_LEAVE_ROOM,
            {
                "room_id": room_id,
                "username": username,
            },
        )

