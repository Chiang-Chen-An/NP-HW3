from .developer_client import DeveloperClient


def main():
    developer_client = DeveloperClient("140.113.17.13", 8081)
    developer_client.start()


if __name__ == "__main__":
    main()
