import json
import os

from p2p.application import AuthRepo


class FileAuthRepo(AuthRepo):
    def __init__(self, f_name: str) -> None:
        self._f_name = f_name

    def save(self, uuid: str, auth_data: dict):
        with open(self._f_name, "w+") as f:
            f.write(json.dumps(auth_data))

    def read(self, uuid: str) -> dict:
        if os.path.exists(self._f_name):
            with open(self._f_name, "r+") as f:
                raw = f.read()
                if len(raw) > 0:
                    return json.loads(raw)
        return {}
