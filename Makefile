.PHONY: server lobby_server developer_server client developer_client reset

server:
	@echo "Building server..."
	python -m server.lobby_server.main
	python -m server.developer_server.main

lobby_server:
	@echo "Building lobby server..."
	python -m server.lobby_server.main

developer_server:
	@echo "Building developer server..."
	python -m server.developer_server.main

client:
	@echo "Building client..."
	python -m client.lobby_client.main

developer_client:
	@echo "Building developer client..."
	python -m developer_client.main

reset:
	@echo "Deleting logs and database..."
	rm -rf logs
	rm -rf server/database_server/data
