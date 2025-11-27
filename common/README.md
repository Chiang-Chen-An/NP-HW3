# Common

Common module for the project.

## Packet

定義所以傳送的封包格式，由 `class Packet` 定義。

### Attributes

1. type: string
   定義封包的類別，例如 `LOGIN`、`LOGOUT`、`MESSAGE` 等等
2. data: dict
   定義封包的內容，例如
   ```json
   {
     "username": "user1",
     "password": "password1"
   }
   ```

### Types

#### User Types

1. T_LOGIN
2. T_REGISTER
3. T_LOGOUT
4. T_LIST_ONLINE_USERS

#### Game Types

1. T_LIST_GAMES
2. T_GET_GAME_DETAIL
3. T_GAME_REVIEW
4. T_CREATE_ROOM
5. T_LIST_ROOMS

#### User Packets

1. LoginPacket

   ```json
   {
     "type": "LOGIN",
     "data": {
       "username": "user1",
       "password": "password1"
     }
   }
   ```

2. RegisterPacket

   ```json
   {
     "type": "REGISTER",
     "data": {
       "username": "user1",
       "password": "password1"
     }
   }
   ```

3. LogoutPacket

   ```json
   {
     "type": "LOGOUT",
     "data": {
       "username": "user1"
     }
   }
   ```

4. ListOnlineUsersPacket
   ```json
   {
     "type": "LIST_ONLINE_USERS",
     "data": {}
   }
   ```

#### Game Packets

1. ListGamesPacket

   ```json
   {
     "type": "LIST_GAMES",
     "data": {}
   }
   ```

2. GetGameDetailPacket

   ```json
   {
     "type": "GET_GAME_DETAIL",
     "data": {
       "game_id": "1"
     }
   }
   ```

3. GameReviewPacket

   ```json
   {
     "type": "GAME_REVIEW",
     "data": {
       "game_id": "1",
       "score": 5,
       "comment": "game1 comment"
     }
   }
   ```

4. CreateRoomPacket

   ```json
   {
     "type": "CREATE_ROOM",
     "data": {
       "game_id": "1",
       "host": "user1"
     }
   }
   ```

5. ListRoomsPacket

   ```json
   {
     "type": "LIST_ROOMS",
     "data": {}
   }
   ```

6. ListRoomsPacketReply

   ```json
   {
     "type": "LIST_ROOMS",
     "data": {
       "success": true,
       "rooms": [
         {
           "room_id": "1",
           "game_id": "1",
           "max_players": 2,
           "host": "user1",
           "users": ["user1", "user2", ...],
           "is_started": false,
           "is_ended": false
         },
         ...
       ]
     }
   }
   ```

7. CreateRoomPacketReply
   ```json
   {
     "type": "CREATE_ROOM",
     "data": {
       "success": true,
       "room_id": "1"
     }
   }
   ```

#### Database Packets

Database 回覆 lobby server 的封包

1. DBLoginPacket

   ```json
   {
     "type": "LOGIN",
     "data": {
       "success": true
     }
   }
   ```

2. DBRegisterPacket

   ```json
   {
     "type": "REGISTER",
     "data": {
       "success": true
     }
   }
   ```

3. DBLogoutPacket

   ```json
   {
     "type": "LOGOUT",
     "data": {
       "success": true
     }
   }
   ```

4. DBListOnlineUsersPacket

   ```json
   {
     "type": "LIST_ONLINE_USERS",
     "data": {
       "success": true,
       "online_users": ["user1", "user2", ...]
     }
   }
   ```

5. DBListGamesPacket

   ```json
   {
     "type": "LIST_GAMES",
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
   ```

6. DBGetGameDetailPacket

   ```json
   {
     "type": "GET_GAME_DETAIL",
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
   ```

7. DBGameReviewPacket
   ```json
   {
     "type": "GAME_REVIEW",
     "data": {
       "success": true,
       "message": "Review submitted successfully"
     }
   }
   ```

## Context

### UserContext

定義一個使用者的資訊，包含使用者名稱和 socket

```python
class UserContext:
    def __init__(self, username: str, socket: socket.socket):
        self.username = username
        self.socket = socket
```

### GameContext

定義一個房間的資訊，包含房間 ID、房主、玩家列表、是否開始、是否結束

```python
class GameContext:
    def __init__(self, game_id: int, host: str):
        self.game_id = game_id
        self.host = host
        self.users = []
        self.is_started = False
        self.is_ended = False
```
