#!/usr/bin/python3

import os
import sys
import re
import json



class EthtoolDriver:

    name = None
    version = None
    firmware = None
    expansion_rom = None
    bus_info = None

    @staticmethod
    def new_from_sos(sos, name):
        driver = EthtoolDriver()
        path = f"{sos}/sos_commands/networking/ethtool_-i_{name}"
        d = dict([ x.split(": ",1) for x in open(path).read().split('\n') if x ])
        driver.name = d.get("driver")
        driver.version = d.get("version")
        driver.firmware = d.get("firmware-version")
        driver.expansion_rom = d.get("expansion-rom-version")
        driver.bus_info = d.get("bus-info")

        return driver

class Ethtool:
    driver = None

    def __init__(self, sos, name):
        self.driver = EthtoolDriver.new_from_sos(sos, name)


class InterfaceGroup:

    ifaces = None

    def __init__(self):
        self.ifaces = {}

    def get(self, name):
        return self.ifaces[name]

    def add(self, iface):
        self.ifaces[iface.name] = iface

    @staticmethod
    def new_from_sos(sos):

        group = InterfaceGroup()

        path = f"{sos}/sos_commands/networking/ip_-d_address"

        lines = []
        for line in [ x for x in open(path).read().split("\n") if x ]:
            if line[0].isdigit():
                if lines:
                    iface = Interface.new_from_lines(lines)
                    iface.ethtool_from_sos(sos)
                    group.add(iface)
                lines = [line]
            else:
                lines.append(line)

        iface = Interface.new_from_lines(lines)
        iface.ethtool_from_sos(sos)
        group.add(iface)

        return group

    def _get_name_tree(self):
        tree = {}
        #master_ifaces = set([i.master for i in self.ifaces.values() if i.master])

        for name, i in self.ifaces.items():
            if i.master:
                if i.master in tree:
                    tree[i.master][name] = {}
                else:
                    tree[i.master] = { name: {} }
            else:
                if name not in tree:
                    tree[name] = {}

        return tree

    def print_tree0(self):
        print(json.dumps(self._get_name_tree(), indent=2))

    def print_tree(self):
        def print_one_level(tree, prefix, child_prefix, last_prefix, indent=0):
            i = 0
            for name, children in tree.items():
                i += 1
                iface = self.ifaces[name]
                this_prefix = prefix if i < len(tree) else last_prefix
                pre = f'{(" " * indent)} {this_prefix}'
                pre2= f'{(" " * indent)} │'
                main = f"{pre} {name}"
                print(f"{main:16s}: {iface.details()}")
                #print(f"{pre2} trucu trala")
                #print(f"{pre2}")
                if children:
                    print_one_level(children, prefix, child_prefix,
                            last_prefix, indent+1)

        tree = self._get_name_tree()
        print_one_level(tree, "├", "├", "└")
        #print_one_level(tree, "└", "└", "└")


    def print_dot(self):
        filename = "/tmp/ip-link-tree.gv"

        try:
            import graphviz
        except Exception as e:
            print(f"Cannot build dot file because \"graphviz\" is not available: {e}")
            print(f"Hint: `python -m pip install graphviz --user`")
            print(f"You might also need to install the system package: `yum install -y graphviz`")
            return False

        dot = graphviz.Digraph(comment="", format="svg")
        #dot.graph_attr['rankdir'] = 'LR'
        dot.graph_attr['rankdir'] = 'UD'

        state_color = {
                "UP": "green",
                "DOWN": "red",
                "LOWERLAYERDOWN": "red",
                "UNKNOWN": "black",
                "": "black",
                }

        for ifname, iface in self.ifaces.items():
            shape = "box" if iface.vlan_proto else "doubleoctagon" 
            bgcolor = state_color[iface.state]
            dot.node(ifname,
                    label=iface.dot_label(),
                    shape="box",
                    color=bgcolor)

            if iface.master:
                dot.node(iface.master,
                        self.ifaces[iface.master].dot_label(),
                        shape="egg")

                dot.edge(iface.master, ifname)
                #if iface.bond:
                #    dot.edge(iface.master, ifname)
                #elif iface.vlan_proto:
                #    dot.edge(ifname, iface.master)
                #else:
                #    dot.edge(ifname, iface.master)

            if iface.parent:
                dot.node(iface.parent,
                        self.ifaces[iface.parent].dot_label(),
                        shape="egg")

                dot.edge(ifname, iface.parent)

        dot.render(filename, view=True)


    def debug(self):
        for iface in self.ifaces.values():
            print(str(iface))

