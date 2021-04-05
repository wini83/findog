from abc import ABC, abstractmethod


class Sumable(ABC):
    def get_whole_sum(self) -> float:
        pass

    @abstractmethod
    def get_unpaid_sum(self) -> float:
        pass
