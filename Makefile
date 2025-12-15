.PHONY: server lobby_server developer_server client developer_client reset init help

help:
	@echo "Game Store System - Makefile Commands"
	@echo "======================================"
	@echo "make init              - Initialize database files"
	@echo "make lobby_server      - Start Lobby Server (Port 12346)"
	@echo "make developer_server  - Start Developer Server (Port 8081)"
	@echo "make client            - Start Player Client"
	@echo "make developer_client  - Start Developer Client"
	@echo "make reset             - Delete logs and database (clean slate)"
	@echo "make help              - Show this help message"

init:
	@echo "Initializing database..."
	python3 init_db.py
	@echo "Creating storage directory..."
	mkdir -p server/storage
	@echo "Creating logs directory..."
	mkdir -p logs
	@echo "Initialization complete!"

server:
	@echo "Building server..."
	python3 -m server.lobby_server.main
	python3 -m server.developer_server.main

lobby_server:
	@echo "Starting Lobby Server on port 12346..."
	python3 -m server.lobby_server.main

developer_server:
	@echo "Starting Developer Server on port 8081..."
	python3 -m server.developer_server.main

client:
	@echo "Starting Player Client..."
	python3 -m client.lobby_client.main

developer_client:
	@echo "Starting Developer Client..."
	python3 -m developer_client.main

reset:
	@echo "WARNING: This will delete all data!"
	@echo "Deleting logs and database..."
	rm -rf logs
	rm -rf server/database_server/data
	@echo "Reinitializing..."
	@make init
