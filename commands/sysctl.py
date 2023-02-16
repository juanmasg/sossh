from .base import BaseCommand
from printers.list import ListPrinter

class Sysctl(BaseCommand):
    name = "_sysctl"

    _check = {
            "net.ipv4.icmp_echo_ignore_all": {
                "value": "0",
                "reason": ("When this is enabled, received ICMP messages "
                           "are ignored, including pings")
                },
            "net.ipv4.ip_forward": {
                "value": "1",
                "reason": ("When this is disabled, docker port forwarding, "
                           "forward rules or port redirections won't work")
                },
            "kernel.modules_disabled": {
                "value": "0",
                "reason": ("When this is enabled, kernel modules cannot be "
                           "loaded")
                },
    }

    def run(self, *args):
        sysctl_data = self._sos.run_cmd("sysctl -a")
        sysctl_entries = dict([ [y.strip() for y  in x.split("=", 1)] \
                for x in sysctl_data.split("\n") \
                if x and not x.startswith("sysctl: reading key") ])

        for key, expect in self._check.items():
            if key in sysctl_entries and sysctl_entries[key] != expect["value"]:
                prefix = "CHECK"
            else:
                prefix = " OK  "

            keystr = f"{key} is {sysctl_entries[key]}"
            print(f"[{prefix:5s}] {keystr:36s}: {expect['reason']}")
