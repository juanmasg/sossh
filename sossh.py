import os
import readline
import subprocess


class SosFilesystem:

    _path = None

    _cmds = {}

    def __init__(self, path):
        self._path = path
        self._cmds = {}
        self._cache_cmds(path)

    def _cache_cmds(self, path):
        for root, dirs, files in os.walk(f"{self._path}/sos_commands"):
            for filename in files:
                self._cmds[filename] = f"{root}/{filename}"


    def _resolve_cmd(self, cmd):
        underscored = " ".join([x for x in cmd.split(" ") if x]).replace(" ", "_")

        if underscored not in self._cmds:
            #print(f"Unknown command `{cmd}` ({underscored})")
            raise FileNotFoundError

        return self._cmds.get(underscored)

    def read_cmd(self, cmd):
        dest = self._resolve_cmd(cmd)
        if callable(dest):
            return dest(*cmd.split(" ")[1:])
        else:
            return open(dest).read()[:-1]

    def read_direct(self, filepath):
        return open(f"{self._path}/{filepath}").read()

    def run_cmd(self, cmd):
        try:
            return self.read_cmd(cmd)
        except FileNotFoundError:
            print(f"Command not found or options required `{cmd}`")
            cmd = cmd.strip()
            matching = [ c for c in self._cmds if c.startswith(cmd) ]
            for m in matching:
                print(m.replace("_", " "))

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


class SosfsWrapper(SosFilesystem):

    _internal_cmds = None

    def __init__(self, path):

        super().__init__(path)

        self._internal_cmds = {}

        self._internal_cmds["help"] = self._cmd_help
        for cmd in self._cmds:
            cmd0 = cmd.split("_", 1)[0]
            self._internal_cmds[f"help_{cmd0}"] = lambda x: self._cmd_help(x)
            #self._internal_cmds[f"help_{cmd}"] = lambda *args: self._cmd_help(x)

        self._cmds.update(self._internal_cmds)
        print(self._cmds)

    def _cmd_help(self, *args):
        print("CMDHELP", args)
        for cmd in sorted(self._cmds.keys()):
            if cmd.startswith(" ".join(args)):
                print(" ".join(cmd.split("_")))
            


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




    _hostname = None
    _version = None
    _fs = None

    def __init__(self, path):
        self._fs = SosfsWrapper(path)
        try:
            self._read_version()
            print(f"Sosreport found: {self._version}")
            self._read_hostname()
        except Exception as e:
            print(f"This doesn't seem like a sosreport `{e}`")

        readline.parse_and_bind("tab: complete")
        readline.set_completer(
                SosShell.Completer(self._fs.get_cmd_tree()).complete)

    def _read_version(self):
        data = self._fs.read_direct("version.txt")
        self._version = data.split("\n")[0]

    def _read_hostname(self):
        self._hostname = self._fs.read_direct("hostname")[:-1]

    def loop(self):
        while True:
            try:
                prompt = f"{self._hostname}) "
                cmd = input(prompt)
                shell_pipe = None
                if "|" in cmd:
                    cmd, shell_pipe = [ x.strip() for x in cmd.split("|",1) ]
                cmd_output = self._fs.run_cmd(cmd)
                if shell_pipe:
                    subprocess.run(shell_pipe,
                            input=cmd_output.encode(), shell=True)
                else:
                    print(cmd_output)
            except EOFError:
                print("EOF!")
                return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-S", "--sos")
    parser.add_argument("-c", "--command")
    args = parser.parse_args()

    if args.command:
        sosfs = SosFilesystem(args.sos) #SosFilesystem(args.sos)

        #sosfs.run("ip -d address")

        try:
            print(sosfs.run_cmd(args.command))
        except FileNotFoundError:
            pass
    else:
        sh = SosShell(args.sos)
        cmd_tree = sh._fs.get_cmd_tree()
        sh.loop()
