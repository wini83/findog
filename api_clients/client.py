from abc import ABC, abstractmethod


class Client(ABC):  # pylint: disable=too-few-public-methods

    @abstractmethod
    def login(self):
        """
        Abstract login method
        """
        pass


class NotInitializedError(Exception):
    pass
