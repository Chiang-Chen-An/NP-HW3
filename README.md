# Network Programming Final - Game Store System

A complete Game Store System featuring a Developer Platform for uploading/managing games and a Lobby/Store for players to download, review, and play games.

## 🎯 System Overview

This project implements a comprehensive game distribution platform with three main components:

1. **Developer Platform**: Upload, update, and manage games
2. **Player Lobby**: Browse, download, review, and play games
3. **Backend Servers**: Handle authentication, storage, and game orchestration

## 📋 Features Implemented

### Developer Features (Use Cases D1, D2, D3)
- ✅ **D1**: Upload new games with metadata and version control
- ✅ **D2**: Update existing games with new versions
- ✅ **D3**: Delete/unpublish games from the store
- ✅ Account management with single-session enforcement
- ✅ Menu-driven interface (max 5 options per screen)

### Player Features (Use Cases P1, P2, P3, P4)
- ✅ **P1**: Browse game store with detailed game information
- ✅ **P2**: Download and update games (organized by player)
- ✅ **P3**: Create rooms and launch games automatically
- ✅ **P4**: Rate games (1-5 stars) and write reviews
- ✅ Account management with single-session enforcement
- ✅ Version tracking for each downloaded game

### Technical Features
- ✅ Persistent JSON database (survives server restart)
- ✅ Chunked file transfer for large game uploads/downloads
- ✅ MD5 checksum verification
- ✅ Automatic game server launching
- ✅ Multi-room support
- ✅ Comprehensive logging

## 🏗️ System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Developer Client├─────►│Developer Server  │     │  Lobby Server   │
└─────────────────┘     │  (Port 8081)     │     │  (Port 12346)   │
                        └──────────────────┘     └─────────────────┘
                                 │                        │
                                 ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │ Database Server  │     │  Lobby Client   │
                        │ (JSON Files)     │◄────┤  (Players)      │
                        └──────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Storage/        │
                        │  {game_id}/      │
                        │    {version}/    │
                        └──────────────────┘
```

- **Lobby Server** (`140.113.17.13:12346`): Player authentication, game listing, room management, game launching
- **Developer Server** (`140.113.17.13:8081`): Developer authentication, game upload/update/delete
- **Database**: JSON-based storage in `server/database_server/data/`
  - `users.json`: Player accounts
  - `developers.json`: Developer accounts  
  - `games.json`: Game metadata with ratings
- **Storage**: `server/storage/{game_id}/{version}/` for uploaded games

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- Linux environment (recommended for demo)
- No external dependencies required (uses standard library only)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd NP-HW3
```

2. Initialize the system:
```bash
make init
# This creates database files, storage, and log directories
```

3. (Optional) Verify everything is ready:
```bash
./verify_setup.sh
# Should show "All checks passed!"
```

### Starting the System

**You need 4 separate terminal windows to run a complete demo.**

#### Terminal 1: Lobby Server
```bash
make lobby_server
# or manually:
python3 -m server.lobby_server.main
```

#### Terminal 2: Developer Server  
```bash
make developer_server
# or manually:
python3 -m server.developer_server.main
```

#### Terminal 3: Developer Client
```bash
make developer_client
# or manually:
python3 -m developer_client.main
```

#### Terminal 4: Player Client (Lobby)
```bash
make client
# or manually:
python3 -m client.lobby_client.main
```

### First-Time Setup (Optional)

If you want to reset the database and start fresh:

```bash
make reset
```

This will delete all logs and database files. The system will recreate empty databases on first startup.

## 📖 Usage Guide

### For Developers

#### 1. Register and Login
- Run Developer Client
- Choose "Register" and create a new developer account
- Login with your credentials

#### 2. Upload a New Game (Use Case D1)
1. Prepare a game folder with this structure:
   ```
   your_game/
   ├── config.json          # Required: Game metadata
   ├── client/              # Required: Client code
   │   ├── client.py or main.py
   │   └── ...
   └── server/              # Required: Server code
       ├── server.py or main.py
       └── ...
   ```

2. Example `config.json`:
   ```json
   {
     "game_id": "my_awesome_game",
     "game_name": "My Awesome Game",
     "game_description": "A fun multiplayer game",
     "game_version": "1.0.0",
     "max_players": 2
   }
   ```

3. In Developer Client menu:
   - Select "2. Upload a new game"
   - Enter game name and description
   - Provide the absolute or relative path to your game folder
   - Wait for upload to complete

#### 3. Update a Game (Use Case D2)
1. Prepare an updated version with incremented version in `config.json`
2. Select "3. Update a game"
3. Enter the game_id and new version number
4. Provide path to the updated game folder

#### 4. Delete a Game (Use Case D3)
1. Select "4. Delete a game"
2. Enter the game_id to remove
3. Confirm deletion

#### 5. View Your Games
- Select "1. List my games" to see all your published games

### For Players

#### 1. Register and Login
- Run Lobby Client
- Choose "Register" and create a player account
- Login with your credentials

#### 2. Browse Games (Use Case P1)
1. Select "1. List the available games"
2. View the game list with ratings
3. Enter "1" to view details of a specific game
4. Enter the Game ID to see:
   - Full description
   - Version information
   - Player ratings and comments

#### 3. Download a Game (Use Case P2)
1. From game details, select "1. Download Game"
2. The game will be downloaded to:
   ```
   client/lobby_client/download/{your_username}/{game_id}/v{version}/
   ```
