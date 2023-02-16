from .base import BaseCommand
from printers.tree import TreePrinter
from printers.list import ListPrinter
import json

class Dmi(BaseCommand):
    name = "dmi"

    def _parse_level(into, data, lvl):
        pass

    def run(self, *args):
        dmidecode_data = self._sos.read("dmidecode")

        dmidecode = {}
        cur_lvl = {}
        cur_handle = None
        for line in dmidecode_data.split("\n"):
            lvl = line.count("\t")
            line = line.strip()
            if not line: continue

            if line.startswith("Handle"):
                if line == cur_handle:
                    # Duplicated handle
                    cur_handle = f"{cur_handle} #2"
                else:
                    cur_handle = line
                continue
            #print(f"ORIG LINE: '{line}'", "LVL", lvl)
            #print("CURLVLS", cur_lvl)
            #print("CUR", json.dumps(dmidecode))
            line = line.replace("\t", "")
            if lvl == 0: # main
                line = f"{line} - {cur_handle}"
                cur_lvl[0] = line
                if line not in dmidecode:
                    dmidecode[line] = {}
                else:
                    print("DUPE!", line, json.dumps(dmidecode[line],
                        indent=2))


            elif lvl == 1:
                cur_lvl[1] = line
                lvl0 = cur_lvl[0]
                if ": " in line:
                    dmidecode[lvl0].__setitem__(*[ x.strip() for x in
                        line.split(": ")])
                else:
                    dmidecode[lvl0][line] = {}

            elif lvl == 2:
                cur_lvl[2] = line
                lvl0 = cur_lvl[0]
                lvl1 = cur_lvl[1]
                try:
                    dmidecode[lvl0][lvl1][line] = None
                except:
                    pass
                    #import traceback; traceback.print_exc()

            else:
                print("LVL!", lvl)


        #print(json.dumps(list(dmidecode.keys()), indent=2))
        #print("DMiDECODE", json.dumps(dmidecode, indent=2))

        data = {
            "System Information": {},
            "Processors": {
                "Populated": 0,
                "Enabled": 0,
            }
        }
        for k, v in dmidecode.items():
            if k.startswith("System Information - "):
                data["System Information"] = v
            elif k.startswith("Processor Information"):
                if v["Status"].startswith("Populated, Enabled"):
                    data["Processors"]["Populated"] += 1
                    data["Processors"]["Enabled"] += 1
                elif v["Status"].startswith("Populated, Disabled"):
                    data["Processors"]["Populated"] += 1
                
        ListPrinter().print(
                "System Information", **data["System Information"])
        print("")
        ListPrinter().print(
                "Processors", **data["Processors"])
