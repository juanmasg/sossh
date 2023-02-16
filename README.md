### Sos(report) Sh(ell)

### Project status

The software is functional, but it's still in its early stages and work
right now is mainly focused on functionality rather than stability or bugfixes.
Things might change internally without prior notice, and bugs are expected.
The plan for now is to keep writing new commands that perform data pre-processing
and display insights about the system, replacing the need to print the raw
file contents. Think about a python based [xsos](https://github.com/ryran/xsos)
on steroids.
I'll fix bugs, add core functionality or change the internal design as it's
needed depending on what the command implementations need.


### Usage

```
% ./sossh.py -h
usage: sossh.py [-h] [-N] [-c COMMAND] <path/to/sosreport/file/or/directory>

positional arguments:
  </path/to/sosreport/file/or/directory>

optional arguments:
  -h, --help            show this help message and exit
  -N, --no-banner
  -c COMMAND, --command COMMAND

```

### Features

* Transparently open sosreports from tar files in memory, without extracting
  the contents

* Access the `sos_commands` output as if they were run locally. In other
  words, I prefer to check the network interfaces by writing this:
  ```
  sossh) ip -d address
  ```

  than this:
  ```
  $ cat sos_commands/networking/ip_-d_address
  ```

* Readline integration with command line history and tab completion for the
  commands under `sos_commands/`

* Pipe any command's output through the shell

* Write custom additional commands that pre-process any data available in
  the sosreport.


### Available custom commands (more to come):
* `links`: Print a tree like structure of the network interfaces and their
  dependencies
* `cat`: Display the contents of any file.
* `tainted`: Display extended tainted information
* `packages`: Display third party package information
* `inet`: Display ipv4 info
* `dmi`: Display a summary from dmidecode
* `firewalld_explain`: Run [firewalld_explain](https://github.com/juanmasg/firewalld-explain.git) if it exists in the path
* `help`: Display available commands 
* `_sysctl`: Display some potentially problematic sysctls
* `_services`: Display all (known) security related services
* `_ethtool`: Display curated ethtool statistics.
* `osinfo`: Display basic OS information
* `cmdgroup`: Run multiple commands at once. Available groups: banner, net

### Example

```
% sossh  000-sosreport-testhost-01234567-2023-02-14-abcdefg.tar.xz
Reading tarfile for the first time. This might take a while...
Sosreport found: sosreport: 4.2

  Path            : 000-sosreport-testhost-01234567-2023-02-14-abcdefg.tar.xz
  Generated       : Local time: Tue 2023-02-14 10:38:30 CET
  Hostname        : testhost
  Uname           : Linux testhost 4.18.0-372.16.1.el8_6.x86_64 #1 SMP Tue Jun 28 03:02:21 EDT 2022 x86_64 x86_64 x86_64 GNU/Linux
  Uptime          : 10:37:47 up 5 days, 19:08,  3 users,  load average: 7.21, 5.35, 5.18
  Cmdline         : BOOT_IMAGE=(hd0,gpt2)/vmlinuz-4.18.0-372.16.1.el8_6.x86_64 root=/dev/mapper/rhel-root ro crashkernel=auto resume=/dev/mapper/rhel-swap rd.lvm.lv=rhel/root rd.lvm.lv=rhel/swap rhgb quiet
  Release         : Red Hat Enterprise Linux release 8.6 (Ootpa)
  Tainted         : YES: {'tmhook': 'Unsigned', 'dsa_filter_hook': 'Unsigned', 'dsa_filter': 'Unsigned', 'bmhook': 'Unsigned'}

testhost🆘 nmcli con
NAME      UUID                                  TYPE      DEVICE  
vlan_123  10e4d230-9815-4999-aa87-37bfd2da5b82  vlan      vlan123 
vlan_456  10e4d230-9815-4999-aa87-37bfd2da5b83  vlan      vlan456
eno1      10e4d230-9815-4999-aa87-37bfd2da5b84  ethernet  eno1    
eno2      10e4d230-9815-4999-aa87-37bfd2da5b85  ethernet  eno2    
ens2f0    10e4d230-9815-4999-aa87-37bfd2da5b86  ethernet  ens2f0  
ens2f1    10e4d230-9815-4999-aa87-37bfd2da5b87  ethernet  ens2f1  
TEAM0     10e4d230-9815-4999-aa87-37bfd2da5b88  team      team0   
ens1f0    10e4d230-9815-4999-aa87-37bfd2da5b89  ethernet  --      
ens1f1    10e4d230-9815-4999-aa87-37bfd2da5b80  ethernet  --      
ens2f0    10e4d230-9815-4999-aa87-37bfd2da5b8a  ethernet  --      
ens2f1    10e4d230-9815-4999-aa87-37bfd2da5b8b  ethernet  --      

testhost🆘 links
 ├ lo           : LOOPBACK 65536 00:00:00:00:00:00  (UP,LOWER_UP)                 127.0.0.1/8
 ├ ens1f0       : DOWN      1500 00:aa:a4:7e:8a:28  (NO-CARRIER,UP)               
 ├ team0        : UP        1500 00:bb:a4:7d:8b:01  (UP,LOWER_UP)                 
  ├ eno1        : UP        1500 00:cc:a4:70:8c:02  (UP,LOWER_UP)                 
  ├ eno2        : UP        1500 00:dd:a4:71:8d:03  (UP,LOWER_UP)                 
  ├ ens2f0      : UP        1500 00:ee:a4:72:8e:04  (UP,LOWER_UP)                 
  └ ens2f1      : UP        1500 00:a1:a4:73:81:05  (UP,LOWER_UP)                 
 ├ ens1f1       : DOWN      1500 00:a2:a4:74:83:2a  (NO-CARRIER,UP)               
 ├ vlan123      : UP        1500 00:a3:a4:75:85:37  (UP,LOWER_UP)    802.1Q(123)  192.168.10.20/24
 └ vlan456      : UP        1500 00:a4:a4:76:87:24  (UP,LOWER_UP)    802.1Q(456)  10.100.100.1/24

testhost🆘 packages
Third party packages installed:
  * Trend Micro Inc.
    - ds_agent-10.0.0-2048.el8.x86_64


```