3. If a newer version exists, you'll be prompted to update

#### 4. Play a Game (Use Case P3)
1. Go to "3. Play game" from main menu
2. Choose "1. Create Room"
3. Select a game you've downloaded
4. Wait for other players or start immediately
5. The game client will launch automatically
6. After the game ends, you return to the lobby

#### 5. Rate and Review a Game (Use Case P4)
1. From game details, select "3. Write a Review / Rate"
2. Enter a rating (1-5 stars)
3. Write an optional comment
4. Your rating will appear in the game details for others to see

## 🎮 Testing with the Example Game

The repository includes a sample Tic-Tac-Toe game in `developer_client/games/tic_tac_toe/`.

### Demo Flow:

**Terminal 1 & 2**: Start both servers as described above

**Terminal 3 (Developer)**:
```
1. Register as "dev1" / "password"
2. Login
3. Select "Upload a new game"
4. Enter path: developer_client/games/tic_tac_toe
5. Wait for upload confirmation
```

**Terminal 4 (Player 1)**:
```
1. Register as "player1" / "password"
2. Login
3. Select "List the available games"
4. Note the game_id (e.g., "tic_tac_toe")
5. Select "View Game Details", enter game_id
6. Select "Download Game"
7. Select "Create Room"
8. Choose the downloaded game
```

**Terminal 5 (Player 2)** - Open a new terminal:
```bash
python3 -m client.lobby_client.main
```
```
1. Register as "player2" / "password"
2. Login
3. Select "Play game"
4. Select "Join Room"
5. Enter the room_id shown by Player 1
6. Wait for Player 1 to start the game
```

**Back to Terminal 4**: Press 's' to start the game

Both players will see their game clients launch and can play Tic-Tac-Toe!

## 🔧 Configuration

### Changing Server Addresses

Edit the following files to change IP/Port:

- **Lobby Server**: `server/lobby_server/main.py`
- **Developer Server**: `server/developer_server/main.py`
- **Lobby Client**: `client/lobby_client/main.py`
- **Developer Client**: `developer_client/main.py`

Example:
```python
def main():
    lobby_server = LobbyServer("0.0.0.0", 12346)  # Change here
    lobby_server.start()
```

## 🗂️ Project Structure

```
├── client/
│   └── lobby_client/           # Player client code
│       ├── lobby_client.py
│       ├── main.py
│       └── download/           # Downloaded games per player
│           └── {username}/
│               └── {game_id}/
│                   └── v{version}/
├── developer_client/
│   ├── developer_client.py     # Developer client code
│   ├── main.py
│   └── games/                  # Sample games for upload
│       └── tic_tac_toe/
├── server/
│   ├── database_server/
│   │   ├── database_server.py  # DB logic (in-memory but persistent)
│   │   └── data/               # JSON database files
│   │       ├── users.json
│   │       ├── developers.json
│   │       └── games.json
│   ├── developer_server/
│   │   ├── developer_server.py # Handles game upload/update/delete
│   │   ├── main.py
│   │   └── temp_uploads/       # Temporary upload staging
│   ├── lobby_server/
│   │   ├── lobby_server.py     # Handles rooms, downloads, game launch
│   │   └── main.py
│   └── storage/                # Uploaded game storage
│       └── {game_id}/
│           └── {version}/
│               ├── config.json
│               ├── client/
│               └── server/
├── common/
│   ├── packet.py               # Network packet protocol
│   ├── type.py                 # Packet type constants
│   ├── Packet/                 # Packet class definitions
│   └── context/                # User/Room/Game context classes
├── logs/                       # Server and client logs
├── Makefile                    # Convenient startup commands
└── README.md                   # This file
```

## 🐛 Troubleshooting

### "Connection refused"
- Ensure servers are running before starting clients
- Check that no other process is using ports 12346 or 8081

### "Account already logged in"
- The system enforces single-session per account
- Logout from other clients or wait for timeout

### "Game not found" when launching
- Ensure you've downloaded the game before trying to play
- Check that files exist in `client/lobby_client/download/{username}/{game_id}/`

### "Missing config.json" when uploading
- Verify your game folder has all required files
- Ensure `config.json` is in the root of the game folder

## 📝 Demo Checklist for Graders

- [ ] Start Lobby Server and Developer Server
- [ ] Register and login as developer
- [ ] Upload a new game (D1)
- [ ] View uploaded games
- [ ] Update game version (D2)
- [ ] Register and login as player
- [ ] Browse games in store (P1)
- [ ] View game details with ratings
- [ ] Download a game (P2)
- [ ] Create a room (P3)
- [ ] (Optional) Join room from second player
- [ ] Start and play a game
- [ ] Submit a rating and review (P4)
- [ ] Developer deletes a game (D3)
- [ ] Verify database persistence after server restart

## 📄 License

This project is for educational purposes as part of Network Programming course.
    - Press 's' (Owner) to start the game.
    - The system will automatically launch the game client.

## Game Structure Requirement

Uploaded games must follow this structure:

```
my_game/
├── config.json      # Game metadata (id, name, version, max_players)
├── client/          # Client-side code
│   └── client.py    # Entry point (or main.py)
└── server/          # Server-side code
    └── server.py    # Entry point (or main.py)
```

## Reset Data

To clear all data (users, games, logs):

```bash
make reset
```
