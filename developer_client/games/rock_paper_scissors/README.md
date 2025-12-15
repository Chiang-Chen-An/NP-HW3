# Rock Paper Scissors

A CLI-based Rock-Paper-Scissors game for 2 players with best-of-5 rounds.

## Game Rules

- **Rock** beats **Scissors**
- **Scissors** beats **Paper**
- **Paper** beats **Rock**

## Game Flow

1. Two players connect to the server
2. Game plays 5 rounds (or until one player wins 3 rounds)
3. Each round, both players simultaneously choose:
   - `r` or `rock` for Rock 🪨
   - `p` or `paper` for Paper 📄
   - `s` or `scissors` for Scissors ✂️
4. Server determines the winner of each round
5. First player to win 3 rounds wins the game

## Features

- **Best of 5**: Play up to 5 rounds
- **Real-time scoring**: See wins/losses/ties after each round
- **Simple commands**: Just type r, p, or s
- **Automatic synchronization**: Both players must make their choice before results are shown
- **Clear feedback**: Visual indicators for wins, losses, and ties

## How to Play

1. Wait for connection to server
2. Wait for opponent to join
3. When prompted, enter your choice:
   - Type `r` or `rock` for Rock
   - Type `p` or `paper` for Paper
   - Type `s` or `scissors` for Scissors
4. Wait for opponent to choose
5. See the result and continue to next round
6. After 5 rounds (or when someone wins 3), see final results

## Example Game Session

```
==================================================
You are Player 1
==================================================
Waiting for opponent to join...

Game will start when both players are ready.

Rock Paper Scissors - Best of 5 Rounds!
Commands:
  r or rock     - Play Rock
  p or paper    - Play Paper
  s or scissors - Play Scissors
==================================================

🎮 Game Started! 🎮

==================================================
                    ROUND 1                      
==================================================
>>> Your turn! Enter your choice (r/p/s): r
⏳ Waiting for opponent...

==================================================
                  ROUND RESULT                   
==================================================
Player 1 chose: ROCK
Player 2 chose: SCISSORS

🎉 You WIN this round!

Current Score:
  Wins: 1 | Losses: 0 | Ties: 0
==================================================
```

## Technical Details

- **Protocol**: JSON over TCP
- **Max Players**: 2
- **Game Type**: Turn-based (simultaneous choices)
- **Rounds**: Best of 5

## Requirements

- Python 3.x
- Standard libraries (socket, json, threading)
