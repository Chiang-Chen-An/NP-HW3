import socket
import sys
import threading
import json
import os
import logging
from datetime import datetime


class RockPaperScissorsServer:
    def __init__(self, port):
        self.host = "0.0.0.0"
        self.port = port
        self.players = []
        self.lock = threading.Lock()
        self.choices = [None, None]  # Store player choices
        self.scores = [0, 0]  # Win counts for each player
        self.current_round = 0
        self.max_rounds = 5
        self.game_over = False
        self.ready_count = 0
        
        # 設置日誌
        self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        # 創建 logs/game_logs 目錄
        log_dir = "logs/game_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 創建日誌文件名（包含時間戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"rock_paper_scissors_{timestamp}_{self.port}.log")
        
        # 配置日誌
        self.logger = logging.getLogger(f"RPS_{self.port}")
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
        self.logger.info(f"Rock Paper Scissors server initialized on port {self.port}")

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
        
        # 當兩個玩家都連接後，開始第一回合
        import time
        time.sleep(0.5)
        print("Both players connected. Starting game!")
        self.logger.info("Both players connected. Starting game!")
        self.start_new_round()
        
        # 保持伺服器運行直到遊戲結束
        while not self.game_over:
            time.sleep(0.1)
        
        print("Game ended. Server shutting down.")
        self.logger.info("Game ended. Server shutting down.")
        time.sleep(1)  # 給客戶端時間接收最後的訊息
        server.close()

    def handle_client(self, conn, player_id):
        # Send welcome message
        conn.sendall(
            json.dumps({"type": "WELCOME", "player_id": player_id}).encode() + b"\n"
        )
        self.logger.info(f"Sent WELCOME message to player {player_id}")

        while not self.game_over:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                msg = json.loads(data.decode().strip())

                if msg["type"] == "MOVE":
                    self.process_move(player_id, msg["choice"])

            except Exception as e:
                print(f"Error handling client {player_id}: {e}")
                break

        conn.close()

    def start_new_round(self):
        """開始新的一回合"""
        with self.lock:
            if self.game_over:
                return
            
            self.current_round += 1
            self.choices = [None, None]
            self.ready_count = 0
            
            print(f"Starting round {self.current_round}")
            self.logger.info(f"Starting round {self.current_round}")
            
            # 廣播回合開始
            msg = {
                "type": "ROUND_START",
                "round": self.current_round
            }
            self.broadcast(msg)

    def process_move(self, player_id, choice):
        """處理玩家的選擇"""
        with self.lock:
            if self.game_over:
                return
            
            # 檢查玩家是否已經選擇
            if self.choices[player_id] is not None:
                self.send_to_player(player_id, {
                    "type": "ERROR",
                    "message": "You have already made your choice for this round"
                })
                return
            
            # 記錄選擇
            self.choices[player_id] = choice
            self.ready_count += 1
            
            print(f"Player {player_id} chose {choice}")
            self.logger.info(f"Player {player_id} chose {choice}")
            
            # 如果還沒兩個玩家都選擇，通知等待
            if self.ready_count < 2:
                self.send_to_player(player_id, {
                    "type": "WAITING",
                    "message": "Waiting for opponent..."
                })
                return
            
            # 兩個玩家都選擇了，判定結果
            self.logger.info("Both players have chosen. Determining winner...")
            self.determine_winner()

    def determine_winner(self):
        """判定回合勝負"""
        choice0 = self.choices[0]
        choice1 = self.choices[1]
        
        print(f"Round {self.current_round}: {choice0} vs {choice1}")
        self.logger.info(f"Round {self.current_round}: {choice0} vs {choice1}")
        
        # 判定邏輯
        if choice0 == choice1:
            result = "TIE"
        elif (choice0 == "ROCK" and choice1 == "SCISSORS") or \
             (choice0 == "PAPER" and choice1 == "ROCK") or \
             (choice0 == "SCISSORS" and choice1 == "PAPER"):
            result = "PLAYER_0"
            self.scores[0] += 1
        else:
            result = "PLAYER_1"
            self.scores[1] += 1
        
        print(f"Result: {result}, Scores: {self.scores}")
        self.logger.info(f"Result: {result}, Scores: {self.scores}")
        
        # 廣播回合結果
        result_msg = {
            "type": "ROUND_RESULT",
            "round": self.current_round,
            "choices": [choice0, choice1],
            "result": result,
            "scores": self.scores.copy()
        }
        self.broadcast(result_msg)
        
        # 檢查遊戲是否結束
        should_continue = not (
            self.current_round >= self.max_rounds or
            self.scores[0] > self.max_rounds // 2 or
            self.scores[1] > self.max_rounds // 2
        )
        
        # 使用線程來延遲並開始下一回合，避免持有鎖太久
        import threading
        import time
        
        def delayed_action():
            time.sleep(2)  # 讓玩家看到結果
            if should_continue:
                self.start_new_round()
            else:
                self.end_game()
        
        threading.Thread(target=delayed_action, daemon=True).start()

    def end_game(self):
        """結束遊戲"""
        with self.lock:
            self.game_over = True
            
            # 判定最終勝者
            if self.scores[0] > self.scores[1]:
                winner = "PLAYER_0"
            elif self.scores[1] > self.scores[0]:
                winner = "PLAYER_1"
            else:
                winner = "TIE"
            
            print(f"Game Over! Winner: {winner}, Final Scores: {self.scores}")
            self.logger.info(f"Game Over! Winner: {winner}, Final Scores: {self.scores}")
            
            # 廣播遊戲結束
            game_over_msg = {
                "type": "GAME_OVER",
                "winner": winner,
                "scores": self.scores.copy()
            }
            self.broadcast(game_over_msg)

    def broadcast(self, message):
        """廣播訊息給所有玩家"""
        data = json.dumps(message).encode() + b"\n"
        for p in self.players:
            try:
                p.sendall(data)
            except:
                pass

    def send_to_player(self, player_id, message):
        """發送訊息給特定玩家"""
        try:
            data = json.dumps(message).encode() + b"\n"
            self.players[player_id].sendall(data)
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
    
    server = RockPaperScissorsServer(port)
    server.start()
