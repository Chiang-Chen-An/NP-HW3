from ..packet import Packet
from ..type import T_DEVELOPER_LOGIN, T_DEVELOPER_LOGOUT, T_DEVELOPER_REGISTER


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


class UploadGamePacket(Packet):
    """
    Upload game packet format:
    {
        "type": T_UPLOAD_GAME,
        "data": {
            "username": "username",
            "game_name": "game_name",
            "game_description": "game_description",
            "game_file": "game_file"
        }
    }
    """

    def __init__(
        self, username: str, game_name: str, game_description: str, game_file: str
    ):
        super().__init__(
            T_UPLOAD_GAME,
            {
                "username": username,
                "game_name": game_name,
                "game_description": game_description,
                "game_file": game_file,
            },
        )


class UpdateGamePacket(Packet):
    """
    Update game packet format:
    {
        "type": T_UPDATE_GAME,
        "data": {
            "username": "username",
            "game_name": "game_name",
            "game_description": "game_description",
            "game_file": "game_file"
        }
    }
    """

    def __init__(
        self, username: str, game_name: str, game_description: str, game_file: str
    ):
        super().__init__(
            T_UPDATE_GAME,
            {
                "username": username,
                "game_name": game_name,
                "game_description": game_description,
                "game_file": game_file,
            },
        )
