import os


class Config:
    backup_dir: str = ""
    mariadb: list = list()
    mongodb: list = list()
    postgres: list = list()
    gitlab: dict = dict()
    files: dict = list()
    checksums: dict = list()

    def __init__(self, json: dict):
        self.backup_dir = json.get('backup_dir')
        for cfg in json.get('mariadb'):
            self.mariadb.append(self.MariaDB(cfg))
        for cfg in json.get('mongodb'):
            self.mongodb.append(self.MongoDB(cfg))
        for cfg in json.get('postgres'):
            self.postgres.append(self.PostgreSQL(cfg))
        self.gitlab = json.get('gitlab')
        self.files = json.get('files')
        self.checksums = json.get('checksums')

        if not isinstance(self.backup_dir, str):
            print("Error: Backup directory is not properly initialized! Exiting.")
            exit(1)

        if not os.path.isdir(self.backup_dir):
            os.mkdir(self.backup_dir)

    def validate(self):
        pass
        # TODO implement

    class MariaDB:
        container_name: str = ''
        host: str = ''
        port: int = 3306
        username: str = ''
        password: str = ''
        databases: list = list()
        skip_existing: bool = True

        def __init__(self, json: dict):
            self.container_name = json.get('container_name') or 'main_mariadb_1'
            self.host = json.get('host') or 'localhost'
            self.port = json.get('port') or 3306
            self.username = json.get('username')
            self.password = json.get('password')
            self.databases = json.get('databases') or list()
            self.skip_existing = json.get('skip_existing')

    class MongoDB:
        container_name: str = ''
        host: str = ''
        port: int = 27017
        username: str = ''
        password: str = ''
        authentication_database: str = ''
        authentication_mechanism: str = ''
        databases: list = list()
        skip_existing: bool = True

        def __init__(self, json: dict):
            self.container_name = json.get('container_name') or 'main_mongodb_1'
            self.host = json.get('host') or 'localhost'
            self.port = json.get('port') or 27017
            self.username = json.get('username')
            self.password = json.get('password')
            self.authentication_database = json.get('authentication_database')
            self.authentication_mechanism = json.get('authentication_mechanism')
            self.databases = json.get('databases') or list()
            self.skip_existing = json.get('skip_existing')

    class PostgreSQL:
        container_name: str = ''
        host: str = ''
        port: int = 5432
        username: str = ''
        password: str = ''
        databases: list = list()
        skip_existing: bool = True

        def __init__(self, json: dict):
            self.container_name = json.get('container_name') or 'main_postgresql_1'
            self.host = json.get('host') or 'localhost'
            self.port = json.get('port') or 5432
            self.username = json.get('username') or 'postgres'
            self.password = json.get('password')
            self.databases = json.get('databases') or list()
            self.skip_existing = json.get('skip_existing')


def create_from_json(json: dict) -> Config:
    return Config(json)
