from .printer import Printer

class ListPrinter(Printer):

    def print(self, title, *args, **kwargs):
        if title:
            print(f"{title}:")
        if kwargs:
            longest = max([len(x) for x in kwargs])

            for k, v in kwargs.items():
                k = f'{k}:'
                print(f"  {k:{longest+2}} {v}")

        
