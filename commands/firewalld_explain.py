from .base import BaseCommand

class FirewalldExplain(BaseCommand):
    name = "firewalld_explain"

    def run(self, *args):
        import sys
        import shutil
        import importlib.util

        bin_name = "firewalld-explain.py"
        bin_path = shutil.which(bin_name)
        if not bin_path:
            print(f"Not found in path `{bin_name}`")
            return



        spec = importlib.util.spec_from_file_location("explain", bin_path)
        explain = importlib.util.module_from_spec(spec)
        sys.modules["explain"] = explain
        spec.loader.exec_module(explain)

        zones = self._sos.run_cmd("firewall-cmd --list-all-zones")
        if "FirewallD is not running" in zones:
            print(zones)
            return

        conf = self._sos.read("/etc/firewalld/firewalld.conf")
        firewalld = explain.DataFirewalld(zones, conf)
        firewalld.explain_table()
