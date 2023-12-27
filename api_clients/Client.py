from abc import ABC, abstractmethod


class Client(ABC):

    @abstractmethod
    def login(self):
        pass

class NotInitializedError(Exception):
    pass
