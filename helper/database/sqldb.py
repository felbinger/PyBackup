from docker.models.containers import Container
from .db import _Database


class PostgreSQL(_Database):
    _DB_NAME = "postgres"
    _DUMB_CMD = 'pg_dump'
    _FILE_PARAM = '> '
    _DUMB_FILE_EXT = ".sql"
    _PARAM_NAMES = {
        'host': '--host=',
        'port': '--port=',
        'username': '--username=',
        'db': '--db='
    }

    def __init__(self, host: str = 'localhost', port: int = 5432, username: str = 'postgres', password: str = '',
                 path: str = '/home/backups', container: Container = None, skip_existing: bool = True):
        super(PostgreSQL, self).__init__(dbname=self._DB_NAME, host=host, port=port, username=username,
                                         path=path, container=container, skip_existing=skip_existing)

    @staticmethod
    def get_dbname() -> str:
        return PostgreSQL._DB_NAME


class MySQL(_Database):
    _DB_NAME = "mysql"
    _DUMB_CMD = 'mysqldump --lock-tables'
    _FILE_PARAM = '> '
    _DUMB_FILE_EXT = ".sql"
    _PARAM_NAMES = {
        'host': '--host=',
        'port': '--port=',
        'username': '--user=',
        'password': '--password=',
        'protocol': '--protocol=',
        'db': '--databases '
    }

    def __init__(self, host: str = 'localhost', port: int = 3306, username: str = '', password: str = '',
                 path: str = '/home/backups', container: Container = None, skip_existing: bool = True):
        super(MySQL, self).__init__(dbname=self._DB_NAME, host=host, port=port, username=username,
                                    path=path, container=container, skip_existing=skip_existing)
        self._params['protocol'] = 'tcp'
        self._params['password'] = password

    @staticmethod
    def get_dbname() -> str:
        return MySQL._DB_NAME
