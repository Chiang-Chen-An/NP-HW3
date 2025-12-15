# Tic Tac Toe GUI

A graphical version of the classic Tic Tac Toe game using Python's Tkinter library.

## Features

- **Full GUI Interface**: Beautiful graphical interface with clickable buttons
- **Visual Feedback**: 
  - Player X shown in blue
  - Player O shown in red
  - Clear status messages
  - Turn indicators
- **Game Flow**:
  - Automatic connection to game server
  - Real-time board updates
  - Pop-up messages for game over
  - Clean window closing

## How to Play

1. Wait for the game to connect to the server
2. You will be assigned as Player 0 (X) or Player 1 (O)
3. When it's your turn, click any empty square to make your move
4. The game will automatically detect wins or draws
5. Close the window to exit

## Technical Details

- **Client**: Tkinter-based GUI with socket communication
- **Server**: Same game logic as CLI version, works with both GUI and CLI clients
- **Protocol**: JSON-based message protocol over TCP sockets
- **Max Players**: 2 (turn-based gameplay)

## Requirements

- Python 3.x
- tkinter (usually comes with Python)
- socket, json, threading (standard libraries)

## Differences from CLI Version

| Feature       | CLI Version   | GUI Version            |
| ------------- | ------------- | ---------------------- |
| Interface     | Text-based    | Graphical buttons      |
| Input         | Type numbers  | Click squares          |
| Board Display | ASCII art     | 3x3 button grid        |
| Status        | Text messages | Status label + pop-ups |
| Colors        | None          | Blue (X), Red (O)      |

## Game Server

The server is identical to the CLI version - it can handle both CLI and GUI clients simultaneously!