class Interface:
    idx = None
    name = None
    mac = None
    flags = None
    mtu = None
    master = None
    parent = None
    state = None
    vlan_proto = None
    vlan_id = None
    inet = None
    inet6 = None
    bond = None

    ethtool = None

    def __init__(self):
        self.flags = []
        self.inet = []
        self.inet6 = []
        self.bond = {}

    @staticmethod
    def new_from_lines(lines):

        i = Interface()

        i.idx, i.name, i.flags, i.mtu, i.master, i.state = \
            re.match(('^([0-9]+)\: ([^:]+)\: <([^>]+)> mtu '
                      '([0-9]+) (?:qdisc [^ ]+)? ?(?:master ([^ ]+))? '
                      '?(?:state ([^ ]+))? .*$'), lines[0]).groups()
    
        if '@' in i.name:
            i.name, i.parent = i.name.split('@')

        i.flags = i.flags.split(",")

        i.mtu = int(i.mtu)
    
        for line in lines[1:]:
            line = line.strip()

            if line.startswith("link/ether"):
                i.mac = line.split(' ')[1]

            elif line.startswith("link/loopback"):
                i.mac = line.split(' ')[1]
    
            elif line.startswith("vlan "):
                words = line.split(' ')
                i.vlan_proto = words[2]
                i.vlan_id = int(words[4])

            elif line.startswith("inet "):
                i.inet.append(line.split(' ')[1])

            elif line.startswith("inet6 "):
                i.inet6.append(line.split(' ')[1])

            elif line.startswith("bond "):
                bond_mode = line.split(' ')[2] #re.match('^bond mode ([^ ]+)', line).groups()
                i.bond["mode"] = bond_mode

            elif line.startswith("bond_slave"):
                bond_state = line.split(' ')[2]
                i.bond["state"] = bond_state

            elif line.startswith("valid_lft"):
                pass

            else:
                pass #;print(f"OTHER PROPS \"{line}\"")

        return i

    def ethtool_from_sos(self, sos):
        self.ethtool = Ethtool(sos, self.name)

    def details(self):
        l2 = ",".join([x for x in self.flags \
                if x not in ("BROADCAST", "MULTICAST", "LOOPBACK")])

        if l2: l2 = f"({l2})"

        state = self.state
        if state == "UNKNOWN" and "LOOPBACK" in self.flags:
            state = "LOOPBACK"

        l2 = f"{state:8s} {self.mtu:-5d} {self.mac or '':18s} {l2:24s}"

        l25 = ""
        if self.vlan_proto:
            l25 = f"{self.vlan_proto}({self.vlan_id})"

        lbond = ""
        if self.bond:
            if "mode" in self.bond:
                lbond = self.bond["mode"]
            elif "state" in self.bond:
                lbond = self.bond["state"]
            else:
                lbond = str(self.bond)

        l3 = ",".join(self.inet)

        return f"{l2} {l25:14s} {lbond:12s} {l3}"

    def dot_label(self):
        return "\n".join([
                f"{self.name}",
                f"({self.state})",
                ",".join(self.inet),
            ])

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)



if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-S", "--sos")
    #parser.add_argument("-A", "--ip-d-address")
    parser.add_argument("-d", "--dump-ifaces", action="store_true")
    parser.add_argument("-D", "--dot", action="store_true")

    args = parser.parse_args()

    #if args.sos:
    #    path = f"{args.sos}/sos_commands/networking/ip_-d_address"
    #elif args.ip_d_address:
    #    path = args.ip_d_address

    if not args.sos:
        print("No sosreport path provided.")
        sys.exit(0)

    group = InterfaceGroup.new_from_sos(args.sos)
    if args.dump_ifaces:
        group.debug()

    #group.print_tree()
    group.print_dot()

