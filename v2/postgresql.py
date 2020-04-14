from docker.models.containers import Container
import subprocess
from datetime import datetime
from colorama import Fore
import os

from . import Printer, DatabaseResult, secure, remove_timestamp, convert_size


class PostgreSQL:
    dump_cmd: str = 'pg_dump'

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 5432,
                 username: str = 'postgres',
                 password: str = '',
                 databases: list = list(),
                 path: str = '/home/backups',
                 container: Container = None,
                 skip_existing: bool = True):
        # pg_dump options
        self.options: dict = dict()
        self.options['host'] = host
        self.options['port'] = port
        self.options['username'] = username
        # self.options['password'] = password  # TODO how to set password? ~/.pgpass, export PGPASSWORD=?

        self.databases: list = databases or ['postgres']
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
        postgres_path = f'{self.path}{self.container.name}/' if container else f'{self.path}/postgres/'
        if not os.path.isdir(postgres_path):
            os.mkdir(postgres_path)

    def backup(self):
        # add the pg_dump options to the command
        for key, value in self.options.items():
            self.dump_cmd += f' --{key}={value}'
        # execute the pg_dump command for each database
        for database in self.databases:
            self.database = database
            cmd = f'{self.dump_cmd} --dbname={database}'
            self.docker_exec(cmd) if self.container else self.exec(cmd)

    # TODO test local backup: not working
    def exec(self, cmd: str):
        backup_path = f'{self.path}/postgres/{self.database}.sql'
        if self.skip_existing and os.path.isfile(backup_path):
            Printer.print(
                f'{Fore.YELLOW}PostgreSQL Database {self.database} backup already exists. Skipping!{Fore.RESET}')
            return DatabaseResult.data.append([
                "PostgreSQL",
                "<host>",
                self.database,
                " ",
                f'{Fore.YELLOW}Skipped{Fore.RESET}'
            ])
        Printer.print(f'{Fore.YELLOW}PostgreSQL Database {self.database} backup has been started!{Fore.RESET}')
        Printer.print(f'Executing: {secure(cmd)}', 0)
        result = subprocess.run(cmd.split(' '), capture_output=True)
        if result.returncode != 0:
            Printer.print(f'{Fore.RED}MongoDB Database {self.database} backup was not successful!{Fore.RESET}')
            Printer.print(result.stdout.decode(), 0)
            return DatabaseResult.data.append([
                "PostgreSQL",
                "<host>",
                self.database,
                " ",
                f'{Fore.RED}Failed{Fore.RESET}'
            ])

        with open(backup_path, 'wb') as f:
            f.write(result.stdout)

        return DatabaseResult.data.append([
            "PostgreSQL",
            "<host>",
            self.database,
            convert_size(os.path.getsize(backup_path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])

    def docker_exec(self, cmd: str):
        backup_path = f'{self.path}/{self.container.name}/{self.database}.sql'
        if self.skip_existing and os.path.isfile(backup_path):
            Printer.print(
                f'{Fore.YELLOW}PostgreSQL Database {self.database} backup already exists. Skipping!{Fore.RESET}')
            return DatabaseResult.data.append([
                "PostgreSQL",
                self.container.name,
                self.database,
                " ",
                f'{Fore.YELLOW}Skipped{Fore.RESET}'
            ])
        Printer.print(f'{Fore.YELLOW}PostgreSQL Database {self.database} backup has been started!{Fore.RESET}')
        Printer.print(f'Executing ({self.container.name}): {secure(cmd)}', 0)
        result, stdout = self.container.exec_run(cmd)
        if result != 0:
            Printer.print(f'{Fore.RED}PostgreSQL Database {self.database} backup was not successful!{Fore.RESET}')
            Printer.print(stdout.decode(), 0)
            return DatabaseResult.data.append([
                "PostgreSQL",
                self.container.name,
                self.database,
                " ",
                f'{Fore.RED}Failed{Fore.RESET}'
            ])

        with open(backup_path, 'wb') as f:
            f.write(stdout)

        Printer.print(f'{Fore.GREEN}PostgreSQL Database {self.database} backup was successful.{Fore.RESET}')

        return DatabaseResult.data.append([
            "PostgreSQL",
            self.container.name,
            self.database,
            convert_size(os.path.getsize(backup_path)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])
