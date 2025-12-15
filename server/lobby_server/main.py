from .lobby_server import LobbyServer


def main():
    lobby_server = LobbyServer("0.0.0.0", 12346)
    lobby_server.start()


if __name__ == "__main__":
    main()
