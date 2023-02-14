#!/usr/bin/python3

import os
import re
import readline
import subprocess
import mimetypes
import tarfile

import ipaddress

from commands.base import BaseCommand
from commands.inet import Inet
from commands.cat import Cat
from commands.help import Help
from commands.tainted import Tainted
from commands.packages import Packages

#from interface import InterfaceGroup

#class Links(BaseCommand):
#    name = "links"
#
#    def run(self, *args):
#        data = self._sos.read("/sos_commands/networking/ip_-d_address")
#        group = InterfaceGroup.new_from_ip_d_address(data)
#        group.print_tree()


class Drops(BaseCommand):
    name = "drops"

    def run(self, *args):
        pass



class SosDirectory:

    _root = None

    def __init__(self, path):
        self._root = path

    def walk(self, path):
        for root, dirs, files in os.walk(f"{self._root}/{path}"):
            yield root.replace(self._root, ""), dirs, files

    def open(self, path):
        return open(f"{self._root}/{path}", "rb")

    def read(self, filepath, remove_last=True):
        data = self.open(filepath).read().decode()
        return data[:-1] if remove_last else data


class SosTarfile(SosDirectory):

    _root = None
    _tarroot = None
    _walked = False

    def __init__(self, root):
        self._root = tarfile.open(root, "r:xz")
        self._tarroot = self._root.next().name

    def _fixpath(self, path):
        return "/".join([x for x in path.split("/") if x ])

    def walk(self, path):
        if not self._walked:
            print(("Reading tarfile for the first time. "
                    "This might take a while..."))

        root = self._fixpath(f"{self._tarroot}/{path}")
        tree = {}
        for x in self._root.getmembers():
            if not x.name.startswith(root):
                continue

            if x.isfile():
                d, f = x.name.rsplit("/", 1)
                d = d.split("/", 1)[1]
                if d not in tree:
                    tree[d] = []

                tree[d].append(f)
            
        for k, v in tree.items():
            yield k, [], v

        self._walked = True

    def open(self, path):
        filepath = self._fixpath(f"{self._tarroot}/{path}")
        return self._root.extractfile(filepath)


class SosReport:

    sosdir = None
    _cmds = {}

    def __init__(self, root):

        if mimetypes.guess_type(root)[0] == "application/x-tar":
            self.sosdir = SosTarfile(root)
        else:
            self.sosdir = SosDirectory(root)

        self._cmds = {}
        self._cache_cmds(root)

    def read(self, *args, **kwargs):
        return self.sosdir.read(*args, **kwargs)

    def _cache_cmds(self, path):
        for root, dirs, files in self.sosdir.walk("/sos_commands"):
            for filename in files:
                self._cmds[filename] = f"{root}/{filename}"

    def _underscored(self, cmd):
        return " ".join([x for x in cmd.split(" ") if x]).replace(" ", "_")

    def _resolve_cmd(self, cmd):
        underscored = self._underscored(cmd)

        if underscored not in self._cmds:
            #print(f"Unknown command `{cmd}` ({underscored})")
            raise FileNotFoundError

        return self._cmds.get(underscored)

    def read_cmd(self, cmd):
        dest = self._resolve_cmd(cmd)
        #if callable(dest):
        #    return dest(*cmd.split(" ")[1:])
        #else:
        return self.read(dest)

    def run_cmd(self, cmd):
        return self.read_cmd(cmd)

    def get_cmd_tree(self):
        tree = {}
        for cmd in self._cmds.keys():
            words = cmd.split("_")
            cur = tree
            for i, word in enumerate(words):
                if word not in cur:
                    cur[word] = {}
                cur = cur[word]

        #import json
        #print(json.dumps(tree, indent=2))
        return tree

class SosWrapper(SosReport):

    _internal_cmds = None

    def __init__(self, path):

        super().__init__(path)

        self._internal_cmds = {
            #"links": Links(self).run,
            "cat": Cat(self).run,
            "help": Help(self).run,
            "tainted": Tainted(self).run,
            "drops": Drops(self).run,
            "inet": Inet(self).run,
            "packages": Packages(self).run,
        }

        self._cmds.update(self._internal_cmds)

    def read_cmd(self, cmd):
        args = cmd.strip().split(" ", 1)
        if len(args) == 1:
            cmd0 = args[0]
            args = ""
        else:
            cmd0, args = args
            
        if cmd0 in self._internal_cmds:
            return self._internal_cmds[cmd0](*args.split(" "))
        else:
            return super().read_cmd(cmd)


