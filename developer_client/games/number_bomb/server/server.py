import socket
import json
import threading
import random
import time
import os
import logging
from datetime import datetime


class NumberBombServer:
    def __init__(self, host, port, max_players):
        self.host = host
        self.port = port
        self.max_players = max_players
        self.clients = {}  # {player_id: socket}
        self.players = []  # 玩家列表
        self.eliminated_players = []  # 出局的玩家
        self.running = True
        self.game_started = False
        
        # 遊戲狀態
        self.current_number = 0
        self.bomb_number = 21  # 預設炸彈數字
        self.current_turn_index = 0
        self.lock = threading.Lock()
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # 設置日誌
        self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        # 創建 logs/game_logs 目錄
        log_dir = "logs/game_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 創建日誌文件名（包含時間戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"number_bomb_{timestamp}_{self.port}.log")
        
        # 配置日誌
        self.logger = logging.getLogger(f"NumberBomb_{self.port}")
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
        self.logger.info(f"Number Bomb server initialized on port {self.port} for {self.max_players} players")
        
    def start(self):
        """啟動伺服器"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            print(f"Number Bomb Server started on {self.host}:{self.port}")
            print(f"Waiting for {self.max_players} players...")
            self.logger.info(f"Number Bomb Server started on {self.host}:{self.port}")
            self.logger.info(f"Waiting for {self.max_players} players...")
            
            # 接受玩家連線
            while len(self.clients) < self.max_players and self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_sock, addr = self.server_socket.accept()
                    player_id = f"Player{len(self.clients) + 1}"
                    
                    with self.lock:
                        self.clients[player_id] = client_sock
                        self.players.append(player_id)
                    
                    print(f"{player_id} connected from {addr}")
                    self.logger.info(f"{player_id} connected from {addr}")
                    
                    # 發送初始化訊息
                    init_packet = {
                        "type": "INIT",
                        "data": {"player_id": player_id}
                    }
                    self.send_to_client(client_sock, init_packet)
                    
                    # 啟動客戶端處理執行緒
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(player_id, client_sock),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    break
            
            # 開始遊戲
            if len(self.clients) == self.max_players:
                print(f"\nAll {self.max_players} players connected!")
                print("Starting game...")
                self.logger.info(f"All {self.max_players} players connected! Starting game...")
                time.sleep(1)
                self.start_game()
                
                # 保持伺服器運行直到遊戲結束
                while self.running:
                    time.sleep(0.5)
            
        except Exception as e:
            print(f"Server error: {e}")
            self.logger.error(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def start_game(self):
        """開始遊戲"""
        with self.lock:
            self.game_started = True
            self.current_number = 0
            
            # 隨機炸彈數字（15-30之間）
            self.bomb_number = random.randint(15, 30)
            print(f"Bomb number set to: {self.bomb_number}")
            
            # 隨機選擇第一個玩家
            self.current_turn_index = random.randint(0, len(self.players) - 1)
            
            # 發送初始遊戲狀態
            self.broadcast_update()
    
    def handle_client(self, player_id, client_sock):
        """處理客戶端訊息"""
        buffer = ""
        try:
            while self.running:
                data = client_sock.recv(4096).decode()
                if not data:
                    print(f"{player_id} disconnected")
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.handle_message(player_id, line)
                        
        except Exception as e:
            print(f"Error handling {player_id}: {e}")
        finally:
            self.remove_player(player_id)
    
    def handle_message(self, player_id, message):
        """處理玩家訊息"""
        try:
            packet = json.loads(message)
            packet_type = packet.get("type")
            data = packet.get("data", {})
            
            if packet_type == "INPUT":
                self.handle_move(player_id, data.get("move"))
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error from {player_id}: {e}")
    
    def handle_move(self, player_id, add_value):
        """處理玩家移動"""
        with self.lock:
            # 檢查是否是當前玩家的回合
            if not self.game_started:
                return
            
            current_player = self.players[self.current_turn_index]
            if player_id != current_player:
                print(f"{player_id} tried to move but it's not their turn")
                return
            
            # 檢查是否已出局
            if player_id in self.eliminated_players:
                return
            
            # 驗證移動是否有效
            if add_value not in [1, 2, 3]:
                return
            
            old_number = self.current_number
            new_number = self.current_number + add_value
            
            # 檢查是否超過炸彈數字
            if new_number > self.bomb_number:
                print(f"{player_id} tried to add {add_value} but would exceed bomb number")
                return
            
            self.current_number = new_number
            print(f"{player_id} added +{add_value}: {old_number} → {new_number}")
            
            # 檢查是否踩到炸彈
            if self.current_number == self.bomb_number:
                print(f"💥 {player_id} hit the bomb!")
                self.eliminated_players.append(player_id)
                
                # 先廣播踩到炸彈的狀態（數字還是炸彈數字）
                self.broadcast_update(last_move={
                    "player": player_id,
                    "added": add_value,
                    "old_number": old_number,
                    "new_number": new_number,
                    "hit_bomb": True
                })
                
                # 檢查是否只剩一個玩家
                remaining_players = [p for p in self.players if p not in self.eliminated_players]
                
                if len(remaining_players) <= 1:
                    # 遊戲結束
                    winner = remaining_players[0] if remaining_players else None
                    time.sleep(1)  # 讓玩家看到炸彈效果
                    self.send_game_result(winner, player_id, self.current_number)
                    self.running = False
                else:
                    # 繼續遊戲，等待一下讓玩家看到出局訊息
                    time.sleep(2)
                    
                    # 重置數字和炸彈
                    self.current_number = 0
                    self.bomb_number = random.randint(15, 30)
                    print(f"New round! Bomb number set to: {self.bomb_number}")
                    
                    # 跳到下一個還在遊戲中的玩家
                    self.move_to_next_player()
                    
                    # 廣播新回合開始
                    self.broadcast_update()
            else:
                # 移動到下一個玩家
                self.move_to_next_player()
                self.broadcast_update(last_move={
                    "player": player_id,
                    "added": add_value,
                    "old_number": old_number,
                    "new_number": new_number
                })
    
    def move_to_next_player(self):
        """移動到下一個還在遊戲中的玩家"""
        attempts = 0
        while attempts < len(self.players):
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            current_player = self.players[self.current_turn_index]
            if current_player not in self.eliminated_players:
                break
            attempts += 1
    
    def broadcast_update(self, last_move=None):
        """廣播遊戲狀態更新"""
        current_player = self.players[self.current_turn_index]
        
        update_data = {
            "current_number": self.current_number,
            "bomb_number": self.bomb_number,
            "current_turn": current_player,
            "players": self.players,
            "eliminated": self.eliminated_players
        }
        
        if last_move:
            update_data["last_move"] = last_move
        
        update_packet = {
            "type": "UPDATE",
            "data": update_data
        }
        
        self.broadcast(update_packet)
    
    def send_game_result(self, winner, loser, final_number):
        """發送遊戲結果"""
        result_packet = {
            "type": "RESULT",
            "data": {
                "winner": winner,
                "loser": loser,
                "final_number": final_number
            }
        }
        
        self.broadcast(result_packet)
        print(f"\n=== Game Over ===")
        if winner:
            print(f"Winner: {winner}")
        print(f"Loser: {loser} (hit bomb at {final_number})")
    
    def broadcast(self, packet):
        """廣播訊息給所有客戶端"""
        message = json.dumps(packet) + "\n"
        disconnected = []
        
        for player_id, client_sock in list(self.clients.items()):
            try:
                client_sock.sendall(message.encode())
            except Exception as e:
                print(f"Error sending to {player_id}: {e}")
                disconnected.append(player_id)
        
        # 移除斷線的客戶端
        for player_id in disconnected:
            self.remove_player(player_id)
    
    def send_to_client(self, client_sock, packet):
        """發送訊息給特定客戶端"""
        try:
            message = json.dumps(packet) + "\n"
            client_sock.sendall(message.encode())
        except Exception as e:
            print(f"Error sending to client: {e}")
    
    def remove_player(self, player_id):
        """移除玩家"""
        with self.lock:
            if player_id in self.clients:
                try:
                    self.clients[player_id].close()
                except:
                    pass
                del self.clients[player_id]
                print(f"{player_id} removed from game")
    
    def cleanup(self):
        """清理資源"""
        print("\nShutting down server...")
        self.running = False
        
        for client_sock in self.clients.values():
            try:
                client_sock.close()
            except:
                pass
        
        try:
            self.server_socket.close()
        except:
            pass
        
        print("Server stopped")


def main():
    import sys
    import json
    import os
    
    if len(sys.argv) != 3:
        print("Usage: python server.py <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    # 從 config.json 讀取 max_players
    config_path = os.path.join(os.path.dirname(__file__), "../config.json")
    max_players = 4  # 預設值
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                max_players = config.get("max_players", 4)
                print(f"Loaded max_players from config: {max_players}")
        except Exception as e:
            print(f"Error reading config.json: {e}, using default max_players=4")
    
    server = NumberBombServer(host, port, max_players)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
        server.cleanup()


if __name__ == "__main__":
    main()
