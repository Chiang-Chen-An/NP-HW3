import os
import json

data_dir = "server/database_server/data"
files = ["users.json", "games.json", "developers.json"]

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

for file in files:
    path = os.path.join(data_dir, file)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
        print(f"Created {path}")
    else:
        print(f"{path} already exists")
