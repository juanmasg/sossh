from .base import BaseCommand
class Cat(BaseCommand):
    name = "cat"

    def run(self, *args):
        for arg in args:
            data = self._sos.read(arg)
            print(data)


