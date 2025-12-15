import socket
import sys
import json
import threading


class RockPaperScissorsClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.player_id = None
        self.running = True
        self.my_turn = False
        self.game_started = False
        self.wins = 0
        self.losses = 0
        self.ties = 0

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Retry connection
            import time
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    self.sock.connect((self.host, self.port))
                    print(f"Connected to game server at {self.host}:{self.port}")
                    break
                except ConnectionRefusedError:
                    if attempt < max_retries - 1:
                        print(f"Connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(1)
                    else:
                        raise

            # Start receive thread
            threading.Thread(target=self.receive_loop, daemon=True).start()

            # Input loop
            self.input_loop()

        except Exception as e:
            print(f"Connection failed: {e}")
        finally:
            self.sock.close()

    def receive_loop(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024).decode()
                if not data:
                    print("Server disconnected.")
                    self.running = False
                    break

                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_message(json.loads(line))
            except Exception as e:
                if self.running:
                    print(f"Error receiving data: {e}")
                self.running = False
                break

    def handle_message(self, msg):
        if msg["type"] == "WELCOME":
            self.player_id = msg["player_id"]
            print(f"\n{'='*50}")
            print(f"You are Player {self.player_id + 1}")
            print(f"{'='*50}")
            if self.player_id == 0:
                print("Waiting for opponent to join...")
            print("\nGame will start when both players are ready.")
            print("\nRock Paper Scissors - Best of 5 Rounds!")
            print("Commands:")
            print("  r or rock     - Play Rock")
            print("  p or paper    - Play Paper")
            print("  s or scissors - Play Scissors")
            print("="*50 + "\n")
        
        elif msg["type"] == "ROUND_START":
            if not self.game_started:
                self.game_started = True
                print("\n🎮 Game Started! 🎮\n")
            
            round_num = msg["round"]
            print(f"\n{'='*50}")
            print(f"ROUND {round_num}".center(50))
            print(f"{'='*50}")
            self.my_turn = True
            print(">>> Your turn! Enter your choice (r/p/s): ", end='', flush=True)
        
        elif msg["type"] == "ROUND_RESULT":
            print(f"\n{'='*50}")
            print("ROUND RESULT".center(50))
            print(f"{'='*50}")
            
            choices = msg["choices"]
            result = msg["result"]
            
            # 顯示雙方選擇
            print(f"Player 1 chose: {choices[0]}")
            print(f"Player 2 chose: {choices[1]}")
            print()
            
            # 顯示結果
            if result == "TIE":
                print("🤝 It's a TIE!")
                self.ties += 1
            elif result == f"PLAYER_{self.player_id}":
                print("🎉 You WIN this round!")
                self.wins += 1
            else:
                print("😢 You LOSE this round!")
                self.losses += 1
            
            # 顯示當前比分
            print(f"\nCurrent Score:")
            print(f"  Wins: {self.wins} | Losses: {self.losses} | Ties: {self.ties}")
            print(f"{'='*50}\n")
            
            self.my_turn = False
        
        elif msg["type"] == "GAME_OVER":
            print(f"\n{'='*50}")
            print("GAME OVER".center(50))
            print(f"{'='*50}")
            
            winner = msg["winner"]
            final_scores = msg["scores"]
            
            print(f"Player 1 - Wins: {final_scores[0]}")
            print(f"Player 2 - Wins: {final_scores[1]}")
            print()
            
            if winner == "TIE":
                print("🤝 The game is a TIE!")
            elif winner == f"PLAYER_{self.player_id}":
                print("🎉🎉🎉 YOU WIN THE GAME! 🎉🎉🎉")
            else:
                print("😢 You lost the game. Better luck next time!")
            
            print(f"{'='*50}\n")
            print("Press Enter to exit...")
            self.running = False
            self.my_turn = False
        
        elif msg["type"] == "ERROR":
            print(f"❌ Error: {msg['message']}")
            if self.my_turn:
                print(">>> Your turn! Enter your choice (r/p/s): ", end='', flush=True)
        
        elif msg["type"] == "WAITING":
            print(f"⏳ {msg['message']}")

    def input_loop(self):
        while self.running:
            try:
                choice = input().strip().lower()
                if not self.running:
                    break
                
                # 忽略空輸入
                if not choice:
                    continue
                
                # 檢查是否是玩家的回合
                if not self.my_turn:
                    continue
                
                # 解析輸入
                move = None
                if choice in ['r', 'rock']:
                    move = "ROCK"
                elif choice in ['p', 'paper']:
                    move = "PAPER"
                elif choice in ['s', 'scissors']:
                    move = "SCISSORS"
                else:
                    print("❌ Invalid input. Use r/rock, p/paper, or s/scissors")
                    print(">>> Your turn! Enter your choice (r/p/s): ", end='', flush=True)
                    continue

                self.sock.sendall(
                    json.dumps({"type": "MOVE", "choice": move}).encode() + b"\n"
                )
                self.my_turn = False
                print("⏳ Waiting for opponent...")
                
            except EOFError:
                break
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")
                break


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    client = RockPaperScissorsClient(host, port)
    client.start()
