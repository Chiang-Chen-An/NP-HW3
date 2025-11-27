# Database Server

Database server for the project.

## Database Schema

### users.json

```json
[
  {
    "username": "user",
    "password": "user",
    "is_online": true,
    "last_login": "2025-11-25T22:58:34+08:00",
    "created_at": "2025-11-25T22:58:34+08:00",
    "role": "user"
  },
  {
    "username": "developer",
    "password": "developer",
    "is_online": true,
    "last_login": "2025-11-25T22:58:34+08:00",
    "created_at": "2025-11-25T22:58:34+08:00",
    "role": "developer"
  }
]
```

### games.json

```json
[
  {
    "game_id": 1,
    "game_name": "game1",
    "game_description": "game1 description",
    "game_version": "1.0.0",
    "game_author": "user",
    "download_count": 0,
    "max_players": 2,
    "comments": [
      {
        "username": "user",
        "rating": 5,
        "comment": "game1 comment"
      }
    ],
    "game_created_at": "2025-11-25T22:58:34+08:00"
  },
  {
    "game_id": 2,
    "game_name": "game2",
    "game_description": "game2 description",
    "game_version": "1.0.0",
    "game_author": "user",
    "download_count": 0,
    "max_players": 2,
    "comments": [
      {
        "username": "user",
        "rating": 5,
        "comment": "game1 comment"
      }
    ],
    "game_created_at": "2025-11-25T22:58:34+08:00"
  }
]
```

## Function

### handle_login
