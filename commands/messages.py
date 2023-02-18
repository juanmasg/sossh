from .base import BaseCommand

class Messages(BaseCommand):
    name = "messages"

    def run(self, *args):
        messages = self._sos.read("/var/log/messages")
        for line in messages.split("\n"):
            if " systemd" in line:
                continue

            print(line)
