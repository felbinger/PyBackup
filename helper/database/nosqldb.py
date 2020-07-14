from docker.models.containers import Container
from .db import _Database


class MongoDB(_Database):
    _DB_NAME = "mongodb"
    _DUMB_CMD = 'mongodump'
    _FILE_PARAM = '--gzip --out='
    _DUMB_FILE_EXT = ".tar"
    _PARAM_NAMES = {
        'host': '--host=',
        'port': '--port=',
        'username': '--username=',
        'password': '--password=',
        'authenticationDatabase': '--authenticationDatabase=',
        'authenticationMechanism': '--authenticationMechanism=',
        'db': '--db='
    }

    def __init__(self, host: str = 'localhost', port: int = 27017, username: str = '', password: str = '',
                 path: str = '/home/backups', container: Container = None, skip_existing: bool = True,
                 authentication_database: str = 'admin', authentication_mechanism: str = 'SCRAM-SHA-1'):
        super(MongoDB, self).__init__(dbname=self._DB_NAME, host=host, port=port, username=username,
                                      path=path, container=container, skip_existing=skip_existing)
        if password:
            self._params['password'] = password
            self._params['authenticationDatabase'] = authentication_database
            self._params['authenticationMechanism'] = authentication_mechanism

    @staticmethod
    def get_dbname() -> str:
        return MongoDB._DB_NAME
