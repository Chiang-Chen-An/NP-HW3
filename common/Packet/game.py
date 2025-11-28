from ..packet import Packet
from ..type import (
    T_LIST_GAMES,
    T_GET_GAME_DETAIL,
    T_GAME_REVIEW,
    T_CREATE_ROOM,
    T_LIST_ROOMS,
)


class ListGamesPacket(Packet):
    def __init__(self):
        super().__init__(T_LIST_GAMES, {})


class GetGameDetailPacket(Packet):
    def __init__(self, game_id: str):
        super().__init__(T_GET_GAME_DETAIL, {"game_id": game_id})


class GameReviewPacket(Packet):
    def __init__(self, game_id: str, score: int, comment: str):
        super().__init__(
            T_GAME_REVIEW, {"game_id": game_id, "score": score, "comment": comment}
        )


class CreateRoomPacket(Packet):
    def __init__(self, game_id: str, username: str):
        super().__init__(T_CREATE_ROOM, {"game_id": game_id, "username": username})


class CreateRoomPacketReply(Packet):
    def __init__(self, success: bool, room_id: str):
        super().__init__(T_CREATE_ROOM, {"success": success, "room_id": room_id})


class ListRoomsPacket(Packet):
    def __init__(self):
        super().__init__(T_LIST_ROOMS, {})


class ListRoomsPacketReply(Packet):
    def __init__(self, success: bool, rooms: list[dict]):
        super().__init__(T_LIST_ROOMS, {"success": success, "rooms": rooms})
