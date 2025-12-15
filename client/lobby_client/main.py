from .lobby_client import LobbyClient


def main():
    lobby_client = LobbyClient("140.113.17.13", 12346)
    lobby_client.start()


if __name__ == "__main__":
    main()
