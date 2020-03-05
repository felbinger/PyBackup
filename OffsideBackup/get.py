#!/usr/bin/python3.6

# This script is intended to run on a storage server at least once a week as a cronjob.
# It will download the current backup using secure file transfer protocol.

from argparse import ArgumentParser
from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.ssh_exception import BadAuthenticationType, AuthenticationException
import os
import json
import hashlib

from config import Config, create_from_json


def print_verbose(msg: str) -> None:
    if VERBOSE:
        print(f"[{str(datetime.now().strftime('%H:%M:%S'))}] {msg}")


def check_date(date) -> bool:
    ret = True
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        ret = False
    return ret


def main(config: Config) -> None:
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    if config.ssh_key_file:
        print_verbose(f'Checking for backups on {config.ssh_username}@{config.ssh_hostname}:{config.ssh_port}' +
                      f' with {config.ssh_key_file}')
        pkey = RSAKey.from_private_key_file(config.ssh_key_file, password=config.ssh_passphrase)
        ssh.connect(config.ssh_hostname, port=config.ssh_port,
                    username=config.ssh_username, pkey=pkey)
    else:
        print_verbose(f'Checking for backups on {config.ssh_username}@{config.ssh_hostname}:{config.ssh_port}')
        try:
            ssh.connect(config.ssh_hostname, port=config.ssh_port,
                        username=config.ssh_username, password=config.ssh_password, allow_agent=False)
        except BadAuthenticationType:
            print("Error: Password authentication is disabled! Exiting...")
            exit(1)
        except AuthenticationException as e:
            print("Error: Authentication failed! Exiting...")
            exit(1)

    # backup location on the server (remote path)
    server_path: str = config.server_location
    if not server_path.endswith('/'):
        server_path += "/"

    # list existing backups (from stdout)
    existing_backups = ssh.exec_command(f"ls -1 -d {server_path}*/ | xargs -n 1 basename")[1].readlines()

    # remove \n from list entries
    existing_backups = list(map(lambda s: s.strip(), existing_backups))

    # remove non pybackup specific directories
    existing_backups = list(filter(check_date, existing_backups))

    if not existing_backups:
        print(f'Error: Unable to find backups on {config.ssh_hostname}:{config.server_location}')
        exit(1)

    # sort existing backups and get the directory name of the latest
    backup_date = sorted(existing_backups, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))[-1]

    print_verbose(f'Downloading backup from {config.ssh_username}@{config.ssh_hostname}:{config.ssh_port}' +
                  f' from {config.server_location}')

    sftp = ssh.open_sftp()

    # local directory where the backup should be stored
    local_path: str = config.local_location
    if not os.path.isdir(local_path):
        os.mkdir(local_path)

    if not local_path.endswith('/'):
        local_path += "/"

    local_path += backup_date

    # create local directory for the backup
    if not os.path.isdir(local_path):
        os.mkdir(local_path)

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

    config_file: str = args.get('config')[0] if args.get('config') else './.config.json'

    if not os.path.isfile(config_file):
        print(f"{config_file} is not a file!")
        exit(1)

    if not os.path.exists(config_file):
        print(f"{config_file} not found!")
        exit(1)

    json_object: dict = {}
    try:
        json_object: dict = json.loads(open(config_file).read())
    except ValueError:
        print(f'{config_file} does not contain valid json.')
        exit(1)

    config_obj = create_from_json(json_object)
    config_obj.validate()
    main(config_obj)
