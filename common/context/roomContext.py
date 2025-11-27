class RoomContext:
    def __init__(self, room_id: int, game_id: int, max_players: int, room_owner: str):
        self.room_id = room_id
        self.game_id = game_id
        self.max_players = max_players
        self.room_owner = room_owner
        self.players = [room_owner]
        self.is_started = False
