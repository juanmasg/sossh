from .printer import Printer
from .list import ListPrinter

class TreePrinter(Printer):
    _step = 2
    _prefixes = ["*", "-", "+", "·"]
    #_prefixes = [ "├", "├", "└"]
    #_prefixes = [ "-┐", "└", "└"]

    def print(self, title, *args, level=0, **kwargs):
        if title:
            print(f"{title}:")

        prefix = f"{(level+1 * self._step)*' '}{self._prefixes[level]}"
        if kwargs:
            for k, v in kwargs.items():
                if v and isinstance(v, list):
                    print(f"{prefix} {k}")
                    self.print("", *v, level=level+1)
                elif v and isinstance(v, dict):
                    print(f"{prefix} {k}")
                    self.print("", level=level+1, **v)
                elif callable(v):
                    print(f"{prefix} {k}: {v()}")
                else:
                    print(f"{prefix} {k}: {v}")
        elif args:
            for k in args:
                print(f"{prefix} {k}")


