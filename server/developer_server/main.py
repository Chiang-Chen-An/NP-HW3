from .developer_server import DeveloperServer


def main():
    developer_server = DeveloperServer("127.0.0.1", 12345)
    developer_server.start()


if __name__ == "__main__":
    main()
