from .lobby_server import LobbyServer


def main():
    lobby_server = LobbyServer("127.0.0.1", 12346)
    lobby_server.start()


if __name__ == "__main__":
    main()
