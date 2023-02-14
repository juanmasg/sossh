import re
from .base import BaseCommand
from printers.tree import TreePrinter

class Inet(BaseCommand):
    name = "inet"

    def run(self, *args):

        ifaces = {}

        for line in self._sos.read("ip_addr").split("\n"):
            if "inet " not in line:
                continue
            i, name, inet = \
                re.match("^([0-9]+): (.*) inet ([^ ]+) .*", line).groups()
            if name not in ifaces:
                ifaces[name] = []

            ifaces[name].append(inet)

        TreePrinter().print("Inet", **ifaces)


