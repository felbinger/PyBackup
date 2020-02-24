#!/usr/bin/python3

import hashlib
import json
import os
from argparse import ArgumentParser
from datetime import datetime
from shutil import copyfile
from tarfile import open as tar_open
from time import time

from colorama import init, Fore
from docker import from_env as docker_env
from docker.models.containers import Container
from prettytable import PrettyTable

from config import Config, create_from_json


def print_verbose(msg: str) -> None:
    if VERBOSE:
        print(f"[{str(datetime.utcnow().strftime('%H:%M:%S'))}] {msg}")


# convert bytes to next unit
def convert_size(num: float) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'):
        if abs(num) < 1000.0:
            # return "%3.2f %s" % (num, unit)
            return '{:3.2f} {}'.format(num, unit)
        num /= 1000.0
    # return "%.2f YiB" % (num)
    return '{:3.2f} YiB'.format(num)


# convert seconds to next unit
def convert_time(seconds: int) -> str:
    # humanfriendly.format_timespan(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ret = 'elapsed time: '

    if days:
        ret += f'{days} days, ' if days > 1 else '1 day, '
    if hours:
        ret += f'{hours} hours, ' if hours > 1 else '1 hour, '
    if minutes:
        ret += f'{minutes} minutes, ' if minutes > 1 else '1 minute, '
    if seconds:
        ret += f'{seconds} seconds' if seconds > 1 else '1 second'

    li = ret.rstrip(", ").rsplit(",", 1)
    return " and".join(li)


# size of a specific path including all subdirectories
def sizeof(start: str) -> str:
    if os.path.isfile(start):
        return convert_size(os.path.getsize(start))
    size = 0
    for path, folder, files in os.walk(start):
        for file in files:
            file = os.path.join(path, file)
            if not os.path.islink(file):
                size += os.path.getsize(file)
    return convert_size(size)


def docker_db_backup(container: Container, username: str, password: str, database: str, backup_dir: str) -> list:
    # path where the backup should be stored
    path: str = f'{backup_dir}/{database}.sql'
    # check if the backup of the database does already exist
    if os.path.exists(path):
        print_verbose(f'Backup of {database} database has been skipped!')
        return [
            database,
            " ",
            f'{Fore.YELLOW}Skipped{Fore.RESET}'
        ]

    print_verbose(f'Backup of {database} database has been started!')
    # execute the backup command
    res = container.exec_run(f'mysqldump --lock-tables -h localhost -u {username} -p{password} {database}')

    if res.exit_code != 0:
        print_verbose(f'{Fore.RED}Database {database} backup was not successful.{Fore.RESET}')
        print_verbose(f'- Status Code: {res.exit_code}')
        print_verbose(f'- Stdout: {res.output.decode("utf-8")}')

    with open(path, 'wb') as f:
        f.write(res.output)

    return [
        database,
        convert_size(os.path.getsize(path)),
        f'{Fore.GREEN}OK{Fore.RESET}' if res.exit_code == 0 else
        f'{Fore.RED}Failed ({res.exit_code}){Fore.RESET}'
    ]


def file_backup(path: str, backup_dir: str, checksums: list):
    # remove slash at the end of the path
    if path.endswith("/"):
        path = path[:-1]

    print_verbose(f'Backup of {path} has been started!')

    base = os.path.basename(path)
    filename = f'{backup_dir}/{base}.tar.gz'

    # check if the backup is already done
    if os.path.exists(filename):
        print_verbose(f'Backup of {path} has been skipped!')
        return [
            path,
            " ",
            " ",
            f'{Fore.YELLOW}Skipped{Fore.RESET}'
        ]

    if os.path.isfile(path):
        # file backup
        copyfile(path, filename)

        return [
            path,
            sizeof(path),
            "-",
            f'{Fore.GREEN}O{Fore.RESET}' if os.path.exists(filename) else f'{Fore.RED}Failed{Fore.RESET}'
        ]
    else:
        # directory backup
        with tar_open(filename, "w:gz") as target_fd:
            target_fd.add(path, arcname=base)

        # create checksum's
        if check_check_sums(checksums):
            for method in checksums:
                with open(f'{backup_dir}/{method}sum.txt', 'a') as f:
                    val = getattr(hashlib, method)(open(filename, 'rb').read()).hexdigest()
                    f.write(f'{val}\t{filename}\n')
        else:
            print("Config Error: Invalid checksum methods, skipping...")

        return [
            path,
            sizeof(path),
            convert_size(os.path.getsize(filename)),
            f'{Fore.GREEN}OK{Fore.RESET}' if os.path.exists(filename) else f'{Fore.RED}Failed{Fore.RESET}'
        ]


