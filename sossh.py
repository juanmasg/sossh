import os
import readline


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
            print(f"Unknown command `{cmd}` ({underscored})")
            raise FileNotFoundError

        return self._cmds.get(underscored)

    def read_cmd(self, cmd):
        filename = self._resolve_cmd(cmd)
        return open(filename).read()

    def read_direct(self, filepath):
        return open(filepath).read()

    def run_cmd(self, cmd):
        print(self.read_cmd(cmd))

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

class SosSH:

    #class ARLCompleter:
    #    def __init__(self,logic):
    #        self.logic = logic
    #
    #    def traverse(self,tokens,tree):
    #        if not tree:
    #            return []
    #        elif len(tokens) == 0:
    #            return []
    #        if len(tokens) == 1:
    #            return [x+' ' for x in tree if x.startswith(tokens[0])]
    #        else:
    #            if tokens[0] in tree.keys():
    #                return self.traverse(tokens[1:],tree[tokens[0]])
    #            else:
    #                return []
    #        return []
    #
    #    def complete(self,text,state):
    #        try:
    #            tokens = readline.get_line_buffer().split()
    #            if not tokens or readline.get_line_buffer()[-1] == ' ':
    #                tokens.append()
    #            results = self.traverse(tokens,self.logic) + [None]
    #            return results[state]
    #        except Exception as e:
    #            print(e)

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
            print(f"RET '{ret}'")
            return ret[state]




    _hostname = None
    _version = None
    _fs = None

    def __init__(self, path):
        self._fs = SosFilesystem(path)
        try:
            self._read_version()
            print(f"Sosreport found: {self._version}")
            self._read_hostname()
        except Exception as e:
            print(f"This doesn't seem like a sosreport `{e}`")

        readline.parse_and_bind("tab: complete")
        readline.set_completer(
                SosSH.Completer(self._fs.get_cmd_tree()).complete)

    def _read_version(self):
        data = self._fs.read_direct("version.txt")
        self._version = data.split("\n")[0]

    def _read_hostname(self):
        self._hostname = self._fs.read_direct("hostname")[:-1]

    def loop(self):
        print("LOOP!")
        while True:
            try:
                prompt = f"{self._hostname}) "
                cmd = input(prompt)
                self._fs.run_cmd(cmd)
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
        sosfs = SosFilesystem(args.sos)

        #sosfs.run("ip -d address")

        try:
            sosfs.run_cmd(args.command)
        except FileNotFoundError:
            pass
    else:
        sh = SosSH(args.sos)
        cmd_tree = sh._fs.get_cmd_tree()
        sh.loop()