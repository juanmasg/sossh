from .base import BaseCommand
class Help(BaseCommand):
    name = "help"

    def run(self, *args):
        cmdline = " ".join(args)
        for cmd in self._sos._cmds:
            if cmd.startswith(cmdline):
                print(cmd)



