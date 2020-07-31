from docker.models.containers import Container
import subprocess
from datetime import datetime
from colorama import Fore
from shutil import move
import os
from tarfile import is_tarfile

from . import Printer, DatabaseResult, secure, remove_timestamp, convert_size
from .database.db import Database


import logging

logger = logging.getLogger(__name__)

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
        self._db = Database("mongodb", host, port, username, password, path, container, skip_existing,
                            authentication_database, authentication_mechanism)
        self.databases: list = databases or ['admin']
        self.container = container


    def backup(self):
        for database in self.databases:
            self.docker_exec(database) if self.container else self.exec(database)

    def docker_exec(self, db: str):
        try:
            result = self._db.backup_db(db)
        except Exception as e:
            logger.warning("%s", e)
            return DatabaseResult.data.append([
                "MongoDB",
                self.container.name,
                db,
                " ",
                f'{Fore.RED}Failed{Fore.RESET}'
            ])

        if not result:
            return DatabaseResult.data.append([
                "MongoDB",
                self.container.name,
                db,
                " ",
                f'{Fore.YELLOW}Skipped{Fore.RESET}'
            ])

        return DatabaseResult.data.append([
            "MongoDB",
            self.container.name,
            db,
            convert_size(result["size"]),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])

    def exec(self, db: str):
        pass
