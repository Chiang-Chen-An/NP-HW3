import socket
import sys
import json
import threading
import tkinter as tk
from tkinter import messagebox


class TicTacToeGUIClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.player_id = None
        self.running = True
        self.my_turn = False
        self.game_started = False
        self.board = [" " for _ in range(9)]
        
        # 創建 GUI
        self.root = tk.Tk()
        self.root.title("Tic Tac Toe")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 設置視窗大小
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # 狀態標籤
        self.status_label = tk.Label(
            self.root, 
            text="Connecting to server...", 
            font=("Arial", 14),
            pady=10
        )
        self.status_label.pack()
        
        # 玩家資訊標籤
        self.player_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
            pady=5
        )
        self.player_label.pack()
        
        # 遊戲板框架
        self.board_frame = tk.Frame(self.root)
        self.board_frame.pack(pady=20)
        
        # 創建 9 個按鈕
        self.buttons = []
        for i in range(3):
            row = []
            for j in range(3):
                btn = tk.Button(
                    self.board_frame,
                    text=" ",
                    font=("Arial", 24, "bold"),
                    width=5,
                    height=2,
                    command=lambda pos=i*3+j: self.make_move(pos),
                    state="disabled"
                )
                btn.grid(row=i, column=j, padx=5, pady=5)
                row.append(btn)
            self.buttons.extend(row)

    def start(self):
        """連接伺服器並啟動 GUI"""
        try:
            # 連接伺服器
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 重試連接
            import time
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    print(f"[DEBUG] Attempting to connect to {self.host}:{self.port}!!!!!")
                    self.sock.connect((self.host, self.port))
                    print(f"[DEBUG] Connected successfully!")
                    self.update_status("Connected to game server!")
                    break
                except ConnectionRefusedError:
                    if attempt < max_retries - 1:
                        self.update_status(f"Connection attempt {attempt + 1}...")
                        time.sleep(1)
                    else:
                        raise
            
            # 測試：立即嘗試接收一點資料
            print("[DEBUG] Testing socket - setting timeout...")
            self.sock.settimeout(2.0)
            try:
                test_data = self.sock.recv(10, socket.MSG_PEEK)
                print(f"[DEBUG] Peek test: {repr(test_data)}")
            except socket.timeout:
                print("[DEBUG] Peek test: timeout (no immediate data)")
            except Exception as e:
                print(f"[DEBUG] Peek test error: {e}")
            finally:
                self.sock.settimeout(None)  # 恢復阻塞模式
            
            # 啟動接收線程
            print("[DEBUG] Starting receive thread...")
            recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
            recv_thread.start()
            print(f"[DEBUG] Receive thread started: {recv_thread.is_alive()}")
            
            # 確保線程有時間啟動
            import time
            time.sleep(0.1)
            
            print("[DEBUG] Starting GUI mainloop...")
            # 啟動 GUI
            self.root.mainloop()
            print("[DEBUG] GUI mainloop ended")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
        finally:
            if self.sock:
                self.sock.close()

    def receive_loop(self):
        """接收伺服器訊息"""
        print("[DEBUG] receive_loop started")
        buffer = ""
        while self.running:
            try:
                print("[DEBUG] Waiting to receive data...")
                data = self.sock.recv(1024).decode()
                print(f"[DEBUG] Received raw data: {repr(data)}")
                if not data:
                    print("[DEBUG] No data received, server disconnected")
                    self.root.after(0, lambda: self.update_status("Server disconnected"))
                    self.running = False
                    break

                buffer += data
                print(f"[DEBUG] Buffer now: {repr(buffer)}")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    print(f"[DEBUG] Processing line: {line}")
                    self.handle_message(json.loads(line))
            except Exception as e:
                if self.running:
                    print(f"[DEBUG] Error receiving data: {e}")
                    import traceback
                    traceback.print_exc()
                self.running = False
                break
        print("[DEBUG] receive_loop ended")

    def handle_message(self, msg):
        """處理伺服器訊息"""
        print(f"[DEBUG] Received message: {msg}")  # 添加調試輸出
        
        if msg["type"] == "WELCOME":
            self.player_id = msg["player_id"]
            symbol = 'X' if self.player_id == 0 else 'O'
            print(f"[DEBUG] Player ID set to: {self.player_id}")
            self.root.after(0, lambda: self.player_label.config(
                text=f"You are Player {self.player_id + 1} ({symbol})"
            ))
            if self.player_id == 0:
                self.root.after(0, lambda: self.update_status("You go first! Waiting for opponent..."))
            else:
                self.root.after(0, lambda: self.update_status("Waiting for opponent to start..."))
        
        elif msg["type"] == "UPDATE":
            print(f"[DEBUG] UPDATE received. player_id={self.player_id}, current_turn={msg.get('current_turn')}")
            
            if not self.game_started:
                self.game_started = True
                self.root.after(0, lambda: self.update_status("Game Started!"))
            
            self.board = msg["board"]
            self.root.after(0, self.update_board_display)
            
            if "winner" in msg:
                if msg["winner"] == "DRAW":
                    self.root.after(0, lambda: self.show_game_over("It's a Draw!"))
                else:
                    self.root.after(0, lambda: self.show_game_over(f"{msg['winner']} Wins!"))
                self.running = False
                self.my_turn = False
            else:
                if msg["current_turn"] == self.player_id:
                    print(f"[DEBUG] It's my turn!")
                    self.my_turn = True
                    self.root.after(0, lambda: self.update_status("Your turn! Click a square."))
                    self.root.after(0, self.enable_buttons)
                else:
                    print(f"[DEBUG] Waiting for opponent...")
                    self.my_turn = False
                    self.root.after(0, lambda: self.update_status("Waiting for opponent's move..."))
                    self.root.after(0, self.disable_buttons)
        
        elif msg["type"] == "ERROR":
            self.root.after(0, lambda: messagebox.showwarning("Error", msg["message"]))

    def update_board_display(self):
        """更新棋盤顯示"""
        for i, value in enumerate(self.board):
            self.buttons[i].config(text=value if value != " " else " ")
            # 設置顏色
            if value == "X":
                self.buttons[i].config(fg="blue")
            elif value == "O":
                self.buttons[i].config(fg="red")

    def make_move(self, position):
        """玩家下棋"""
        if not self.my_turn:
            return
        
        if self.board[position] != " ":
            messagebox.showwarning("Invalid Move", "This square is already taken!")
            return
        
        try:
            self.sock.sendall(
                json.dumps({"type": "MOVE", "position": position}).encode() + b"\n"
            )
            self.my_turn = False
            self.disable_buttons()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send move: {e}")

    def enable_buttons(self):
        """啟用可用的按鈕"""
        for i, btn in enumerate(self.buttons):
            if self.board[i] == " ":
                btn.config(state="normal")

    def disable_buttons(self):
        """禁用所有按鈕"""
        for btn in self.buttons:
            btn.config(state="disabled")

    def update_status(self, message):
        """更新狀態標籤"""
        self.status_label.config(text=message)

    def show_game_over(self, message):
        """顯示遊戲結束訊息"""
        self.update_status(f"Game Over! {message}")
        self.disable_buttons()
        messagebox.showinfo("Game Over", message)

    def on_closing(self):
        """關閉視窗時的處理"""
        self.running = False
        if self.sock:
            self.sock.close()
        self.root.destroy()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    client = TicTacToeGUIClient(host, port)
    client.start()
