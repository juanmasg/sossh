from .base import BaseCommand
class Help(BaseCommand):
    name = "help"

    def run(self, *args):
        underscored = "_".join(args)
        for cmd in self._sos._cmds:
            if cmd.startswith(underscored):
                print(cmd.replace("_", " "))



