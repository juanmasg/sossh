from .base import BaseCommand

class CmdGroup(BaseCommand):
    name = "cmdgroup"

    _groups = {
            "banner": [ "osinfo", "dmi", "inet"],
            "net": [ "inet", "firewalld_explain", "ethtool"],
            }

    def run(self, name, *args):
        if name not in self._groups:
            print(f"No such group `{name}`")
            return

        for cmd in self._groups[name]:
            self._sos.run_cmd(cmd)
            print("")

