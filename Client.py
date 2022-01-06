import string
from abc import ABC, abstractmethod


class Client(ABC):

    @abstractmethod
    def login(self):
        pass
