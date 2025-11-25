import json
from ..packet import Packet
from ..type import T_LOGIN, T_REGISTER, T_LOGOUT


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
