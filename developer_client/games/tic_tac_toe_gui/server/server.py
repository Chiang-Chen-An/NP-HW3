import socket
import sys
import threading
import json
import os
import logging
from datetime import datetime


class TicTacToeServer:
    def __init__(self, port):
        self.host = "0.0.0.0"
        self.port = port
        self.players = []
        self.lock = threading.Lock()
        self.current_turn = 0
        self.board = [" " for _ in range(9)]
        self.game_over = False
        
        # 設置日誌
        self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        # 創建 logs/game_logs 目錄
        log_dir = "logs/game_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 創建日誌文件名（包含時間戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"tic_tac_toe_{timestamp}_{self.port}.log")
        
        # 配置日誌
        self.logger = logging.getLogger(f"TicTacToe_{self.port}")
        self.logger.setLevel(logging.INFO)
        
        # 文件處理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info(f"Tic Tac Toe server initialized on port {self.port}")

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(2)
        print(f"Game Server listening on port {self.port}")
        self.logger.info(f"Game Server listening on port {self.port}")

        while len(self.players) < 2:
            conn, addr = server.accept()
            print(f"Player connected from {addr}")
            self.logger.info(f"Player connected from {addr}")
            with self.lock:
                player_id = len(self.players)
                self.players.append(conn)
                self.logger.info(f"Player {player_id} added to game")
                threading.Thread(
                    target=self.handle_client, args=(conn, player_id)
                ).start()
        
        # 當兩個玩家都連接後，發送初始遊戲狀態
        import time
        time.sleep(0.5)  # 給客戶端一點時間準備
        print("Both players connected. Starting game!")
        self.logger.info("Both players connected. Starting game!")
        initial_state = {
            "type": "UPDATE",
            "board": self.board,
            "current_turn": 0
        }
        self.broadcast(initial_state)
        self.logger.info("Initial game state broadcasted")
        
        # 保持伺服器運行直到遊戲結束
        while not self.game_over:
            time.sleep(0.1)
        
        print("Game ended. Server shutting down.")
        self.logger.info("Game ended. Server shutting down.")
        time.sleep(1)  # 給客戶端時間接收最後的訊息
        server.close()

    def handle_client(self, conn, player_id):
        # Send welcome message
        welcome_msg = json.dumps({"type": "WELCOME", "player_id": player_id}).encode() + b"\n"
        self.logger.info(f"Sending WELCOME to player {player_id}: {welcome_msg}")
        conn.sendall(welcome_msg)
        self.logger.info(f"Sent WELCOME message to player {player_id} (sendall returned)")
        
        # 確保資料發送
        import time
        time.sleep(0.1)

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
                self.logger.warning(f"Player {player_id} tried to move but it's not their turn")
                self.send_error(player_id, "Not your turn")
                return

            if self.board[position] != " ":
                self.logger.warning(f"Player {player_id} tried invalid move at position {position}")
                self.send_error(player_id, "Invalid move")
                return

            symbol = "X" if player_id == 0 else "O"
            self.board[position] = symbol
            self.logger.info(f"Player {player_id} ({symbol}) moved to position {position}")

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
                self.logger.info(f"Game over! Winner: {winner}")
            elif " " not in self.board:
                update["winner"] = "DRAW"
                self.game_over = True
                self.logger.info("Game over! It's a draw")

            self.current_turn = 1 - self.current_turn
            self.broadcast(update)
            self.logger.info(f"Game state updated. Next turn: Player {self.current_turn}")

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
    # 支援兩種格式：
    # python server.py <port>  (舊格式，向後相容)
    # python server.py <host> <port>  (新格式，統一標準)
    if len(sys.argv) == 2:
        # 舊格式：只有 port
        port = int(sys.argv[1])
    elif len(sys.argv) == 3:
        # 新格式：host port (忽略 host，因為伺服器總是監聽所有介面)
        port = int(sys.argv[2])
    else:
        print("Usage: python server.py <port> or python server.py <host> <port>")
        sys.exit(1)
    
    server = TicTacToeServer(port)
    server.start()
