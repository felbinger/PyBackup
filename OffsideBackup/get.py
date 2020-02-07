#!/usr/bin/python3.6

# This script is intended to run on a storage server at least once a week as a cronjob.
# It will download the current backup using secure file transfer protocol.

import hashlib
import json
import os
from argparse import ArgumentParser
from datetime import date, datetime

from paramiko import SSHClient, AutoAddPolicy

from .config import Config, create_from_json


def print_verbose(msg: str) -> None:
    if VERBOSE:
        print(f"[{str(datetime.utcnow().strftime('%H:%M:%S'))}] {msg}")


def main(config: Config) -> None:
    print_verbose(f'Downloading backup from {config.ssh_username}@{config.ssh_hostname}:{config.ssh_port} '
                  f'with {config.ssh_keyfile}')

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(config.ssh_hostname, port=config.ssh_port, username=config.ssh_username,
                key_filename=config.ssh_keyfile)

    # list existing backups (from stdout)
    existing_backups = ssh.exec_command("ls -d /home/backups")[1].readlines()

    # remove \n from list entries
    existing_backups = list(map(lambda s: s.strip(), existing_backups))

    # sort existing backups and get the directory name of the latest
    backup_date = sorted(existing_backups, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))[-1]

    sftp = ssh.open_sftp()

    # local directory where the backup should be stored
    local_path: str = config.local_location
    if not local_path.endswith('/'):
        local_path += "/"
    local_path += backup_date

    # create local directory for the backup
    if not os.path.exists(local_path):
        os.mkdir(local_path)
    else:
        # if local path exists, but is not a directory, exit
        if not os.path.isdir(local_path):
            print_verbose(f'{local_path} is not a directory! Exitig')
            exit(1)

    # backup location on the server (remote path)
    server_path: str = config.server_location
    if not server_path.endswith('/'):
        server_path += "/"
    server_path += backup_date

    for filename in list(filter(None, ssh.exec_command(f"ls {server_path}")[1].read().decode().split("\n"))):
        print_verbose(f'- {server_path}/{filename} (remote) => {local_path}/{filename} (local)')
        sftp.get(f'{server_path}/{filename}', f'{local_path}/{filename}')

    # check check sums
    methods: list = ["sha512", "sha384", "sha256", "sha224", "sha1", 'md5']
    best_available_method = next((m for m in methods if os.path.isfile(f'{local_path}/{m}sum.txt')), None)

    if best_available_method:
        with open(f'{local_path}/{best_available_method}sum.txt', 'r') as check_sum_file:
            for entry in check_sum_file.readlines():
                checksum, filepath = entry.split("\t")
                if not os.path.isfile(filepath):
                    print_verbose(f"There is a check sum for {os.path.basename(filepath)}, but the file does not exist")
                if checksum != getattr(hashlib, best_available_method)(open(filepath, 'rb').read()).hexdigest():
                    print(f"Checksum of {os.path.basename(filepath)} is not correct!")
    else:
        print_verbose("Unable to find check sums, skipping integrity check!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', help='verbose output', action="store_true")
    parser.add_argument('-c', '--config', help='config file', nargs=1)

    # get arguments
    args = vars(parser.parse_args())
    VERBOSE = args.get('verbose') or False

    CONFIG_FILE: str = args.get('config')[0] if args.get('config') else './config.json'

    if not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} not found!")
        exit(1)

    if not os.path.isfile(CONFIG_FILE):
        print(f"{CONFIG_FILE} is not a file!")
        exit(1)

    json_object: dict = {}
    try:
        json_object: dict = json.loads(open(CONFIG_FILE).read())
    except ValueError:
        print(f'{CONFIG_FILE} does not contain valid json.')
        exit(1)

    config_object = create_from_json(json_object)
    config_object.verify_settings()
    main(config_object)
