import socket
import sys
import json
import threading


class TicTacToeClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.player_id = None
        self.running = True
        self.my_turn = False
        self.game_started = False

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Retry connection a few times in case server is still starting
            import time
            max_retries = 3
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
                print(f"Error receiving data: {e}")
                self.running = False
                break

    def handle_message(self, msg):
        if msg["type"] == "WELCOME":
            self.player_id = msg["player_id"]
            symbol = 'X' if self.player_id == 0 else 'O'
            print(f"\n{'='*50}")
            print(f"You are Player {self.player_id} ({symbol})")
            print(f"{'='*50}")
            if self.player_id == 0:
                print("You go first! Waiting for opponent to join...")
            else:
                print("Waiting for opponent to start...")
            print("\nGame will start automatically when both players are ready.")
            print("Enter position (0-8) when it's your turn:")
            print("\n  0 | 1 | 2")
            print(" -----------")
            print("  3 | 4 | 5")
            print(" -----------")
            print("  6 | 7 | 8\n")
        elif msg["type"] == "UPDATE":
            if not self.game_started:
                self.game_started = True
                print("\n🎮 Game Started! 🎮\n")
            
            self.print_board(msg["board"])
            
            if "winner" in msg:
                if msg["winner"] == "DRAW":
                    print("\n" + "="*50)
                    print("Game Over! It's a Draw!")
                    print("="*50 + "\n")
                else:
                    print("\n" + "="*50)
                    print(f"🎉 Game Over! {msg['winner']} Wins! 🎉")
                    print("="*50 + "\n")
                self.running = False
                self.my_turn = False
                print("Press Enter to exit...")
            else:
                if msg["current_turn"] == self.player_id:
                    self.my_turn = True
                    print(">>> Your turn! Enter position (0-8): ", end='', flush=True)
                else:
                    self.my_turn = False
                    print("⏳ Waiting for opponent's move...\n")
        elif msg["type"] == "ERROR":
            print(f"❌ Error: {msg['message']}")
            if self.my_turn:
                print(">>> Your turn! Enter position (0-8): ", end='', flush=True)

    def print_board(self, board):
        print("\n")
        print(f" {board[0]} | {board[1]} | {board[2]} ")
        print("---+---+---")
        print(f" {board[3]} | {board[4]} | {board[5]} ")
        print("---+---+---")
        print(f" {board[6]} | {board[7]} | {board[8]} ")
        print("\n")

    def input_loop(self):
        while self.running:
            try:
                move = input()
                if not self.running:
                    break
                
                # 忽略空輸入
                if not move.strip():
                    continue
                
                # 檢查是否是玩家的回合
                if not self.my_turn:
                    # 靜默忽略，不顯示錯誤訊息
                    continue
                
                if not move.isdigit() or not (0 <= int(move) <= 8):
                    print("❌ Invalid input. Enter 0-8.")
                    print(">>> Your turn! Enter position (0-8): ", end='', flush=True)
                    continue

                self.sock.sendall(
                    json.dumps({"type": "MOVE", "position": int(move)}).encode() + b"\n"
                )
            except EOFError:
                break
            except Exception as e:
                if self.running:
                    print(f"Error sending move: {e}")
            except Exception as e:
                print(f"Error sending move: {e}")
                break


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <server_ip> <server_port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    client = TicTacToeClient(host, port)
    client.start()
