import argparse
from subprocess import call, Popen, PIPE
from collections import namedtuple
import os
import socket

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--local')
parser.add_argument('-p', '--peer', action='append', dest='peers')
args = parser.parse_args()


def _root_name_from_fqdn(dns_entry):
    return dns_entry.split('.', 1)[0]


HostData = namedtuple('HostData', ['hostname', 'etcd_name', 'host_ip'])


def hostdata_from_dns(hostname):
    return HostData(hostname, _root_name_from_fqdn(hostname),
                    socket.gethostbyname(hostname))


HOST = hostdata_from_dns(args.local)
PEERS = list(map(hostdata_from_dns, args.peers))
ALL = PEERS + [HOST]
print('HOST IS {}'.format(HOST.hostname))
print('PEERS ARE {}'.format(', '.join(x.hostname for x in PEERS)))

GROUPNAME = 'etcd'
USERNAME = 'etcd'
PROXY_URL = 'proxy1.dfw1.corp.rackspace.com:3128'
ETCD_VERSION = 'v3.1.7'


# create the dirs necessary
for dir_ in ('/var/lib/etcd', '/etc/etcd'):
    call(['mkdir', dir_])

# build an etcd user and group, assign the dir to the user
call(['groupadd', '-r', '{}'.format(GROUPNAME)])
call(['useradd',
      '-r',
      '-g', '{}'.format(GROUPNAME),
      '-d', '/var/lib/etcd',
      '-s', '/sbin/nologin',
      '-c', '"{} user"'.format(USERNAME), USERNAME])
call(['chown',
      '-R', '{}:{}'.format(GROUPNAME, USERNAME),
      '/var/lib/etcd'])

# write out the necessary configs for the systemd service
service_configs = {
        'Unit': {
            'Description': 'etcd service',
            'After': 'network.target'
            },
        'Service': {
            'Type': 'notify',
            'WorkingDirectory': '/var/lib/etcd',
            'EnvironmentFile': '/etc/etcd/etcd.conf',
            'User': USERNAME,
            'ExecStart': '/usr/bin/etcd',
            'LimitNOFILE': '65536'
            },
        'Install': {
            'WantedBy': 'multi-user.target'
            }
        }

with open('/usr/lib/systemd/system/etcd.service', 'w') as f:
    for section in service_configs.keys():
        f.write('[{}]\n'.format(section))
        for k, v in service_configs[section].iteritems():
            f.write('{}={}\n'.format(k, v))
        f.write('\n')

# write out the config file for etcd itself
host_client_url = 'https://{}'.format(HOST.hostname)
etcd_conf = {
        'member': {
            'NAME': {'value': HOST.etcd_name},
            'DATA_DIR': {'value': '/var/lib/etcd/default.etcd'},
            'SNAPSHOT_COUNTER': {'value': '10000', 'disabled': True},
            'HEARTBEAT_INTERVAL': {'value': "100", 'disabled': True},
            'ELECTION_TIMEOUT': {'value': '1000', 'disabled': True},
            'LISTEN_PEER_URLS': {'value': 'http://0.0.0.0:2380'},
            'LISTEN_CLIENT_URLS': {'value': 'https://0.0.0.0:2379'},
            'ADVERTISE_CLIENT_URLS': {'value': 'https://0.0.0.0:2379',
                                      'disabled': False},
            'MAX_SNAPSHOTS': {'value': '5', 'disabled': True},
            'MAX_WALS': {'value': '5', 'disabled': True},
            'CORS': {'value': '', 'disabled': True}
            },
        'cluster': {
            'INITIAL_ADVERTISE_PEER_URLS': {
                'value': 'http://{}:2380'.format(HOST.host_ip),
                },
            'INITIAL_CLUSTER': {
                'value': ','.join(['{}=http://{}:2380'.format(x.etcd_name,
                                                              x.host_ip)
                                   for x in ALL]),
                },
            'INITIAL_CLUSTER_STATE': {
                'value': 'new',
                },
            'INITIAL_CLUSTER_TOKEN': {
                'value': 'etcd-cluster',
                },
            'ADVERTISE_CLIENT_URLS': {
                'value': 'https://0.0.0.0:2379,{}'.format(host_client_url),
                'disabled': True
                },
            'DISCOVERY': {'value': '', 'disabled': True},
            'DISCOVERY_SRV': {'value': '', 'disabled': True},
            'DISCOVERY_FALLBACK': {'value': 'proxy', 'disabled': True},
            'DISCOVERY_PROXY': {'value': '', 'disabled': True}
            },
        'proxy': {
            'PROXY': {'value': 'off', 'disabled': True}
            },
        'security': {
            'CA_FILE': {'value': '', 'disabled': True},
            'CERT_FILE': {'value': '', 'disabled': True},
            'KEY_FILE': {'value': '', 'disabled': True},
            'PEER_CA_FILE': {'value': '', 'disabled': True},
            'PEER_CERT_FILE': {'value': '', 'disabled': True},
            'PEER_KEY_FILE': {'value': '', 'disabled': True},
            'AUTO_TLS': {'value': 'true'}
            }
        }

with open('/etc/etcd/etcd.conf', 'w') as f:
    for section in etcd_conf.keys():
        f.write('#[{}]\n'.format(section))
        for key, value_dict in etcd_conf[section].iteritems():
            line = 'ETCD_{}="{}"\n'.format(key, value_dict['value'])
            if value_dict.get('disabled', False):
                line = '#' + line
            f.write(line)
        f.write('#\n')

# set proxies to reach github from within infrastructure
for protocol in ('http', 'https'):
    os.environ['{}_proxy'.format(protocol)] = '{}://{}'.format(protocol,
                                                               PROXY_URL)

# create and claim ownership of download dir
etcd_dir = '/opt/etcd-{}'.format(ETCD_VERSION)
call(['mkdir', etcd_dir])
call(['chown', 'root:{}'.format(USERNAME), etcd_dir])
call(['chmod', '750', etcd_dir])

# download and unzip the etcd program
etcd_file_name = 'etcd-{}-linux-amd64.tar.gz'.format(ETCD_VERSION)
url_template = 'https://github.com/coreos/etcd/releases/download/{}/{}'
etcd_dl_url = url_template.format(ETCD_VERSION, etcd_file_name)
dl = Popen(['curl', '-L', etcd_dl_url], stdout=PIPE)
unzip = call(['tar', 'xz', '--strip-components=1', '-C', etcd_dir],
             stdin=dl.stdout)
dl.wait()

# symlink downloaded etcd programs to the bin directories
call(['ln', '-sf', '{}/etcd'.format(etcd_dir), '/usr/bin/etcd'])
call(['ln', '-sf', '{}/etcdctl'.format(etcd_dir), '/usr/bin/etcdctl'])
call(['etcd', '--version'])

# unset the proxies, no longer needed
for protocol in ('http', 'https'):
    os.environ.pop('{}_proxy'.format(protocol))

# forward port 443 to default etcd port 2379, open 2380 for peer communication
call(['firewall-cmd', '--zone=public',
      '--add-forward-port=port=443:proto=tcp:toport=2379',
      '--permanent'])
call(['firewall-cmd', '--zone=public', '--add-port=2380/tcp', '--permanent'])
call(['firewall-cmd', '--reload'])
call(['firewall-cmd', '--list-all'])

# start the etcd service
call(['touch', '/etc/init.d/etcd'])
call(['systemctl', 'enable', 'etcd'])
call(['systemctl', 'start', 'etcd'])
