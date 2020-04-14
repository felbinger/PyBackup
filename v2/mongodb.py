from docker.models.containers import Container
import subprocess
from datetime import datetime
from colorama import Fore
from shutil import move
import os
from tarfile import is_tarfile

from . import Printer, DatabaseResult, secure, remove_timestamp, convert_size


class MongoDB:
    dump_cmd = 'mongodump --gzip --out=/data/transfer/'

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 27017,
                 username: str = '',
                 password: str = '',
                 authentication_database: str = 'admin',
                 authentication_mechanism: str = 'SCRAM-SHA-1',
                 databases: list = list(),
                 path: str = '/home/backups',
                 container: Container = None,
                 skip_existing: bool = True):
        # mongodump options
        self.options: dict = dict()
        self.options['host'] = host
        self.options['port'] = port
        if username and password:
            self.options['username'] = username
            self.options['password'] = password
            self.options['authenticationDatabase'] = authentication_database
            self.options['authenticationMechanism'] = authentication_mechanism

        self.databases: list = databases or ['admin']
        self.database: str = ''

        # docker container in which the command should be executed
        self.container = container

        # skip the creation of backup's that already exist
        self.skip_existing = skip_existing

        # path where the backup should be stored
        date = datetime.now().strftime("%Y-%m-%d")
        if path.endswith("/"):
            path = path[:-1]
        self.path: str = f'{path}/{date}/'
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        mongodb_path = f'{self.path}{self.container.name}/' if container else f'{self.path}mongodb/'
        if not os.path.isdir(mongodb_path):
            os.mkdir(mongodb_path)

    def backup(self):
        # add the mongodump options to the command
        for key, value in self.options.items():
            self.dump_cmd += f' --{key}={value}'
        # execute the mongodump command for each database
        for database in self.databases:
            self.database = database
            cmd = f'{self.dump_cmd} --db={database}'
            self.docker_exec(cmd) if self.container else self.exec(cmd)

    # TODO test local backup: not working
    def exec(self, cmd: str):
        backup_path = f'{self.path}/mongodb/{self.database}'
        if os.path.isdir(backup_path):
            if self.skip_existing:
                Printer.print(f'{Fore.YELLOW}MongoDB Database {self.database} backup already exists. Skipping!{Fore.RESET}')
                return DatabaseResult.data.append([
                    "MongoDB",
                    "<host>",
                    self.database,
                    " ",
                    f'{Fore.YELLOW}Skipped{Fore.RESET}'
                ])
            else:
                os.rmdir(backup_path)

        Printer.print(f'{Fore.YELLOW}MongoDB Database {self.database} backup has been started!{Fore.RESET}', 0)
        Printer.print(f'Executing: {secure(cmd)}', 0)
        result = subprocess.run(cmd.split(' '), capture_output=True)
        if result.returncode != 0:
            Printer.print(f'{Fore.RED}MongoDB Database {self.database} backup was not successful!{Fore.RESET}')
            Printer.print(result.stdout.decode(), 0)
            return DatabaseResult.data.append([
                "MongoDB",
                "<host>",
                self.database,
                " ",
                f'{Fore.RED}Failed{Fore.RESET}'
            ])

        Printer.print(f'Moving backup from /data/transfer/{self.database}/ to {backup_path}...', 0)
        move(f'/data/transfer/{self.database}/', backup_path)
        return DatabaseResult.data.append([
            "MongoDB",
            "<host>",
            self.database,
            convert_size(os.path.getsize(backup_path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])

    def docker_exec(self, cmd: str):
        backup_path = f'{self.path}/{self.container.name}/{self.database}.tar'
        if self.skip_existing and os.path.isfile(backup_path) and is_tarfile(backup_path):
            Printer.print(f'{Fore.YELLOW}MongoDB Database {self.database} backup already exists. Skipping!{Fore.RESET}')
            return DatabaseResult.data.append([
                "MongoDB",
                self.container.name,
                self.database,
                " ",
                f'{Fore.YELLOW}Skipped{Fore.RESET}'
            ])
        if os.path.isdir(backup_path):
            os.rmdir(backup_path)
        Printer.print(f'{Fore.YELLOW}MongoDB Database {self.database} backup has been started!{Fore.RESET}', 0)
        Printer.print(f'Executing ({self.container.name}): {secure(cmd)}', 0)
        result, stdout = self.container.exec_run(cmd)
        if result != 0:
            Printer.print(f'{Fore.RED}MongoDB Database {self.database} backup was not successful!{Fore.RESET}')
            Printer.print(remove_timestamp(stdout.decode()), 0)
            return DatabaseResult.data.append([
                "MongoDB",
                self.container.name,
                self.database,
                " ",
                f'{Fore.RED}Failed{Fore.RESET}'
            ])

        Printer.print(f'Copying Backup from {self.container.name} to host...', 0)
        with open(backup_path, 'wb') as outfile:
            for d in self.container.get_archive(f'/data/transfer/{self.database}')[0]:
                outfile.write(d)

        Printer.print(f'{Fore.GREEN}MongoDB Database {self.database} backup was successful.{Fore.RESET}')

        return DatabaseResult.data.append([
            "MongoDB",
            self.container.name,
            self.database,
            convert_size(os.path.getsize(backup_path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])
