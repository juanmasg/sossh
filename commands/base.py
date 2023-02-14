from abc import abstractmethod

class BaseCommand:
    _sos = None
    name = None

    def __init__(self, sos):
        self._sos = sos

    @abstractmethod
    def run(self, *args):
        raise NotImplementedError



