import os

from .base import BaseCommand

class Tainted(BaseCommand):
    name = "tainted"

    def run(self, *args):
        tainted_descriptions = {
                "P": "Propietary",
                "O": "Out-of-tree",
                "E": "Unsigned",
                "T": "RandStruct",
                }
        tainted = {}
        for root, dirs, files in self._sos.sosdir.walk("/sys/module"):
            if "taint" in files:
                taintdata = self._sos.sosdir.read(f"{root}/taint")
                if not taintdata:
                    continue

                module = os.path.basename(root)
                tainted[module] = []
                for c in taintdata:
                    tainted[module] = tainted_descriptions.get(c, c)

        return tainted and f"YES: {tainted}" or "NO"


