class GameContext:
    def __init__(self, room_id: int, game_id: int, max_players: int, host: str):
        self.room_id = room_id
        self.game_id = game_id
        self.max_players = max_players
        self.host = host
        self.users = []
        self.is_started = False
        self.is_ended = False
