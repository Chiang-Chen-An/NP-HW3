from .developer_client import DeveloperClient


def main():
    developer_client = DeveloperClient("127.0.0.1", 12345)
    developer_client.start()


if __name__ == "__main__":
    main()
