from ..packet import Packet
from ..type import (
    T_DELETE_GAME,
)


class DeleteGamePacket(Packet):
    def __init__(self, game_id: str, username: str):
        super().__init__(
            T_DELETE_GAME,
            {
                "game_id": game_id,
                "username": username,
            },
        )
