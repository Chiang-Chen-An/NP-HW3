import socket
import sys
import threading
import json


class TicTacToeServer:
    def __init__(self, port):
        self.host = "0.0.0.0"
        self.port = port
        self.players = []
        self.lock = threading.Lock()
        self.current_turn = 0
        self.board = [" " for _ in range(9)]
        self.game_over = False

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(2)
        print(f"Game Server listening on port {self.port}")

        while len(self.players) < 2:
            conn, addr = server.accept()
            print(f"Player connected from {addr}")
            with self.lock:
                player_id = len(self.players)
                self.players.append(conn)
                threading.Thread(
                    target=self.handle_client, args=(conn, player_id)
                ).start()
        
        # 當兩個玩家都連接後，發送初始遊戲狀態
        import time
        time.sleep(0.5)  # 給客戶端一點時間準備
        print("Both players connected. Starting game!")
        initial_state = {
            "type": "UPDATE",
            "board": self.board,
            "current_turn": 0
        }
        self.broadcast(initial_state)

    def handle_client(self, conn, player_id):
        # Send welcome message
        conn.sendall(
            json.dumps({"type": "WELCOME", "player_id": player_id}).encode() + b"\n"
        )

        while not self.game_over:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                msg = json.loads(data.decode().strip())

                if msg["type"] == "MOVE":
                    self.process_move(player_id, msg["position"])

            except Exception as e:
                print(f"Error handling client {player_id}: {e}")
                break

        conn.close()

    def process_move(self, player_id, position):
        with self.lock:
            if self.game_over:
                return

            if player_id != self.current_turn:
                self.send_error(player_id, "Not your turn")
                return

            if self.board[position] != " ":
                self.send_error(player_id, "Invalid move")
                return

            symbol = "X" if player_id == 0 else "O"
            self.board[position] = symbol

            # Check win
            winner = self.check_win()

            update = {
                "type": "UPDATE",
                "board": self.board,
                "current_turn": 1 - self.current_turn,
            }

            if winner:
                update["winner"] = winner
                self.game_over = True
            elif " " not in self.board:
                update["winner"] = "DRAW"
                self.game_over = True

            self.current_turn = 1 - self.current_turn
            self.broadcast(update)

    def check_win(self):
        wins = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),  # Rows
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),  # Cols
            (0, 4, 8),
            (2, 4, 6),  # Diagonals
        ]
        for a, b, c in wins:
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] != " ":
                return "Player 1" if self.board[a] == "X" else "Player 2"
        return None

    def broadcast(self, message):
        data = json.dumps(message).encode() + b"\n"
        for p in self.players:
            try:
                p.sendall(data)
            except:
                pass

    def send_error(self, player_id, message):
        try:
            self.players[player_id].sendall(
                json.dumps({"type": "ERROR", "message": message}).encode() + b"\n"
            )
        except:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    server = TicTacToeServer(port)
    server.start()
