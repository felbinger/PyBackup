#!/usr/bin/python3

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
    # humanfriendly.format_timespan(seconds)
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


def docker_mysql_backup(container, username, password, database):
    # path where the backup should be stored
    path = f'{BACKUP_DIR}/{container.name}/{database}.sql'
    # check if the backup of the database does already exist
    if os.path.exists(path):
        print_verbose(f'Backup of (mysql) {database} database has been skipped!')
        return [
            "MySQL",
            container.name,
            database,
            " ",
            f'{Fore.YELLOW}Skipped{Fore.RESET}'
        ]

    print_verbose(f'Backup of (mysql) {database} database has been started!')
    # execute the backup command
    res = container.exec_run(f'mysqldump --lock-tables -h localhost -u {username} -p{password} {database}')

    if res.exit_code != 0:
        print_verbose(f'{Fore.RED}MySQL Database {database} backup was not successful.{Fore.RESET}')
        return [
            "MySQL",
            container.name,
            database,
            " ",
            f'{Fore.RED}Failed ({res.exit_code}){Fore.RESET}'
        ]
    else:
        with open(path, 'wb') as f:
            f.write(res.output)

        return [
            "MySQL",
            container.name,
            database,
            convert_size(os.path.getsize(path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ]


def docker_mongodb_backup(container, username, password, database):
    # path where the backup should be stored
    path = f'{BACKUP_DIR}/{container.name}/{database}.tar'
    # check if the backup of the database does already exist
    if os.path.exists(path):
        print_verbose(f'Backup of (mongodb) {database} database has been skipped!')
        return [
            "MongoDB",
            container.name,
            database,
            " ",
            f'{Fore.YELLOW}Skipped{Fore.RESET}'
        ]

    container_workdir = '/data/transfer/'
    if not container_workdir.endswith("/"):
        container_workdir += "/"

    print_verbose(f'Backup of (mongodb) {database} database has been started!')
    # execute the backup command

    cmd = f'mongodump -h localhost -d {database} --gzip -o {container_workdir}'
    if username and password:
        cmd += f' -u {username} -p{password}'
    res = container.exec_run(cmd)

    if res.exit_code != 0 or not len(res.output):
        print_verbose(f'{Fore.RED}MongoDB Database {database} backup was not successful.{Fore.RESET}')
        return [
            "MongoDB",
            container.name,
            database,
            " ",
            f'{Fore.RED}Failed ({res.exit_code}){Fore.RESET}'
        ]
    else:
        with open(f'{BACKUP_DIR}/{container.name}/{database}.tar', 'wb') as outfile:
            for d in container.get_archive(f'{container_workdir}{database}')[0]:
                outfile.write(d)

        # clean up
        container.exec_run(f'rm -r {container_workdir}{database}')

        return [
            "MongoDB",
            container.name,
            database,
            convert_size(os.path.getsize(path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ]


def docker_postgres_backup(container, username, password, database):
    # path where the backup should be stored
    path = f'{BACKUP_DIR}/{container.name}/{database}.sql'
    # check if the backup of the database does already exist
    if os.path.exists(path):
        print_verbose(f'Backup of (postgresql) {database} database has been skipped!')
        return [
            "PostgreSQL",
            container.name,
            database,
            " ",
            f'{Fore.YELLOW}Skipped{Fore.RESET}'
        ]

    print_verbose(f'Backup of (postgresql) {database} database has been started!')

    # https://www.postgresql.org/docs/current/libpq-pgpass.html
    #if username and password:
    #    container.exec_run(f'echo "localhost:*:{database}:{username}:{password}" | tee -a /root/.pgpass')

    #print(container.exec_run('ls -a /root/'))
    #print(container.exec_run('cat /root/.pgpass'))

    # execute the backup command
    cmd = ''
    if password:
        print("PostgreSQL doesn't work with Auth...")
        # cmd += f'export PGPASSWORD="{password}" '   # <-- should work, but export not found
    cmd += f'pg_dump -h localhost -U{username} {database}'
    res = container.exec_run(cmd)
    print(res)

    if res.exit_code != 0:
        print_verbose(f'{Fore.RED}PostgreSQL Database {database} backup was not successful.{Fore.RESET}')
        return [
            "PostgreSQL",
            container.name,
            database,
            " ",
            f'{Fore.RED}Failed ({res.exit_code}){Fore.RESET}'
        ]
    else:
        with open(path, 'wb') as f:
            f.write(res.output)

        # clean up
        #if username and password:
        #    container.exec_run(f'rm /root/.pgpass')

        return [
            "PostgreSQL",
            container.name,
            database,
            convert_size(os.path.getsize(path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
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
        if check_check_sums(check_sums):
            for method in check_sums:
                with open(f'{BACKUP_DIR}/{method}sum.txt', 'a') as f:
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
def check_check_sums(lst):
    allow = ("md5", "sha1", "sha224", "sha384", "sha256", "sha512")
    ret = not any(sum not in allow for sum in lst)
    if not ret:
        print_verbose(f"Invalid methods: {', '.join(set(lst).difference(set(allow)))}")
    return ret


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

    for job in jobs:
        if job == 'database':
            data = list()
            mysql_backup_config: list = config.get('mysql') or list()
            mongodb_backup_config: list = config.get('mongodb') or list()
            postgres_backup_config: list = config.get('postgres') or list()
            for cfg in mysql_backup_config:
                db_container_name = cfg.get('container_name') or 'main_mariadb_1'
                db_username = cfg.get('username') or 'backup'
                db_password = cfg.get('password')
                databases = cfg.get('databases') or ['mysql']

                container = list(filter(lambda c: c.name == db_container_name, docker_env().containers.list()))[0]

                # create directory for backups of this container if it doesn't exist
                if not os.path.isdir(f'{BACKUP_DIR}/{container.name}'):
                    os.mkdir(f'{BACKUP_DIR}/{container.name}/')

                for database in databases:
                    data.append(docker_mysql_backup(container, db_username, db_password, database))

            for cfg in mongodb_backup_config:
                db_container_name = cfg.get('container_name') or 'main_mongodb_1'
                db_username = cfg.get('username')
                db_password = cfg.get('password')
                databases = cfg.get('databases') or ['admin']

                container = list(filter(lambda c: c.name == db_container_name, docker_env().containers.list()))[0]

                # create directory for backups of this container if it doesn't exist
                if not os.path.isdir(f'{BACKUP_DIR}/{container.name}'):
                    os.mkdir(f'{BACKUP_DIR}/{container.name}/')

                for database in databases:
                    data.append(docker_mongodb_backup(container, db_username, db_password, database))

            for cfg in postgres_backup_config:
                db_container_name = cfg.get('container_name') or 'main_postgres_1'
                db_username = cfg.get('username') or 'postgres'
                db_password = cfg.get('password')
                databases = cfg.get('databases') or ['postgres']

                container = list(filter(lambda c: c.name == db_container_name, docker_env().containers.list()))[0]

                # create directory for backups of this container if it doesn't exist
                if not os.path.isdir(f'{BACKUP_DIR}/{container.name}'):
                    os.mkdir(f'{BACKUP_DIR}/{container.name}/')

                for database in databases:
                    data.append(docker_postgres_backup(container, db_username, db_password, database))

            if data:
                # create table
                table = PrettyTable()
                table.title = "Database Backup Status"
                table.field_names = ["Type", "Container", "Database", "Size", "Status"]
                for row in data:
                    table.add_row(row)
                table.align['Type'] = 'l'
                table.align['Container'] = 'l'
                table.align['Database'] = 'l'
                table.align['Size'] = 'r'
                table.sortby = 'Container'
                print(table)
            else:
                print("Skipped database backup - nothing to do!")

        if job == 'files':
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

        if job == 'gitlab':
            print("GitLab repository backup has been started!")
            git_container = config.get('gitlab').get('container_name') or 'main_gitlab_1'
            container = list(filter(lambda c: c.name == git_container, docker_env().containers.list()))[0]

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

    try:
        global conf
        conf = json.loads(open(CONFIG_FILE).read())
    except ValueError:
        print(f'{CONFIG_FILE} does not contain valid json.')
        exit(1)

    main(conf)