# check if the check sums from the config file are all valid method names from the hashlib module
def check_check_sums(lst: list):
    allow: tuple = ("md5", "sha1", "sha224", "sha384", "sha256", "sha512")
    ret: bool = not any(sum not in allow for sum in lst)
    if not ret:
        print_verbose(f"Invalid methods: {', '.join(set(lst).difference(set(allow)))}")
    return ret


def main(config: Config):
    # check if the backup directory exists
    if not config.backup_dir.endswith('/'):
        config.backup_dir += "/"

    config.backup_dir += str(datetime.utcnow().strftime("%Y-%m-%d"))  # %H-%M

    if not os.path.exists(config.backup_dir):
        print_verbose(f"Creating backup directory: ({config.backup_dir})")
        os.makedirs(config.backup_dir)

    for job in jobs:
        if job == 'database':
            try:
                container = list(
                    filter(lambda c: c.name == config.database_conatainer_name, docker_env().containers.list())
                )[0]
            except IndexError:
                print_verbose("Warning: Database Container not found!")
                continue
            data = list()

            for database in config.database_list:
                data.append(docker_db_backup(container, config.database_username, config.database_password, database,
                                             config.backup_dir))

            if data:
                # create table
                table = PrettyTable()
                table.title = "Database Backup Status"
                table.field_names = ["Database", "Size", "Status"]
                for row in data:
                    table.add_row(row)
                table.align['Database'] = 'l'
                table.align['Size'] = 'r'
                table.sortby = 'Database'
                print(table)
            else:
                print("Skipped database backup - nothing to do!")

        if job == 'files':
            data = list()

            for path in config.file_path_list:
                data.append(file_backup(path, config.backup_dir, config.checksums))

            if data:
                # create table
                table = PrettyTable()
                table.title = "File Backup Status"
                table.field_names = ["Path", "Original Size", "Compressed Size", "Status"]
                for row in data:
                    table.add_row(row)
                table.align['Path'] = 'l'
                table.align['Original Size'] = 'r'
                table.align['Compressed Size'] = 'r'
                print(table)
            else:
                print("Skipped file backup - nothing to do!")

        if job == 'gitlab':
            print("GitLab repository backup has been started!")
            try:
                container = list(
                    filter(lambda c: c.name == config.gitlab_container_name, docker_env().containers.list())
                )[0]
            except IndexError:
                print_verbose("Warning: Gitlab Container not found!")
                continue

            res = container.exec_run('gitlab-rake gitlab:backup:create')

            if res.exit_code == 0:
                print(f'{Fore.GREEN}GitLab repository backup complete!{Fore.RESET}')
            else:
                print(f'{Fore.RED}GitLab repository backup failed.{Fore.RESET}')
                print_verbose(f'Status Code: {res.status_code}')
                print_verbose(f'Stdout: {res.output}')

    if int(time() - START) > 5:
        print(convert_time(int(time() - START)))


if __name__ == '__main__':
    # initialize colorama
    init()

    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', help='verbose output', action="store_true")
    parser.add_argument('-c', '--config', help='config file', nargs=1)
    parser.add_argument('-a', '--all', help='backup everything', action="store_true")
    parser.add_argument('-d', '--database', help='backup databases', action="store_true")
    parser.add_argument('--gitlab', help='backup gitlab', action="store_true")
    parser.add_argument('-f', '--files', help='backup files', action="store_true")

    # get arguments
    args = vars(parser.parse_args())
    VERBOSE = args.get('verbose') or False

    jobs = list()
    if args.get('all'):
        jobs.append('database')
        jobs.append('gitlab')
        jobs.append('files')
    else:
        if args.get('database'):
            jobs.append('database')
        if args.get('gitlab'):
            jobs.append('gitlab')
        if args.get('files'):
            jobs.append('files')

    # check if jobs have been selected
    if not jobs:
        parser.print_help()
        exit(0)

    CONFIG_FILE = args.get('config')[0] if args.get('config') else '.config.json'

    if not os.path.isfile(CONFIG_FILE):
        print(f"{CONFIG_FILE} is not a file!")
        exit(1)

    if not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} not found!")
        exit(1)

    if os.geteuid() != 0:
        # print_verbose("elevating privileges...")
        # status = subprocess.check_call("sudo -v -p '[sudo] password for %u: '", shell=True)
        # if status != 0:
        # print("You need to have root privileges to run this script!")
        # exit(1)
        print("You need to have elevated privileges to run this script!")
        exit(1)

    START = time()

    json_object: dict = {}
    try:
        json_object: dict = json.loads(open(CONFIG_FILE).read())
    except ValueError:
        print(f'{CONFIG_FILE} does not contain valid json.')
        exit(1)

    config_object = create_from_json(json_object)
    config_object.verify_settings()
    main(config_object)
