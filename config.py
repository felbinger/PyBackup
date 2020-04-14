from typing import List
import os


class Config:
    def __init__(self, json: dict):
        self.backup_dir: str = json.get('backup_dir') or '/home/backups'
        self.mariadb: List[Config.MariaDB] = list()
        for cfg in json.get('mariadb'):
            self.mariadb.append(self.MariaDB(cfg))
        self.mongodb: List[Config.MongoDB] = list()
        for cfg in json.get('mongodb'):
            self.mongodb.append(self.MongoDB(cfg))
        self.postgres: List[Config.PostgreSQL] = list()
        for cfg in json.get('postgres'):
            self.postgres.append(self.PostgreSQL(cfg))
        self.gitlab: dict = json.get('gitlab')
        self.files: dict = json.get('files')
        self.checksums: dict = json.get('checksums') or list()

        if not isinstance(self.backup_dir, str):
            print("Error: Backup directory is not properly initialized! Exiting.")
            exit(1)

        if not os.path.isdir(self.backup_dir):
            os.mkdir(self.backup_dir)

    def validate(self):
        pass
        # TODO implement

    class MariaDB:
        def __init__(self, json: dict):
            self.container_name: str = json.get('container_name') or 'main_mariadb_1'
            self.host: str = json.get('host') or 'localhost'
            self.port: int = json.get('port') or 3306
            self.username: str = json.get('username')
            self.password: str = json.get('password')
            self.databases: list = json.get('databases') or ['mysql']
            self.skip_existing: bool = json.get('skip_existing') or True

    class MongoDB:
        def __init__(self, json: dict):
            self.container_name: str = json.get('container_name') or 'main_mongodb_1'
            self.host: str = json.get('host') or 'localhost'
            self.port: int = json.get('port') or 27017
            self.username: str = json.get('username')
            self.password: str = json.get('password')
            self.authentication_database: str = json.get('authentication_database') or 'admin'
            self.authentication_mechanism: str = json.get('authentication_mechanism') or 'SCRAM-SHA-1'
            self.databases: list = json.get('databases') or ['admin']
            self.skip_existing: bool = json.get('skip_existing') or True

    class PostgreSQL:
        def __init__(self, json: dict):
            self.container_name: str = json.get('container_name') or 'main_postgresql_1'
            self.host: str = json.get('host') or 'localhost'
            self.port: int = json.get('port') or 5432
            self.username: str = json.get('username') or 'postgres'
            self.password: str = json.get('password')
            self.databases: list = json.get('databases') or ['postgres']
            self.skip_existing: bool = json.get('skip_existing') or True


def create_from_json(json: dict) -> Config:
    return Config(json)
