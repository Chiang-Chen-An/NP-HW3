# Lobby Server

## Description

The lobby server is a server that handles the lobby of the game.

## Storage

Lobby Server 會將正在進行的房間存在自己的 memory 中 (python dict list)，並在遊戲結束後將房間的資訊寫入到 database 中。

### Function

#### \_handle_create_room

clinet 傳送 CreateRoomPacket，lobby server 會在 memory 中新增一個房間，並回傳 CreateRoomPacketReply。

#### \_handle_list_rooms

clinet 傳送 ListRoomsPacket，lobby server 會回傳 ListRoomsPacketReply。
