from docker.models.containers import Container
import subprocess
from datetime import datetime
from colorama import Fore
import os

from . import Printer, DatabaseResult, secure, remove_timestamp, convert_size
from .database.db import Database


class PostgreSQL:

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 5432,
                 username: str = 'postgres',
                 password: str = '',
                 databases: list = list(),
                 path: str = '/home/backups',
                 container: Container = None,
                 skip_existing: bool = True):
        self._db = Database("postgres", host, port, username, password, path, container, skip_existing)
        self.databases: list = databases or ['postgres']
        self.container = container

    def backup(self):
        for database in self.databases:
            self.docker_exec(database) if self.container else self.exec(database)

    def docker_exec(self, db: str):
        try:
            result = self._db.backup_db(db)
        except:
            return DatabaseResult.data.append([
                "PostgreSQL",
                self.container.name,
                db,
                " ",
                f'{Fore.RED}Failed{Fore.RESET}'
            ])

        if not result:
            return DatabaseResult.data.append([
                "PostgreSQL",
                self.container.name,
                db,
                " ",
                f'{Fore.YELLOW}Skipped{Fore.RESET}'
            ])

        return DatabaseResult.data.append([
            "PostgreSQL",
            self.container.name,
            db,
            convert_size(result["size"]),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])

    def exec(self, db):
        pass
