import json, struct, socket


class Packet:
    def __init__(self, type: str, data: dict):
        self.type = type
        self.data = data

    def to_bytes(self):
        payload = self.data.copy()
        payload["type"] = self.type
        json_str = json.dumps(payload)
        json_bytes = json_str.encode("utf-8")

        header = struct.pack("!I", len(json_bytes))
        return header + json_bytes

    @staticmethod
    def receive(sock: socket.socket):
        try:
            header_bytes = recv_all(sock, 4)
            if not header_bytes:
                return None
            body_length = struct.unpack("!I", header_bytes)[0]
            body_bytes = recv_all(sock, body_length)
            if not body_bytes:
                return None
            json_str = body_bytes.decode("utf-8")
            data_dict = json.loads(json_str)

            return Packet(data_dict["type"], data_dict)

        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None


def recv_all(sock: socket.socket, n: int):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
