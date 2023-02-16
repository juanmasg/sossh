from .base import BaseCommand
from printers.tree import TreePrinter
from printers.list import ListPrinter

class SysInfo(BaseCommand):
    name = "sysinfo"

    def run(self, *args):
        dmidecode = self._sos.read("dmidecode")
        lines = dmidecode.split('\n')
        sysinfo = {}
        for i, line in enumerate(lines):
            if line.startswith("System Information"):
                i += 1
                while lines[i].startswith("\t"):
                    text = lines[i].replace("\t", "").replace("\n", "")
                    sysinfo.__setitem__(*[ x.strip() for x in text.split(":", 1)])
                    #sysinfo.append(text)
                    i += 1

                break

        ListPrinter().print("System Information", **sysinfo)
