from ..packet import Packet
from ..type import (
    T_DEVELOPER_LOGIN,
    T_DEVELOPER_LOGOUT,
    T_DEVELOPER_REGISTER,
    T_LIST_DEVELOPER_GAMES,
    T_UPLOAD_GAME_INIT,
    T_UPLOAD_GAME_CHUNK,
    T_UPLOAD_GAME_FINISH,
    T_UPDATE_GAME_INIT,
    T_UPDATE_GAME_CHUNK,
    T_UPDATE_GAME_FINISH,
)


class DeveloperLoginPacket(Packet):
    """
    Login packet format:
    {
        "type": T_DEVELOPER_LOGIN,
        "data": {
            "username": "username",
            "password": "password"
        }
    }
    """

    def __init__(self, username: str, password: str):
        super().__init__(
            T_DEVELOPER_LOGIN, {"username": username, "password": password}
        )


class DeveloperRegisterPacket(Packet):
    """
    Register packet format:
    {
        "type": T_DEVELOPER_REGISTER,
        "data": {
            "username": "username",
            "password": "password"
        }
    }
    """

    def __init__(self, username: str, password: str):
        super().__init__(
            T_DEVELOPER_REGISTER, {"username": username, "password": password}
        )


class DeveloperLogoutPacket(Packet):
    """
    Logout packet format:
    {
        "type": T_DEVELOPER_LOGOUT,
        "data": {
            "username": "username"
        }
    }
    """

    def __init__(self, username: str):
        super().__init__(T_DEVELOPER_LOGOUT, {"username": username})


class ListDeveloperGamesPacket(Packet):
    """
    List developer games packet format:
    {
        "type": T_LIST_DEVELOPER_GAMES,
        "data": {
            "username": "username"
        }
    }
    """

    def __init__(self, username: str):
        super().__init__(T_LIST_DEVELOPER_GAMES, {"username": username})


class UploadGameInitPacket(Packet):
    def __init__(
        self, username: str, game_name: str, game_description: str, file_size: int
    ):
        super().__init__(
            T_UPLOAD_GAME_INIT,
            {
                "username": username,
                "game_name": game_name,
                "game_description": game_description,
                "file_size": file_size,
            },
        )


class UploadGameChunkPacket(Packet):
    def __init__(self, upload_id: str, chunk_data: str):
        super().__init__(
            T_UPLOAD_GAME_CHUNK,
            {"upload_id": upload_id, "chunk_data": chunk_data},
        )


class UploadGameFinishPacket(Packet):
    def __init__(self, upload_id: str, checksum: str):
        super().__init__(
            T_UPLOAD_GAME_FINISH,
            {"upload_id": upload_id, "checksum": checksum},
        )


class UpdateGameInitPacket(Packet):
    def __init__(self, username: str, game_id: str, game_version: str, file_size: int):
        super().__init__(
            T_UPDATE_GAME_INIT,
            {
                "username": username,
                "game_id": game_id,
                "game_version": game_version,
                "file_size": file_size,
            },
        )


class UpdateGameChunkPacket(Packet):
    def __init__(self, upload_id: str, chunk_data: str):
        super().__init__(
            T_UPDATE_GAME_CHUNK,
            {"upload_id": upload_id, "chunk_data": chunk_data},
        )


class UpdateGameFinishPacket(Packet):
    def __init__(self, upload_id: str, checksum: str):
        super().__init__(
            T_UPDATE_GAME_FINISH,
            {"upload_id": upload_id, "checksum": checksum},
        )
