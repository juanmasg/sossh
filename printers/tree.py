from .printer import Printer

class TreePrinter(Printer):
    _step = 2
    _prefixes = ["*", "-", "+", "·"]
    #_prefixes = [ "├", "├", "└"]
    #_prefixes = [ "-┐", "└", "└"]

    def print(self, title, level=0, *args, **kwargs):
        if title:
            print(f"{title}:")
        prefix = f"{(level+1 * self._step)*' '}{self._prefixes[level]}"
        if kwargs:
            for k, v in kwargs.items():
                print(f"{prefix} {k}")
                if v and isinstance(v, list):
                    self.print("", level+1, *v)
                elif v and isinstance(v, dict):
                    self.print("", level+1, **v)
                elif v:
                    print("TRUCU!")
        elif args:
            for k in args:
                print(f"{prefix} {k}")


