import os
from textwrap import wrap
from .base import BaseCommand
from printers.list import ListPrinter

class OSInfo(BaseCommand):
    name = "osinfo"

    def run(self, *args):

        try:
            cols = os.get_terminal_size().columns
        except OSError:
            # most probably being piped
            cols = 80

        data = {
            "Path": self._sos._sospath,
            "Generated": self._sos._date,
            "Hostname": self._sos._hostname,
            "Uname": self._sos._uname,
            "Uptime": self._sos._uptime,
            "Cmdline": "\n".join(wrap(self._sos._cmdline,
                width=cols-15, subsequent_indent=15*" ")),
            "Release": self._sos._release,
            "Tainted": self._sos.run_cmd("tainted"),
        }

        ListPrinter().print("OS Information", **data)
