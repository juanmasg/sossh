#!/usr/bin/python3

import os
import re
import json
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
from commands.sysinfo import SysInfo
from commands.firewalld_explain import FirewalldExplain
from commands.dmidecode import Dmi
from commands.sysctl import Sysctl
from commands.services import Services
from commands.ethtool import Ethtool
from commands.osinfo import OSInfo
from commands.cmdgroup import CmdGroup

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
    _sospath = None
    _cmds = None
    _cmdtree = None

    def __init__(self, root):
        abspath = os.path.abspath(root)
        basename = os.path.basename(abspath)
        self._sospath = basename

        if mimetypes.guess_type(root)[0] == "application/x-tar":
            self.sosdir = SosTarfile(root)
        else:
            self.sosdir = SosDirectory(root)

        self._cmds = {}
        self._cmdtree = {}


    @property
    def _cmdline(self):
        return self.read("/proc/cmdline").strip()

    @property
    def _release(self):
        return self.read("/etc/redhat-release").strip()

    @property
    def _uname(self):
        return self.read("uname").strip()

    @property
    def _uptime(self):
        return self.read("uptime").strip()

    @property
    def _date(self):
        return self.read("date").split("\n")[0].strip()

    @property
    def _version(self):
        ver = self.read("version.txt", remove_last=False).split("\n")
        return ver[0]

    @property
    def _hostname(self):
        return self.read("hostname")


    def read(self, *args, **kwargs):
        return self.sosdir.read(*args, **kwargs)

    def find_manifest_loader(self):
        for _, _, files in self.sosdir.walk("/sos_reports"):
            if "manifest.json" in files:
                return self._cache_cmds_from_manifest_json
            elif "sos.json" in files:
                return self._cache_cmds_from_sos_json
            elif "sos.html" in files:
                return self._cache_cmds_from_sos_html
            elif "sos.txt" in files:
                return self._cache_cmds_from_sos_txt
            else:
                return lambda: print("No manifest found")

    def _cache_cmds_from_sos_html(self):
        from html.parser import HTMLParser
        class SOSHtmlParser(HTMLParser):
            commands = {}
            cur_tag = None
            last_a_href = None

            def handle_starttag(self, tag, attrs):
                self.cur_tag = tag
                if tag == "a":
                    attrs = dict(attrs)
                    if "href" in attrs and "/sos_commands/" in attrs["href"]:
                        self.last_a_href = attrs["href"]

                    
            def handle_data(self, data):
                if self.cur_tag == "a" and self.last_a_href:
                    self.commands[data] = self.last_a_href
                    self.last_a_href = None


        parser = SOSHtmlParser() 
        data = self.sosdir.open("sos_reports/sos.html").read()
        parser.feed(data.decode())
        parser.close()
        for cmd_exec, href in parser.commands.items():
            cmd_filepath = href.split("/", 1)[1]
            self._cmds[cmd_exec] = cmd_filepath
            words = cmd_exec.split(" ")
            tree_cur = self._cmdtree
            for word in words:
                if word not in tree_cur:
                    tree_cur[word] = {}
                tree_cur = tree_cur[word]
            
    def _cache_cmds_from_sos_txt(self):
        mf = self.sosdir.open("/sos_reports/sos.txt").read().decode().split("\n")

        all_sos_commands_files = []
        for root, dirs, files in self.sosdir.walk("sos_commands"):
            for f in files:
                all_sos_commands_files.append(f"{root}/{f}")

        cur_plugin = None
        cur_section = None
        for line in mf:
            line = line.strip()
            if line.startswith("====="):
                continue
            elif line.startswith("-  commands executed"):
                cur_section = "commands"
            elif line.startswith("-  files copied"):
                cur_section = "copied"
            elif line.startswith("-  files created"):
                cur_section = "created"
            elif line.startswith("*"):
                if cur_section != "commands":
                    continue

                cmd_exec = line.split("*", 1)[1].strip()
                cmd_filepath = None
                #filepath = cmd_exec.replace(" ", "_")
                #filepath = filepath.replace(",", "_")
                filepath = re.sub("[ ,]", "_", cmd_exec)
                filepath = re.sub("/", ".", filepath)
                #filepath = filepath.replace("/", ".")
                filepath = re.sub("[\"\'\{\}]", ".", filepath)
                #filepath = filepath.replace('"', "")
                #filepath = filepath.replace("'", "")
                #filepath = filepath.replace("}", "")
                #filepath = filepath.replace("{", "")

                print("CMD EXEC", cmd_exec)
                for f in all_sos_commands_files:
                    #print("F", f, "FILEPATH", filepath)
                    if f.endswith(filepath):
                        cmd_filepath = f
                        break

                if not cmd_filepath:
                    print(f"Couldn't find path for command {cmd_exec}")
                    continue

                self._cmds[cmd_exec] = cmd_filepath

            else:
                #print(f"Don't know how to handle line `{line}`")
                cur_plugin = line
            

    def _cache_cmds_from_sos_json(self):
        mf = json.load(self.sosdir.open("/sos_reports/sos.json"))
        for plugin_data in mf:
            name, plugin = plugin_data
            if not "commands" in plugin:
                continue

            for cmd in plugin["commands"]:
                cmd_exec = cmd["name"]
                cmd_filepath = cmd["href"].split("/", 1)[1]
                self._cmds[cmd_exec] = cmd_filepath
                words = cmd_exec.split(" ")
                tree_cur = self._cmdtree
                for word in words:
                    if word not in tree_cur:
                        tree_cur[word] = {}
                    tree_cur = tree_cur[word]

    def _cache_cmds_from_manifest_json(self):
        mf = json.load(self.sosdir.open("/sos_reports/manifest.json"))
        _ver = mf["version"]
        plugins = mf["components"]["report"]["plugins"]
        for name, plugin in plugins.items():
            for cmd in plugin["commands"]:
                cmd_exec = cmd["exec"]
                cmd_filepath = cmd["filepath"]
                self._cmds[cmd_exec] = cmd_filepath
                words = [cmd["command"]] + cmd["parameters"]
                tree_cur = self._cmdtree
                for word in words:
                    if word not in tree_cur:
                        tree_cur[word] = {}
                    tree_cur = tree_cur[word]

    def _resolve_cmd(self, cmd):
        if cmd not in self._cmds:
            raise FileNotFoundError

        return self._cmds.get(cmd)

    def read_cmd(self, cmd):
        dest = self._resolve_cmd(cmd)
        return self.read(dest)

    def run_cmd(self, cmd):
        return self.read_cmd(cmd.strip())

    def get_cmd_tree(self):
        return self._cmdtree

