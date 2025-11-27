from .lobby_client import LobbyClient


def main():
    lobby_client = LobbyClient("127.0.0.1", 12346)
    lobby_client.start()


if __name__ == "__main__":
    main()
