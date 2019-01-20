#!/usr/bin/python3

# Python Backup Script by NicoF2000 - v0.1

from colorama import init, Fore
from argparse import ArgumentParser
from time import time
from datetime import datetime
from shutil import copyfile
from prettytable import PrettyTable
from docker import from_env as docker_env
from tarfile import open as tar_open
import os
import json
import hashlib

CONFIG_FILE = ''


def print_verbose(msg):
    if VERBOSE:
        print(f"[{str(datetime.now().strftime('%H:%M:%S'))}] {msg}")


# convert bytes to next unit
def convert_size(num):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'):
        if abs(num) < 1000.0:
            # return "%3.2f %s" % (num, unit)
            return '{:3.2f} {}'.format(num, unit)
        num /= 1000.0
    # return "%.2f YiB" % (num)
    return '{:3.2f} YiB'.format(num)


# convert seconds to next unit
def convert_time(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ret = 'elapsed time: '

    if days:
        ret += f'{days} days' if days > 1 else '1 day'
        if hours:
            ret += f', {hours} hours' if hours > 1 else ', 1 hour'
            if minutes:
                ret += f', {minutes} minutes' if minutes > 1 else ', 1 minute'
                if seconds:
                    ret += f' and {seconds} seconds' if seconds > 1 else ' and 1 second'
    elif hours:
        ret += f'{hours} hours' if hours > 1 else '1 hour'
        if minutes:
            ret += f', {minutes} minutes' if minutes > 1 else ', 1 minute'
            if seconds:
                ret += f' and {seconds} seconds' if seconds > 1 else ' and 1 second'
    elif minutes:
        ret += f'{minutes} minutes' if minutes > 1 else '1 minute'
        if seconds:
            ret += f' and {seconds} seconds' if seconds > 1 else ' and 1 second'
    else:
        ret += f'{seconds} seconds' if seconds > 1 else '1 second'

    return ret


# size of a specific path including all subdirectories
def sizeof(start):
    if os.path.isfile(start):
        return convert_size(os.path.getsize(start))
    size = 0
    for path, folder, files in os.walk(start):
        for file in files:
            file = os.path.join(path, file)
            if not os.path.islink(file):
                size += os.path.getsize(file)
    return convert_size(size)


def docker_db_backup(container, username, password, database):
    # path where the backup should be stored
    path = f'{BACKUP_DIR}/{database}.sql'
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

    with open(path, 'w') as f:
        f.write(res.output.decode("utf-8"))

    return [
        database,
        convert_size(os.path.getsize(path)),
        f'{Fore.GREEN}OK{Fore.RESET}' if res.exit_code == 0 else
        f'{Fore.RED}Failed ({res.exit_code}){Fore.RESET}'
    ]


def file_backup(path):
    # remove slash at the end of the path
    if path.endswith("/"):
        path = path[:-1]

    print_verbose(f'Backup of {path} has been started!')

    base = os.path.basename(path)
    filename = f'{BACKUP_DIR}/{base}.tar.gz'

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
        for method in check_sums:
            with open(f'{BACKUP_DIR}/{method}sum.txt', 'a') as f:
                val = getattr(hashlib, method)(open(f'{filename}', 'rb').read()).hexdigest()
                f.write(f'{val}\t{filename}\n')

        return [
            path,
            sizeof(path),
            convert_size(os.path.getsize(filename)),
            f'{Fore.GREEN}OK{Fore.RESET}' if os.path.exists(filename) else f'{Fore.RED}Failed{Fore.RESET}'
        ]


def main(config):
    global BACKUP_DIR
    BACKUP_DIR = config.get('backup_dir') or '/var/backups/system/'

    # check if the backup directory exists
    if not BACKUP_DIR.endswith('/'):
        BACKUP_DIR += "/"

    BACKUP_DIR += str(datetime.now().strftime("%Y-%m-%d"))  # %H-%M

    if not os.path.exists(BACKUP_DIR):
        print_verbose(f"Creating backup directory: ({BACKUP_DIR})")
        os.makedirs(BACKUP_DIR)

    if DB_BACKUP:
        db_container_name = config.get('database').get('container_name') or 'root_db_1'
        db_username = config.get('database').get('username') or 'backup'
        db_password = config.get('database').get('password') or 'default_password'
        databases = config.get('database').get('list') or ['mysql']

        container = list(filter(lambda c: c.name == db_container_name, docker_env().containers.list()))[0]
        data = list()

        for database in databases:
            data.append(docker_db_backup(container, db_username, db_password, database))

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

    if GITLAB_BACKUP:
        print("GitLab repository backup has been started!")
        git_container = config.get('gitlab').get('container_name') or 'root_gitlab_1'
        container = list(filter(lambda c: c.name == git_container, docker_env().containers.list()))[0]

        res = container.exec_run('gitlab-rake gitlab:backup:create')

        if res.exit_code == 0:
            print(f'{Fore.GREEN}GitLab repository backup complete!{Fore.RESET}')
        else:
            print(f'{Fore.RED}GitLab repository backup failed.{Fore.RESET}')
            print_verbose(f'Status Code: {res.status_code}')
            print_verbose(f'Stdout: {res.output}')

    if FILE_BACKUP:
        paths = config.get('files').get('paths') or list()

        global check_sums
        check_sums = config.get('files').get('checksums') or list()

        data = list()

        for path in paths:
            data.append(file_backup(path))

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
    FILE_BACKUP = args.get('files')
    DB_BACKUP = args.get('database')
    GITLAB_BACKUP = args.get('gitlab')
    if args.get('all'):
        FILE_BACKUP = True
        GITLAB_BACKUP = True
        DB_BACKUP = True

    if not FILE_BACKUP and not GITLAB_BACKUP and not DB_BACKUP:
        parser.print_help()
        exit(0)

    CONFIG_FILE = args.get('config') or '.config.json'
    if not os.path.exists(CONFIG_FILE):
        print_verbose(f"{CONFIG_FILE} not found!")
        exit(1)

    if os.geteuid() != 0:
        print("You need to have root privileges to run this script!")
        exit(1)

    START = time()

    # parse config file and execute backups
    main(json.loads(open(CONFIG_FILE).read()))
