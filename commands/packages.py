from .base import BaseCommand
from printers.tree import TreePrinter

class Packages(BaseCommand):
    name = "packages"

    _ignore_vendors = ["Red Hat, Inc."]

    def run(self, *args):
        package_data = self._sos.run_cmd("package-data")
        vendors = {}
        for pkg in package_data.split("\n"):
            words = pkg.split("\t")
            vendor = words[3]
            name = words[0]
            if vendor in self._ignore_vendors:
                continue

            if vendor not in vendors:
                vendors[vendor] = []

            vendors[vendor].append(name)

        if vendors:
            TreePrinter().print("Third party packages installed", **vendors)
        #    print("Third party packages installed:")
        #for vendor, pkgs in vendors.items():
        #    print(f" * {vendor}")
        #    for pkg in pkgs:
        #        print(f"   - {pkg}")

        return b""

