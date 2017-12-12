import os
from collections import OrderedDict
from virl.api import VIRLServer
from virl import helpers
import yaml
from jinja2 import Environment, FileSystemLoader, PackageLoader
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def render_topl_template(devices):
    """
    renders topology: section of testbed yaml
    """
    pass

def setup_yaml():
  """ https://stackoverflow.com/a/8661021 """
  represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
  yaml.add_representer(OrderedDict, represent_dict_order)

setup_yaml()

def render_topology_block(virl_xml, roster=None, interfaces=None):
    """
    we need to merge information from multiple sources to generate all
    the required parameters for the topology key in the testbed yaml config

    """
    if not all([virl_xml, roster, interfaces]):
        raise ValueError("we really need virl_xml, roster, and interfaces")

    # sim_name should be the only key in the dictionary
    if len(interfaces.keys()) != 1:
        raise ValueError("too many keys in interface response")

    sim_name = interfaces.keys()[0]

    try:
        devices = interfaces[sim_name]
    except KeyError:
        raise Exception('something went wrong')


    # for device, interface in devices.items():
    #     render_device_template(device, interface)

    # return render_device_template(devices)
    j2_env = Environment(loader=PackageLoader('virl', 'templates'),
                         trim_blocks=False)
    return j2_env.get_template('testbed-yaml.j2').render(devices=devices)



def pyats_testbed_generator(env,
                            virl_data,
                            roster,
                            interfaces,
                            dev_username='cisco',
                            dev_password='cisco',
                            conn_class='unicon.Unicon'):
    """
    given a sim roster produces a testbed file suitable for
    use with pyats

    """


    # testbed:
    #    name: example_testbed
    testbed = OrderedDict()
    testbed['testbed'] = OrderedDict()
    testbed['testbed']['name'] = env + '_testbed'

    #
    #     servers:
    #         tftp:
    #             server: "ott2lab-tftp1"
    #             address: "223.255.254.254"
    #             path: ""
    #             username: "username"
    #             password: "password"
    #
    testbed['testbed']['servers'] = dict()
    servers = testbed['testbed']['servers']
    testbed['devices'] = dict()
    for device, props in roster.items():
        virl_server = str(props.get("SimulationHost", None))
        device_type = str(props.get("NodeSubtype", None))
        device_name = str(props.get("NodeName", None))
        protocol = str(props.get("managementProtocol", None))
        console_port = str(props.get("PortConsole", None))
        username = os.getenv("VIRL_USERNAME", "guest")
        username = os.getenv("VIRL_PASSWORD", "guest")

        # prefer external addr
        external_ip = str(props.get("externalAddr", ""))
        mgmt_ip = str(props.get("managementIP", ""))
        if len(external_ip) > 6:
            address = external_ip

        elif len(mgmt_ip) > 6:
            address = mgmt_ip

        # # minimally required information to generate a meaningful device
        # REQUIRED_PROPS = [device_type,
        #                   device_name,
        #                   address,
        #                   console_port]
        #
        # valid =  None in REQUIRED_PROPS
        # print REQUIRED_PROPS,
        # print valid
        # if not valid:
        #     print('bailing')
        #     continue

        # management lxc
        if device_type == 'mgmt-lxc':
            servers['mgmt-lxc'] = dict()
            entry = dict()
            entry['server'] = device_name
            entry['address'] = address
            entry['path'] = ""
            servers['mgmt-lxc'] = entry
        # some devices can't conform
        elif device_type in ['LXC FLAT']:
            continue
        # all other devices
        else:
            #     ott-tb1-n7k3:

            if device_name == 'None':
                continue

            testbed['devices'][device_name] = dict()
            entry = testbed['devices'][device_name]


            entry['alias'] = device_name
            entry['type'] = device_type

    #         tacacs:
    #             login_prompt: "login:"
    #             password_prompt: "Password:"
    #             username: "admin"
    #         passwords:
    #             tacacs: password
    #             enable: password
    #             line: password

            entry['tacacs'] = {
                "username": dev_username
            }

            entry['passwords'] = {
                "tacacs": dev_password,
                "enable": dev_password,
                "line": dev_password
            }
    #         connections:
    #             a:
    #                 protocol: telnet
    #                 ip: "10.85.87.25"
    #                 port: 2003
    #             b:
    #                 protocol: telnet
    #                 ip: "10.85.87.25"
    #                 port: 2004
    #             alt:
    #                 protocol : telnet
    #                 ip : "5.25.25.3"
            entry['connections'] = OrderedDict()
            entry['connections']['defaults'] = {
                    "class": conn_class
                    }
            entry['connections']['console'] = OrderedDict()
            entry['connections']['console'] = {
                    "protocol": "telnet",
                    "ip": virl_server,
                    "port": console_port
                    }

    print(type(interfaces))
    testbed_yaml = yaml.dump(testbed, default_flow_style=False)
    topology_yaml = render_topology_block(virl_data, roster, interfaces)
    return testbed_yaml + '\n' + topology_yaml




    #             clean:
    #                 pre_clean: |
    #                    switchname %{self}
    #                    license grace-period
    #                    feature telnet
    #                    interface mgmt0
    #                            ip addr %{self.connections.alt.ip}/24
    #                    no shut
    #                    vrf context management
    #                      ip route 101.0.0.0/24 5.19.27.251
    #                      ip route 102.0.0.0/24 5.19.27.251
    #                 post_clean: |
    #                     switchname %{self}
    #                     license grace-period
    #                     feature telnet
    #                     interface mgmt0
    #                             ip addr %{self.connections.alt.ip}/24
    #                     no shut
    #                     vrf context management
    #                       ip route 101.0.0.0/24 5.19.27.251
    #                       ip route 102.0.0.0/24 5.19.27.251
    # topology:
    #
    #     links:
    #         link-1:
    #             alias: 'loopback-1'
    #
    #     ott-tb1-n7k3:
    #         interfaces:
    #             Ethernet3/1:
    #                 link: link-1
    #                 type: ethernet
    #
    #             Ethernet4/1:
    #                 link: link-1
    #                 type: ethernet
    #
    #             Ethernet4/2:
    #                 type: ethernet
    #
    #             Ethernet4/3:
    #                 type: ethernet