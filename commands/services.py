from .base import BaseCommand
from printers.list import ListPrinter
from printers.tree import TreePrinter

class Services(BaseCommand):
    name = "_services"

    _well_known_security_av_services = [
        "ds_agent.service",
        "sav-protect.service",
        "autoprotect.service",
        "rtvscand.service",
        "falcon-sensor.service",
        "openonload.service",
        "cbdaemon.service",
        "sisipsdaemon.service",
        "sisidsdaemon.service",
        "mcafee.ma.service",
        "mfeespd.service",
        "mfefwd.service",
        "mfetpd.service"
    ]

    def run(self, *args):

        systemctl_status_data = self._sos.run_cmd("systemctl status --all")

        all_services = {}
        cur_service = None
        for line in systemctl_status_data.split("\n"):
            line = line.strip()
            if line.startswith("* "):
                if cur_service:
                    all_services[cur_service["name"]] = cur_service
                if " - " in line:
                    name, desc = [x.strip() for x in line[2:].split(" - ",1)]
                else:
                    name = line[2:].strip()
                    desc = ""
                cur_service = {
                        "name": name,
                        "desc": desc,
                        }
                continue


            if not cur_service:
                continue

            if line.startswith("Loaded: "):
                cur_service["loaded"] = line.split(": ", 1)[1]
            elif line.startswith("Active: "):
                cur_service["active"] = line.split(": ", 1)[1]

        found_security_av_services = {}
        for s in self._well_known_security_av_services:
            if s in all_services:
                found_security_av_services[s] = all_services[s]

        TreePrinter().print("Security services", **found_security_av_services)
