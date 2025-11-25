from ..packet import Packet
from ..type import T_LOGIN, T_REGISTER, T_LOGOUT


class LoginPacket(Packet):
    """
    Login packet format:
    {
        "type": T_LOGIN,
        "data": {
            "username": "username",
            "password": "password"
        }
    }
    """

    def __init__(self, username: str, password: str):
        super().__init__(T_LOGIN, {"username": username, "password": password})


class RegisterPacket(Packet):
    """
    Register packet format:
    {
        "type": T_REGISTER,
        "data": {
            "username": "username",
            "password": "password"
        }
    }
    """

    def __init__(self, username: str, password: str):
        super().__init__(T_REGISTER, {"username": username, "password": password})


class LogoutPacket(Packet):
    """
    Logout packet format:
    {
        "type": T_LOGOUT,
        "data": {}
    }
    """

    def __init__(self):
        super().__init__(T_LOGOUT, {})
