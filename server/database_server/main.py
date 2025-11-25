from .database_server import DatabaseServer


def main():
    db_server = DatabaseServer(12345, "127.0.0.1")
    db_server.start()


if __name__ == "__main__":
    main()
