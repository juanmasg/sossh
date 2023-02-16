from .printer import Printer

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
                print(f"{prefix} {k}")
                if v and isinstance(v, list):
                    self.print("", *v, level=level+1)
                elif v and isinstance(v, dict):
                    self.print("", level=level+1, **v)
                elif callable(v):
                    print(v())
                elif isinstance(v, str):
                    print(v)
                elif v:
                    print(v)
                else:
                    print("NO V!", v)
        elif args:
            for k in args:
                print(f"{prefix} {k}")


