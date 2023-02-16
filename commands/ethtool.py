import re
from .base import BaseCommand

class Ethtool(BaseCommand):
    name = "ethtool_stats"

    _driver_ok_regex = {
                "802.1Q": None,
                "be2net": '[tx]q[0-9]*: [tr]x(_mcast)?_(bytes|pkts|compl|reqs)',
                "bnx2": '[rt]x_?(ucast|mcast|bcast|[0-9]*_to_[0-9]*_byte|[0-9]*_byte)?_(bytes|packets)',
                "bnx2x": '[tr]x_([1-9_to]*)?(u|m|b)cast|octet|byte(s|_packets)|tpa_aggregat(ions|ed_frames)',
                "bnxt_en": '([rt]x_(bits|bytes)|([rt]x_([umb]cast|total|good|[0-9b_]*))_(bytes|packets|frames)|tpa_(packets|bytes|events|aborts)|[rt]x_(packets|bytes)_(pri|cos)[0-9]*):',
                "bridge": None,
                "bonding": None,
                "cdc_eem": None,
                "cdc_ether": None,
                "e1000": '[tr]x_(packets|bytes|broadcast|multicast|long_byte_count|csum_offload_good|tcp_seg_good):',
                "ena": 'queue_[0-9]*_[rt]x_(bytes|cnt|tx_poll):',
                "i40e": '[rt]x[-0-9\._]*(packets|bytes|(uni|multi|broad)cast)|port.[tr]x_size_[0-9]*',
                "ixgbe": '[rt]x(_queue_[0-9]*)?_(packets|bytes|pkts_nic)|(broad|multi)cast',
                "igb": '[tr]x_(queue_[0-9]*_)?(packets|bytes|broadcast|multicast)|multicast',
                "hv_netvsc": '[rt]x_queue_[0-9]*_(packets|bytes)|cpu[0-9]*_[rt]x_(packets|bytes):',
                "enic": '[rt]x_(frames_[0-9]*|(multicast|unicast|broadcast)?_?(bytes|frames)_(ok|total|to_max)):',
                "iavf": '[rt]x[-_0-9\.]*(bytes|packets|unicast|multicast|broadcast)',
                "macvlan": None,
                "mlx4_en": '^ *(vport_)?[rt]x[0-9]*(_multicast|_novlan|_unicast)?_(bytes|packets|csum_good|alloc_pages|lro_aggregated|lro_flushed)|^ *multicast: ',
                "mlx5_core": '(ch|[rt]x)[0-9]*_((poll|arm|events|xdp|tso_inner|tso|mac_control|broadcast|multicast|cache_empty)_)?(packets|bytes|xmit|cqes|phy)?',
                "netxen_nic": 'xmit_(called|finished)|csummed|([rt]x|lro)_(pkts|bytes)',
                "openvswitch": None,
                "qede": '[tr]x_([umb]cast|[0-9_to]*)_(pkts|bytes|byte_packets)|rcv_pkts',
                "qmi_wwan": None,
                "sfc": '[tr]x-[0-9]*.[rt]x_packets|port_[rt]x_(bytes|packets|(broad|multi|uni)cast)|good|[0-9]*_to_[0-9]*',
                "team": None,
                "tg3": '[tr]x_([0-9_to]*)?(u|m|b)cast|octet(s|_packets)',
                "tun": None,
                "veth": 'peer_ifindex',
                "vif": None,
                "virtio_net": None,
                "vmxnet3": '(LRO|TSO|ucast|bcast|mcast) (pkts|bytes?) [rt]x|[TR]x Queue#: [0-9]|pkts linearized: |hdr cloned: ',
                "vrouter": None,
                "vxlan": None,
            }

    def run(self, *args):
        ifaces = {}
        for iface in self._sos.get_cmd_tree()["ethtool"]["-i"]:
            ethtool_i = self._sos.read_cmd(f"ethtool -i {iface}")
            d = dict([[z.strip() for z in x.split(":", 1) ] for x in ethtool_i.split("\n")])
            ifaces[iface] = { "info": d }

        for iface in ifaces.keys():
            if "driver" in ifaces[iface]["info"]:
                driver = ifaces[iface]["info"]["driver"]
                stats = self._sos.read_cmd(f"ethtool -S {iface}")
                if driver not in self._driver_ok_regex:
                    # unsupported (most probably it doesn't provide stats
                    print(f"No regex available for driver `{driver}`. Showing all")
                    print(stats)
                    continue 

                if self._driver_ok_regex[driver] is None:
                    # The driver doesn't provide ethtool stats
                    print(f"{iface} ({driver}): {stats}")
                    continue

                regex = self._driver_ok_regex[driver]
                print(f"Interesting stats for {iface} ({driver}):")
                for line in stats.split("\n")[1:]:
                    if line.endswith(': 0'):
                        continue
                    if re.search(regex, line):
                        continue

                    print(line)

