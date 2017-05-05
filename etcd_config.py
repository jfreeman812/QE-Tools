import argparse
from subprocess import call, Popen, PIPE
import os
import socket

GROUPNAME = 'etcd'
USERNAME = 'etcd'
PROXY_URL = 'proxy1.dfw1.corp.rackspace.com:3128'
ETCD_VERSION = 'v3.1.7'


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--local', default=socket.getfqdn(),
                        help='FQDN for this machine')
    parser.add_argument('--proxy-url', default=PROXY_URL,
                        help='Proxy url to use for downloads')
    parser.add_argument('--etcd-version', default=ETCD_VERSION,
                        help='Version of etcd to install')
    parser.add_argument('peers', nargs='+',
                        help='FQDN for peer machine')
    return parser


def _root_name_from_fqdn(dns_entry):
    return dns_entry.split('.', 1)[0]


def _service_config(user_name):
    return {
        'Unit': {
            'Description': 'etcd service',
            'After': 'network.target'
        },
        'Service': {
            'Type': 'notify',
            'WorkingDirectory': '/var/lib/etcd',
            'EnvironmentFile': '/etc/etcd/etcd.conf',
            'User': user_name,
            'ExecStart': '/usr/bin/etcd',
            'LimitNOFILE': '65536'
        },
        'Install': {
            'WantedBy': 'multi-user.target'
        }
    }


def _etcd_config(host, all_nodes):
    return {
        'member': {
            'NAME': {'value': _root_name_from_fqdn(host)},
            'DATA_DIR': {'value': '/var/lib/etcd/default.etcd'},
            'SNAPSHOT_COUNTER': {'value': '10000', 'disabled': True},
            'HEARTBEAT_INTERVAL': {'value': "100", 'disabled': True},
            'ELECTION_TIMEOUT': {'value': '1000', 'disabled': True},
            'LISTEN_PEER_URLS': {'value': 'http://0.0.0.0:2380'},
            'LISTEN_CLIENT_URLS': {'value': 'https://0.0.0.0:2379'},
            'ADVERTISE_CLIENT_URLS': {'value': 'https://0.0.0.0:2379'},
            'MAX_SNAPSHOTS': {'value': '5', 'disabled': True},
            'MAX_WALS': {'value': '5', 'disabled': True},
            'CORS': {'value': '', 'disabled': True}
        },
        'cluster': {
            'INITIAL_ADVERTISE_PEER_URLS': {
                'value': 'http://{}:2380'.format(host),
            },
            'INITIAL_CLUSTER': {
                'value': ','.join(['{}=http://{}:2380'.format(_root_name_from_fqdn(x), x)
                                   for x in all_nodes]),
            },
            'INITIAL_CLUSTER_STATE': {
                'value': 'new',
            },
            'INITIAL_CLUSTER_TOKEN': {
                'value': 'etcd-cluster',
            },
            'ADVERTISE_CLIENT_URLS': {
                'value': 'https://0.0.0.0:2379,{}'.format('https://{}'.format(host)),
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


def make_dirs():
    for dir_ in ('/var/lib/etcd', '/etc/etcd'):
        call(['mkdir', dir_])


def setup_user(group_name, user_name):
    call(['groupadd', '-r', '{}'.format(group_name)])
    call(['useradd',
          '-r',
          '-g', '{}'.format(group_name),
          '-d', '/var/lib/etcd',
          '-s', '/sbin/nologin',
          '-c', '"{} user"'.format(user_name), user_name])
    call(['chown',
          '-R', '{}:{}'.format(group_name, user_name),
          '/var/lib/etcd'])


def write_etcd_service_config(user_name):
    service_config = _service_config(user_name)
    with open('/usr/lib/systemd/system/etcd.service', 'w') as f:
        for section in service_config.keys():
            f.write('[{}]\n'.format(section))
            for k, v in service_config[section].iteritems():
                f.write('{}={}\n'.format(k, v))
            f.write('\n')


def write_etcd_app_config(host, peers):
    all_nodes = peers + [host]
    etcd_config = _etcd_config(host, all_nodes)
    with open('/etc/etcd/etcd.conf', 'w') as f:
        for section in etcd_config.keys():
            f.write('#[{}]\n'.format(section))
            for key, value_dict in etcd_config[section].iteritems():
                line = 'ETCD_{}="{}"\n'.format(key, value_dict['value'])
                if value_dict.get('disabled', False):
                    line = '#' + line
                f.write(line)
            f.write('#\n')


def download_and_install(user_name, proxy_url, etcd_version):
    # set proxies to reach github from within infrastructure
    for protocol in ('http', 'https'):
        os.environ['{}_proxy'.format(protocol)] = '{}://{}'.format(protocol,
                                                                   proxy_url)

    # create and claim ownership of download dir
    etcd_dir = '/opt/etcd-{}'.format(etcd_version)
    call(['mkdir', etcd_dir])
    call(['chown', 'root:{}'.format(user_name), etcd_dir])
    call(['chmod', '750', etcd_dir])

    # download and unzip the etcd program
    etcd_file_name = 'etcd-{}-linux-amd64.tar.gz'.format(etcd_version)
    url_template = 'https://github.com/coreos/etcd/releases/download/{}/{}'
    etcd_dl_url = url_template.format(etcd_version, etcd_file_name)
    dl = Popen(['curl', '-L', etcd_dl_url], stdout=PIPE)
    call(['tar', 'xz', '--strip-components=1', '-C', etcd_dir], stdin=dl.stdout)
    dl.wait()

    # symlink downloaded etcd programs to the bin directories
    call(['ln', '-sf', '{}/etcd'.format(etcd_dir), '/usr/bin/etcd'])
    call(['ln', '-sf', '{}/etcdctl'.format(etcd_dir), '/usr/bin/etcdctl'])
    call(['etcd', '--version'])

    # unset the proxies, no longer needed
    for protocol in ('http', 'https'):
        os.environ.pop('{}_proxy'.format(protocol))


def forward_ports():
    call(['firewall-cmd', '--zone=public',
          '--add-forward-port=port=443:proto=tcp:toport=2379',
          '--permanent'])
    call(['firewall-cmd', '--zone=public',
          '--add-port=2380/tcp', '--permanent'])
    call(['firewall-cmd', '--reload'])
    call(['firewall-cmd', '--list-all'])


def etcd_start():
    call(['systemctl', 'start', 'etcd'])


def etcd_initial_start():
    call(['touch', '/etc/init.d/etcd'])
    call(['systemctl', 'enable', 'etcd'])
    etcd_start()


def setup():
    args = get_parser().parse_args()
    make_dirs()
    setup_user(GROUPNAME, USERNAME)
    write_etcd_service_config(USERNAME)
    write_etcd_app_config(args.local, args.peers)
    download_and_install(USERNAME, args.proxy_url, args.etcd_version)
    forward_ports()
    etcd_initial_start()


if __name__ == '__main__':
    setup()
