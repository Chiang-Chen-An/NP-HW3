# 遊戲商店系統 - 使用說明

## 快速開始

### 1. 啟動伺服器

在伺服器端（140.113.17.13）執行：

```bash
# 啟動所有 server
./start_server.sh

# 關掉所有 server
./stop_server.sh

# 啟動資料庫伺服器
make database_server

# 啟動開發者伺服器
make developer_server

# 啟動大廳伺服器
make lobby_server
```

### 2. 使用客戶端

在客戶端執行：

```bash
# 虛擬環境
conda create -n nphw3 python=3.13
conda activate nphw3

# 啟動大廳客戶端（玩家）
make client

# 啟動開發者客戶端（遊戲開發者）
make developer_client
```
