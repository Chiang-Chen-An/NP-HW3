from .developer_server import DeveloperServer


def main():
    developer_server = DeveloperServer("0.0.0.0", 8081)
    developer_server.start()


if __name__ == "__main__":
    main()
