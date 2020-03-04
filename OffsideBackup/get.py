#!/usr/bin/python3.6

# This script is intended to run on a storage server at least once a week as a cronjob.
# It will download the current backup using secure file transfer protocol.

from argparse import ArgumentParser
from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy
import os
import json
import hashlib

CONFIG_FILE = ''


def print_verbose(msg):
    if VERBOSE:
        print(f"[{str(datetime.now().strftime('%H:%M:%S'))}] {msg}")


def main(config):
    hostname = config.get("server").get("hostname")
    port = config.get("server").get("port") or 22
    username = config.get("server").get("username") or 'backup'
    key_file = config.get("server").get("keyfile")

    if not hostname or not key_file:
        print(f"Invalid configuration! Check: {CONFIG_FILE}")
        exit(1)

    print_verbose(f'Downloading backup from {username}@{hostname}:{port} with {key_file}')

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, key_filename=key_file)

    # list existing backups (from stdout)
    existing_backups = ssh.exec_command("ls /home/backups")[1].readlines()

    # remove \n from list entries
    existing_backups = list(map(lambda s: s.strip(), existing_backups))

    # sort existing backups and get the directory name of the latest
    backup_date = sorted(existing_backups, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))[-1]

    sftp = ssh.open_sftp()

    # local directory where the backup should be stored
    local_path = config.get('local_location') or '/var/backups/{hostname}/'
    if not local_path.endswith('/'):
        local_path += "/"

    local_path += backup_date

    # create local directory for the backup
    if not os.path.exists(local_path):
        os.mkdir(local_path)

    # backup location on the server (remote path)
    server_path = config.get('server_location') or '/var/backups/'
    if not server_path.endswith('/'):
        server_path += "/"

    server_path += backup_date

    for filename in list(filter(None, ssh.exec_command(f"ls {server_path}")[1].read().decode().split("\n"))):
        print_verbose(f'- {server_path}/{filename} (remote) => {local_path}/{filename} (local)')
        sftp.get(f'{server_path}/{filename}', f'{local_path}/{filename}')

    # check check sums
    methods = ["sha512", "sha384", "sha256", "sha224", "sha1", 'md5']
    best_available_method = next((m for m in methods if os.path.isfile(f'{local_path}/{m}sum.txt')), None)

    if best_available_method:
        with open(f'{local_path}/{best_available_method}sum.txt', 'r') as check_sum_file:
            for entry in check_sum_file.readlines():
                checksum, filepath = entry.split("\t")
                filepath = os.path.basename(filepath.strip("\n"))
                local_filepath = f'{local_path}/{filepath}'
                if not os.path.isfile(local_filepath):
                    print_verbose(f"There is a check sum for {filepath}, but the file does not exist")
                if checksum != getattr(hashlib, best_available_method)(open(local_filepath, 'rb').read()).hexdigest():
                    print(f"Checksum of {filepath} is not correct!")
    else:
        print_verbose("Unable to find check sums, skipping integrity check!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', help='verbose output', action="store_true")
    parser.add_argument('-c', '--config', help='config file', nargs=1)

    # get arguments
    args = vars(parser.parse_args())
    VERBOSE = args.get('verbose') or False

    CONFIG_FILE = args.get('config')[0] if args.get('config') else '.config.json'

    if not os.path.isfile(CONFIG_FILE):
        print(f"{CONFIG_FILE} is not a file!")
        exit(1)

    if not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} not found!")
        exit(1)

    try:
        global conf
        conf = json.loads(open(CONFIG_FILE).read())
    except ValueError:
        print(f'{CONFIG_FILE} does not contain valid json.')
        exit(1)

    main(conf)
