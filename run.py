#!/usr/bin/python3.8

from colorama import init
from argparse import ArgumentParser
from time import time
from docker import from_env as docker_env
import os
import json
import platform
import logging

from config import Config, create_from_json
from helper import Printer, DatabaseResult, FileResult, MariaDB, MongoDB, PostgreSQL, GitLab, File, Checksums


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")


def main(config: Config, tasks: list):
    # check if the backup directory exists
    for task in tasks:
        if task == 'database':
            for mariadb in config.mariadb:
                container = list(filter(lambda c: c.name == mariadb.container_name, docker_env().containers.list()))
                if not container:
                    Printer.print(f'Database Container {mariadb.container_name} does not exist. Skipping!', 2)
                    continue
                MariaDB(
                    path=config.backup_dir,
                    host=mariadb.host,
                    port=mariadb.port,
                    username=mariadb.username,
                    password=mariadb.password,
                    databases=mariadb.databases,
                    skip_existing=mariadb.skip_existing,
                    container=container[0]
                ).backup()

            for mongodb in config.mongodb:
                container = list(filter(lambda c: c.name == mongodb.container_name, docker_env().containers.list()))
                if not container:
                    Printer.print(f'Database Container {mongodb.container_name} does not exist. Skipping!', 2)
                    continue
                MongoDB(
                    path=config.backup_dir,
                    host=mongodb.host,
                    port=mongodb.port,
                    username=mongodb.username,
                    password=mongodb.password,
                    databases=mongodb.databases,
                    skip_existing=mongodb.skip_existing,
                    container=container[0]
                ).backup()

            for postgres in config.postgres:
                container = list(filter(lambda c: c.name == postgres.container_name, docker_env().containers.list()))
                if not container:
                    Printer.print(f'Database Container {postgres.container_name} does not exist. Skipping!', 2)
                    continue
                PostgreSQL(
                    path=config.backup_dir,
                    host=postgres.host,
                    port=postgres.port,
                    username=postgres.username,
                    password=postgres.password,
                    databases=postgres.databases,
                    skip_existing=postgres.skip_existing,
                    container=container[0]
                ).backup()

        elif task == 'files' and config.files:
            for file in config.files:
                File(src=file, path=config.backup_dir).backup()

        elif task == 'gitlab' and config.gitlab:
            container = list(filter(lambda c: c.name == config.gitlab.container_name, docker_env().containers.list()))
            if not container:
                Printer.print(f'GitLab Container {config.gitlab.container_name} does not exist. Skipping!', 2)
                continue
            GitLab(container[0]).backup()

    # Generate Checksums
    checksums = Checksums(path=config.backup_dir)
    checksums.generate_all()

    # Reporting
    dr = DatabaseResult()
    dr.sortby = 'Container'
    dr.print()
    fr = FileResult()
    fr.print()


if __name__ == '__main__':
    # initialize colorama
    init()

    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', help='verbose output', action="store_true")
    parser.add_argument('-q', '--quiet', help='quiet mode', action="store_true")
    parser.add_argument('-c', '--config', help='config file', nargs=1)
    parser.add_argument('-a', '--all', help='backup everything', action="store_true")
    parser.add_argument('-d', '--database', help='backup databases', action="store_true")
    parser.add_argument('--gitlab', help='backup gitlab', action="store_true")
    parser.add_argument('-f', '--files', help='backup files', action="store_true")

    # get arguments
    args = vars(parser.parse_args())
    Printer.verbose = args.get('verbose') or False
    Printer.quiet = args.get('quiet') or False
    Printer.date = False

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

    if platform.system() != "Windows" and os.geteuid() != 0:
        print("You need to have elevated privileges to run this script!")
        exit(1)

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
    START = time()
    main(config_obj, jobs)
