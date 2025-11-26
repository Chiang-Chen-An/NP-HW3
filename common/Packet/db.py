import json
from ..packet import Packet
from ..type import (
    T_LOGIN,
    T_REGISTER,
    T_LOGOUT,
    T_LIST_ONLINE_USERS,
    T_LIST_GAMES,
    T_GET_GAME_DETAIL,
    T_GAME_REVIEW,
)


class DBLoginPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_LOGIN,
        "data": {
            "success": true,
            "message": "Login successful"
        }
    }
    """

    def __init__(self, success: bool, message: str = "Login successful"):
        super().__init__(T_LOGIN, {"success": success, "message": message})


class DBRegisterPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_REGISTER,
        "data": {
            "success": true,
            "message": "Register successful"
        }
    }
    """

    def __init__(self, success: bool, message: str = "Register successful"):
        super().__init__(T_REGISTER, {"success": success, "message": message})


class DBLogoutPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_LOGOUT,
        "data": {
            "success": true,
            "message": "Logout successful"
        }
    }
    """

    def __init__(self, success: bool, message: str = "Logout successful"):
        super().__init__(T_LOGOUT, {"success": success, "message": message})


class DBListOnlineUsersPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_LIST_ONLINE_USERS,
        "data": {
            "success": true,
            "online_users": ["user1", "user2", ...]
        }
    }
    """

    def __init__(self, success: bool, online_users: list[str]):
        super().__init__(
            T_LIST_ONLINE_USERS, {"success": success, "online_users": online_users}
        )


class DBListGamesPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_LIST_GAMES,
        "data": {
            "success": true,
            "games": [
                {
                    "game_id": "1",
                    "game_name": "game1",
                    "game_description": "game1 description",
                    "game_version": "1.0.0",
                    "game_author": "user",
                    "download_count": 0,
                    "comments": [],
                    "game_created_at": "2025-11-25T22:58:34+08:00"
                },
                ...
            ]
        }
    }
    """

    def __init__(self, success: bool, games: list[dict]):
        super().__init__(T_LIST_GAMES, {"success": success, "games": games})


class DBGetGameDetailPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_GET_GAME_DETAIL,
        "data": {
            "success": true,
            "game_info": {
                "game_id": "1",
                "game_name": "game1",
                "game_description": "game1 description",
                "game_version": "1.0.0",
                "game_author": "user",
                "download_count": 0,
                "comments": [],
                "game_created_at": "2025-11-25T22:58:34+08:00"
            }
        }
    }
    """

    def __init__(self, success: bool, game_info: dict):
        super().__init__(
            T_GET_GAME_DETAIL, {"success": success, "game_info": game_info}
        )


class DBGameReviewPacket(Packet):
    """
    Reply packet from database server to lobby server
    Packet format:
    {
        "type": T_GAME_REVIEW,
        "data": {
            "success": true,
            "message": "Review submitted successfully"
        }
    }
    """

    def __init__(self, success: bool, message: str = "Review submitted successfully"):
        super().__init__(T_GAME_REVIEW, {"success": success, "message": message})
