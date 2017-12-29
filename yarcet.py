import argparse
import json
import sys
import os
import socket
import paramiko
import time
import os.path
from termcolor import cprint
from binascii import hexlify


class HKWarningPolicy(paramiko.WarningPolicy):
    def missing_host_key(self, client, hostname, key):
        print('Warning :: unknown %s host key for %s: %s' % (key.get_name(),
              hostname, hexlify(key.get_fingerprint())))


def manage_interactive_session(chan, log=None):
    import select
    import termios
    import tty

    oldtty = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    tty.setcbreak(sys.stdin.fileno())
    try:
        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = chan.recv(1024)
                    if len(x) == 0:
                        break
                    cprint(x.decode(), 'white', 'on_grey', end='')
                    sys.stdout.flush()
                    if log:
                        cout = x.decode().replace('\r', '')
                        log.write(cout)
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


def run_cmd(node, config, log):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(HKWarningPolicy)
    try:
        client.connect(node, username=config['ssh']['user'],
                       allow_agent=config['ssh']['agent'])
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        print("Unable to ssh in to node %s" % node)
        print(e)
        sys.exit(1)

    chan = client.get_transport().open_session()
    chan.set_combine_stderr(True)

    recipe = os.path.abspath(config['recipe'])
    basename = os.path.basename(recipe)
    remote_file = '/tmp/%d_%s' % (int(time.time()), basename)

    try:
        sftp = client.open_sftp()
        sftp.put(recipe, remote_file)
        sftp.close()
    except Exception as e:
        print(e)
        sys.exit(1)

    cmd = ''
    if config['ssh']['sudo']:
        chan.get_pty()
        cmd += 'sudo '
    cmd += 'sh %s; unlink %s' % (remote_file, remote_file)

    try:
        chan.exec_command(cmd)
        if config['connection_mode'] == 'sequential':
            manage_interactive_session(chan, log)
        retcode = chan.recv_exit_status()
    except paramiko.ssh_exception.SSHException as e:
        print('Error executing recipe in node %s' % node)
        print(e)
        sys.exit(1)

    client.close()

    return retcode


def run_sequential(config):
    log = None
    nodes = config['node_groups'][config['node_group']]
    if config['output_mode'] == 'tee':
        logname = config['node_group'] + '.log'
        logfile = os.path.join(config['log_path'], logname)
        log = open(logfile, 'w')

    for node in nodes:
        if log:
            log.write('Time: %s\n' % time.strftime('%Y-%M-%d %H:%M:%S'))
            log.write('Node: %s\n' % node)
        cprint('Node: %s' % node, 'green', 'on_grey', attrs=['bold'])
        retcode = run_cmd(node, config, log)
        exit_color = 'red' if retcode != 0 else 'green'
        cprint('(exit code: %d)\n' % retcode, exit_color, 'on_white')
        if log:
            log.write('exit code: %d\n\n' % retcode)


def run_parallel(config):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description='Execute recipes into remote nodes'
    )
    parser.add_argument('-c', '--config', dest='config',
                        default='config.json',
                        help='Configuration file (default: config.json)')
    parser.add_argument('node_group', metavar='node-group',
                        help='Node group name where payload will be executed')
    parser.add_argument('recipe',
                        help='Recipe to send and execute in remote node')
    parser.add_argument('-m', '--mode', dest='mode', required=False,
                        choices=['p', 's'],
                        help='Connection mode (p=parallel, s=sequential)')

    return parser.parse_args()


def parse_config(config_file):
    try:
        with open(config_file) as f:
            config = json.loads(f.read())
    except (IOError, json.decoder.JSONDecodeError) as e:
        print("[%s]: %s" % (e.__class__.__name__, e))
        sys.exit(1)

    return config


def run(config):
    if config['connection_mode'] == 'sequential':
        run_sequential(config)
    elif config['connection_mode'] == 'parallel':
        run_parallel(config)
    else:
        print("Connection mode %s not valid" % (config['connection_mode']))
        sys.exit(1)


def main():
    args = parse_args()
    config = parse_config(args.config)
    if args.node_group not in config['node_groups']:
        print("%s node group not defined in %s" % (
              args.node_group, args.config))
        sys.exit(1)
    else:
        config['node_group'] = args.node_group

    config['recipe'] = args.recipe

    logpath = os.path.abspath(config['log_path'])
    config['log_path'] = logpath
    if not os.path.isdir(logpath):
        os.mkdir(logpath)

    run(config)


if __name__ == "__main__":
    main()
