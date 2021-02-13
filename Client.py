import string
from abc import ABC


class Client(ABC):
    def retrieve_file(self, file_path: string) -> bytes:
        pass

    def commit_file(self, file: bytes, file_path: string):
        pass
