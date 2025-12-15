from .database_server import DatabaseServer


def main():
    db_server = DatabaseServer(12345, "140.113.17.13")
    db_server.start()


if __name__ == "__main__":
    main()
