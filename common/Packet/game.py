from ..packet import Packet
from ..type import T_LIST_GAMES, T_GET_GAME_DETAIL, T_GAME_REVIEW


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
