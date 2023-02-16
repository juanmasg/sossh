from .base import BaseCommand
from printers.list import ListPrinter

class Banner(BaseCommand):
    name = "banner"

    def run(self, *args):

        print("")
        ListPrinter().print("OS Information", **data)
        print("")
        #self._sos.run_cmd("sysinfo")
        self._sos.run_cmd("dmi")
        print("")
        self._sos.run_cmd("inet")