class SosShell:

    class Completer:
        _tree = None
        def __init__(self, tree):
            self._tree = tree

        def _walk(self, words, tree):
            #print("WALK!", words, tree.keys())
            if not tree:
                return []
            elif len(words) == 0:
                return [x for x in tree.keys()]

            if words[0] in tree:
                return self._walk(words[1:], tree[words[0]])
            elif len(words) == 1:
                return [x+" " for x in tree if x.startswith(words[0])]
            else:
                return []

            return []

        def complete(self, text, state):
            words = [x for x in readline.get_line_buffer().split(" ") if x ]
            #print(f"WORDS '{words}'")
            ret = self._walk(words, self._tree) + [None]
            #print(f"RET '{ret}'")
            return ret[state]



    _histfile = f"{os.environ.get('HOME')}/.sossh_history"

    _hostname = None
    _version = None
    _date = None
    _uname = None
    _uptime = None
    _cmdline = None
    _release = None

    _sos = None
    _sospath = None

    def __init__(self, sospath, banner=True):
        self._sospath = sospath
        self._sos = SosWrapper(sospath)
        try:
            self._read_version()
            print(f"Sosreport found: {self._version}")
            self._read_hostname()
            self._read_date()
            self._read_uname()
            self._read_uptime()
            self._read_cmdline()
            self._read_release()
        except Exception as e:
            print(f"This doesn't seem like a sosreport `{e}`")

        readline.parse_and_bind("tab: complete")
        readline.set_completer(
                SosShell.Completer(self._sos.get_cmd_tree()).complete)

        readline.set_auto_history("True")
        if not os.path.exists(self._histfile):
            open(self._histfile, "w").write("")

        readline.read_history_file(self._histfile)

        if banner:
            self.banner()

    def banner(self):

        banner_data = {
            "Path": self._sospath,
            "Generated": self._date,
            "Hostname": self._hostname,
            "Uname": self._uname,
            "Uptime": self._uptime,
            "Cmdline": self._cmdline,
            "Release": self._release,
            "Tainted": self._sos.run_cmd("tainted"),
        }

        print("")
        for k, v in banner_data.items():
            print(f"  {k:16s}: {v.strip()}")

        print("")

    def _read_cmdline(self):
        self._cmdline = self._sos.read("/proc/cmdline")

    def _read_release(self):
        self._release = self._sos.read("/etc/redhat-release")

    def _read_uname(self):
        self._uname = self._sos.read("uname")

    def _read_uptime(self):
        self._uptime = self._sos.read("uptime")

    def _read_date(self):
        self._date = self._sos.read("date").split("\n")[0]

    def _read_version(self):
        self._version = self._sos.read("version.txt", remove_last=False)

    def _read_hostname(self):
        self._hostname = self._sos.read("hostname")

    def loop(self):
        while True:
            try:
                prompt = f"\033[4m{self._hostname}\033[0m\U0001f198 "
                cmd = input(prompt)
                shell_pipe = None
                if "|" in cmd:
                    cmd, shell_pipe = [ x.strip() for x in cmd.split("|",1) ]
                cmd_output = self._sos.run_cmd(cmd)

                if not cmd_output:
                    continue

                if shell_pipe:
                    subprocess.run(shell_pipe,
                            input=cmd_output.encode(), shell=True)
                else:
                    print(cmd_output)

                readline.write_history_file(self._histfile)

            except FileNotFoundError:
                print(f"Command not found or options required `{cmd}`")
                cmd = cmd.strip()
                self._sos.run_cmd(f"help {cmd}")

            except EOFError:
                print("EOF!")
                return

            except KeyboardInterrupt: # Ctrl+c
                print("")

            except Exception as e:
                import traceback; traceback.print_exc()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("sospath")
    parser.add_argument("-N", "--no-banner", action="store_true")
    parser.add_argument("-c", "--command")
    args = parser.parse_args()

    if args.command:
        sos = SosWrapper(args.sospath)
        output = sos.run_cmd(args.command)
        if output:
            print(output.decode())
    else:
        sh = SosShell(args.sospath, banner=not args.no_banner)
        sh.loop()