class SosWrapper(SosReport):

    _internal_cmds = None

    def __init__(self, path):

        super().__init__(path)


        self._internal_cmds = {
            #"links": Links(self).run,
            Cat.name: Cat(self).run,
            Help.name: Help(self).run,
            Tainted.name: Tainted(self).run,
            Drops.name: Drops(self).run,
            Inet.name: Inet(self).run,
            Packages.name: Packages(self).run,
            SysInfo.name: SysInfo(self).run,
            FirewalldExplain.name: FirewalldExplain(self).run,
            Dmi.name: Dmi(self).run,
            Sysctl.name: Sysctl(self).run,
            Services.name: Services(self).run,
            Ethtool.name: Ethtool(self).run,
            OSInfo.name: OSInfo(self).run,
            CmdGroup.name: CmdGroup(self).run,
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

    class TreeCompleter:
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
            ret = self._walk(words, self._tree)
            #while len(ret) == 1:
            #    word = ret[0])
            #    if 
            #    ret[0]
            ret.append(None)
            #print(f"RET '{ret}'")
            return ret[state]


    _histfile = f"{os.environ.get('HOME')}/.sossh_history"

    _sos = None

    def __init__(self, sospath, banner=True):
        self._sos = SosWrapper(sospath)
        try:
            print(f"Sosreport found: {self._sos._version}")
            manifest_loader = self._sos.find_manifest_loader()
            if manifest_loader:
                print(f"Loading manifest {manifest_loader}")
                manifest_loader()
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"This doesn't seem like a sosreport `{e}`")

        readline.parse_and_bind("tab: complete")
        readline.set_completer(
                SosShell.TreeCompleter(self._sos.get_cmd_tree()).complete)
                #SosShell.ListCompleter([ x.replace("_", " ") \
                #        for x in self._sos._cmds.keys()]).complete)

        readline.set_auto_history("True")
        if not os.path.exists(self._histfile):
            open(self._histfile, "w").write("")

        readline.read_history_file(self._histfile)

        if banner:
            self._sos.run_cmd("cmdgroup banner")

    def loop(self):
        while True:
            try:
                prompt = f"\n\033[4m{self._sos._hostname}\033[0m\U0001f198 "
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
            print(output)
            #print(output.decode())
    else:
        sh = SosShell(args.sospath, banner=not args.no_banner)
        sh.loop()
