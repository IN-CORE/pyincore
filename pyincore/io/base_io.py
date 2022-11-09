from abc import ABC, abstractmethod


class BaseIO(ABC):
    @classmethod
    @abstractmethod
    def read(cls, *args):
        pass

    @classmethod
    @abstractmethod
    def write(cls, *args):
        pass
