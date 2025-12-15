import socket
import sys
import json
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
import time


class NumberBombGUIClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.player_id = None
        self.running = True
        self.game_started = False
        
        # 遊戲狀態
        self.current_number = 0
        self.bomb_number = 21
        self.current_turn = None
        self.players = []
        self.eliminated_players = []
        
        # 創建 GUI
        self.root = tk.Tk()
        self.root.title("💣 Number Bomb Game")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 設置視窗大小
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#2C3E50")
        
        # 標題
        title_label = tk.Label(
            self.root,
            text="💣 Number Bomb 💣",
            font=("Arial", 24, "bold"),
            fg="#E74C3C",
            bg="#2C3E50",
            pady=10
        )
        title_label.pack()
        
        # 狀態標籤
        self.status_label = tk.Label(
            self.root, 
            text="Connecting to server...", 
            font=("Arial", 14),
            fg="#ECF0F1",
            bg="#2C3E50",
            pady=5
        )
        self.status_label.pack()
        
        # 當前數字顯示區域（大字）
        self.number_frame = tk.Frame(self.root, bg="#34495E", bd=5, relief=tk.RAISED)
        self.number_frame.pack(pady=20, padx=20, fill=tk.BOTH)
        
        tk.Label(
            self.number_frame,
            text="Current Number:",
            font=("Arial", 16),
            fg="#BDC3C7",
            bg="#34495E"
        ).pack(pady=(10, 0))
        
        self.current_number_label = tk.Label(
            self.number_frame,
            text="0",
            font=("Arial", 72, "bold"),
            fg="#3498DB",
            bg="#34495E"
        )
        self.current_number_label.pack(pady=10)
        
        # 炸彈數字顯示
        self.bomb_label = tk.Label(
            self.number_frame,
            text="💣 Bomb at: 21",
            font=("Arial", 18, "bold"),
            fg="#E74C3C",
            bg="#34495E"
        )
        self.bomb_label.pack(pady=(0, 10))
        
        # 玩家列表區域
        player_frame = tk.Frame(self.root, bg="#2C3E50")
        player_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(
            player_frame,
            text="Players:",
            font=("Arial", 14, "bold"),
            fg="#ECF0F1",
            bg="#2C3E50"
        ).pack(anchor=tk.W)
        
        self.players_text = tk.Text(
            player_frame,
            height=4,
            font=("Arial", 11),
            bg="#34495E",
            fg="#ECF0F1",
            state=tk.DISABLED,
            bd=2,
            relief=tk.SUNKEN
        )
        self.players_text.pack(fill=tk.X, pady=5)
        
        # 按鈕區域
        self.buttons_frame = tk.Frame(self.root, bg="#2C3E50")
        self.buttons_frame.pack(pady=15)
        
        button_style = {
            "font": ("Arial", 16, "bold"),
            "width": 8,
            "height": 2,
            "bd": 3,
            "relief": tk.RAISED
        }
        
        self.btn_add1 = tk.Button(
            self.buttons_frame,
            text="+1",
            bg="#27AE60",
            fg="white",
            command=lambda: self.send_move(1),
            state=tk.DISABLED,
            **button_style
        )
        self.btn_add1.grid(row=0, column=0, padx=10)
        
        self.btn_add2 = tk.Button(
            self.buttons_frame,
            text="+2",
            bg="#F39C12",
            fg="white",
            command=lambda: self.send_move(2),
            state=tk.DISABLED,
            **button_style
        )
        self.btn_add2.grid(row=0, column=1, padx=10)
        
        self.btn_add3 = tk.Button(
            self.buttons_frame,
            text="+3",
            bg="#E74C3C",
            fg="white",
            command=lambda: self.send_move(3),
            state=tk.DISABLED,
            **button_style
        )
        self.btn_add3.grid(row=0, column=2, padx=10)
        
        # 歷史記錄區域
        history_frame = tk.Frame(self.root, bg="#2C3E50")
        history_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(
            history_frame,
            text="Game History:",
            font=("Arial", 12, "bold"),
            fg="#ECF0F1",
            bg="#2C3E50"
        ).pack(anchor=tk.W)
        
        self.history_text = scrolledtext.ScrolledText(
            history_frame,
            height=8,
            font=("Arial", 10),
            bg="#34495E",
            fg="#ECF0F1",
            state=tk.DISABLED,
            bd=2,
            relief=tk.SUNKEN
        )
        self.history_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def add_history(self, message, color="#ECF0F1"):
        """添加歷史記錄"""
        self.history_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.history_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
    
    def update_players_display(self):
        """更新玩家列表顯示"""
        self.players_text.config(state=tk.NORMAL)
        self.players_text.delete(1.0, tk.END)
        
        for player in self.players:
            if player in self.eliminated_players:
                status = "💀 OUT"
                color = "#E74C3C"
            elif player == self.current_turn:
                status = "👉 YOUR TURN"
                color = "#2ECC71"
            else:
                status = "⏳ Waiting"
                color = "#95A5A6"
            
            self.players_text.insert(tk.END, f"{player}: {status}\n")
        
        self.players_text.config(state=tk.DISABLED)
    
    def update_number_display(self):
        """更新當前數字顯示"""
        self.current_number_label.config(text=str(self.current_number))
        
        # 根據距離炸彈的遠近改變顏色
        distance = self.bomb_number - self.current_number
        if distance <= 3:
            color = "#E74C3C"  # 紅色 - 危險
        elif distance <= 6:
            color = "#F39C12"  # 橙色 - 警告
        else:
            color = "#3498DB"  # 藍色 - 安全
        
        self.current_number_label.config(fg=color)
    
    def enable_buttons(self):
        """啟用按鈕"""
        max_add = self.bomb_number - self.current_number
        
        if max_add >= 1:
            self.btn_add1.config(state=tk.NORMAL)
        else:
            self.btn_add1.config(state=tk.DISABLED)
            
        if max_add >= 2:
            self.btn_add2.config(state=tk.NORMAL)
        else:
            self.btn_add2.config(state=tk.DISABLED)
            
        if max_add >= 3:
            self.btn_add3.config(state=tk.NORMAL)
        else:
            self.btn_add3.config(state=tk.DISABLED)
    
    def disable_buttons(self):
        """禁用按鈕"""
        self.btn_add1.config(state=tk.DISABLED)
        self.btn_add2.config(state=tk.DISABLED)
        self.btn_add3.config(state=tk.DISABLED)
    
    def send_move(self, add_value):
        """發送移動"""
        if not self.running or not self.game_started:
            return
        
        try:
            # 禁用按鈕
            self.disable_buttons()
            
            # 發送移動
            move_packet = {
                "type": "INPUT",
                "data": {"move": add_value}
            }
            self.sock.sendall((json.dumps(move_packet) + "\n").encode())
            
            self.add_history(f"You added +{add_value}")
            
        except Exception as e:
            print(f"Error sending move: {e}")
            self.add_history(f"Error: {e}", "#E74C3C")
    
    def connect_to_server(self):
        """連接到伺服器"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.status_label.config(text="Connected! Waiting for game to start...")
            self.add_history("Connected to server!")
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            self.running = False
            return False
    
    def receive_messages(self):
        """接收伺服器訊息"""
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096).decode()
                if not data:
                    print("Server closed connection")
                    self.running = False
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.handle_message(line)
                        
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
                break
        
        self.root.quit()
    
    def handle_message(self, message):
        """處理伺服器訊息"""
        try:
            packet = json.loads(message)
            packet_type = packet.get("type")
            data = packet.get("data", {})
            
            if packet_type == "INIT":
                self.player_id = data.get("player_id")
                self.status_label.config(text=f"You are: {self.player_id}")
                self.add_history(f"You are {self.player_id}")
                
            elif packet_type == "UPDATE":
                self.handle_update(data)
                
            elif packet_type == "RESULT":
                self.handle_result(data)
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
    
    def handle_update(self, data):
        """處理遊戲狀態更新"""
        self.game_started = True
        
        # 更新遊戲狀態
        self.current_number = data.get("current_number", 0)
        self.bomb_number = data.get("bomb_number", 21)
        self.current_turn = data.get("current_turn")
        self.players = data.get("players", [])
        self.eliminated_players = data.get("eliminated", [])
        
        # 調試輸出
        print(f"UPDATE: current_number={self.current_number}, bomb={self.bomb_number}")
        print(f"UPDATE: current_turn={self.current_turn}, player_id={self.player_id}")
        print(f"UPDATE: players={self.players}, eliminated={self.eliminated_players}")
        
        # 更新顯示
        self.update_number_display()
        self.bomb_label.config(text=f"💣 Bomb at: {self.bomb_number}")
        self.update_players_display()
        
        # 更新狀態標籤
        if self.player_id in self.eliminated_players:
            # 玩家已出局
            self.status_label.config(
                text="💀 You are eliminated!",
                fg="#E74C3C"
            )
            self.disable_buttons()
        elif self.current_turn == self.player_id:
            # 輪到此玩家且未出局
            self.status_label.config(
                text="🎯 YOUR TURN! Choose a number to add:",
                fg="#2ECC71"
            )
            self.enable_buttons()
        else:
            # 等待其他玩家
            self.status_label.config(
                text=f"Waiting for {self.current_turn}...",
                fg="#ECF0F1"
            )
            self.disable_buttons()
        
        # 添加移動歷史
        last_move = data.get("last_move")
        if last_move:
            player = last_move.get("player")
            added = last_move.get("added")
            old_num = last_move.get("old_number")
            new_num = last_move.get("new_number")
            hit_bomb = last_move.get("hit_bomb", False)
            
            if hit_bomb:
                self.add_history(f"💥 {player} added +{added} ({old_num} → {new_num}) and HIT THE BOMB!", "#E74C3C")
            else:
                self.add_history(f"{player} added +{added} ({old_num} → {new_num})")
    
    def handle_result(self, data):
        """處理遊戲結果"""
        winner = data.get("winner")
        loser = data.get("loser")
        final_number = data.get("final_number")
        
        self.disable_buttons()
        
        if loser:
            self.add_history(f"💥 BOOM! {loser} hit the bomb at {final_number}!", "#E74C3C")
            
            if loser == self.player_id:
                self.status_label.config(
                    text="💀 You hit the bomb! You lose!",
                    fg="#E74C3C"
                )
                messagebox.showwarning("Game Over", "💥 You hit the bomb!\nYou lose!")
            else:
                self.status_label.config(
                    text=f"{loser} hit the bomb!",
                    fg="#E74C3C"
                )
        
        if winner:
            self.add_history(f"🎉 {winner} wins the game!", "#2ECC71")
            
            if winner == self.player_id:
                self.status_label.config(
                    text="🎉 YOU WIN!",
                    fg="#2ECC71"
                )
                messagebox.showinfo("Victory!", "🎉 Congratulations!\nYou won!")
            else:
                self.status_label.config(
                    text=f"Game Over - {winner} wins!",
                    fg="#F39C12"
                )
        
        # 延遲關閉
        self.root.after(3000, self.close_game)
    
    def close_game(self):
        """關閉遊戲"""
        self.running = False
        self.root.quit()
    
    def on_closing(self):
        """視窗關閉事件"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.root.destroy()
    
    def start(self):
        """啟動客戶端"""
        if self.connect_to_server():
            # 啟動接收執行緒
            recv_thread = threading.Thread(target=self.receive_messages, daemon=True)
            recv_thread.start()
            
            # 啟動 GUI
            self.root.mainloop()
        
        # 清理
        if self.sock:
            try:
                self.sock.close()
            except:
                pass


def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    client = NumberBombGUIClient(host, port)
    client.start()


if __name__ == "__main__":
    main()
