import logging

from datetime import datetime
from pathlib import Path

from docker.models.containers import Container


logger = logging.getLogger(__name__)


class _MetaDatabase(type):

    def __call__(self, dbname: str = '', *args, **kwargs):
        if not dbname or dbname not in _Database.get_available_dbs():
            raise ValueError('The database is not supported')

        for cls in _Database.__subclasses__():
            if not cls.get_dbname():
                continue
            if dbname.lower() == cls.get_dbname():
                return cls(*args, **kwargs)


class _Database:
    _DB_NAME = "database"
    _DUMB_CMD = ""
    _FILE_PARAM = ""
    _DUMB_FILE_EXT = ""
    _PARAM_NAMES = {}

    def __init__(self, dbname: str = '', host: str = 'localhost', port: int = 0, username: str = '',
                 path: str = '/home/backups', container: Container = None, skip_existing: bool = True):
        params = dict()
        params['host'] = host
        params['port'] = port
        params['username'] = username
        self._params = params

        self._container = container
        self._skip_existing = skip_existing
        self._dbname = dbname if dbname else self._DB_NAME

        date = datetime.now().strftime("%Y-%m-%d")
        self._path: Path = Path(path) / date / (container.name if container else self._dbname)
        if not self._path.exists():
            logger.info("Create backup folder")
            self._path.mkdir(parents=True)

    @staticmethod
    def get_dbname() -> str:
        raise NotImplementedError

    @staticmethod
    def get_available_dbs() -> list:
        return [db.get_dbname() for db in _Database.__subclasses__() if db.get_dbname()]

    def backup_dbs(self, dbs: list):
        for db in dbs:
            self.backup_db(db)

    def backup_db(self, db: str) -> dict:
        _backup = self._container_db if self._container else self._local_db
        backup_path = self._path / (f"{db}.tar" if self._container else f"{db}{self._DUMB_FILE_EXT}")

        if backup_path.exists() and self._skip_existing:
            logger.info("%s Database %s backup already exists. Skipping!", self._dbname, db)
            return None

        logger.debug("%s Database %s backup has been started!", self._dbname, db)
        return _backup(db, backup_path)

    def _build_cmd(self, db: str, path_save_arg: str) -> str:
        cmd = f"sh -c '{self._DUMB_CMD} {self._PARAM_NAMES['db']}{db}"
        cmd += " ".join(f" {self._PARAM_NAMES[key]}{value}" for key, value in self._params.items() if value)
        cmd += f" {path_save_arg}'"

        logger.debug("Executing: %s", cmd)
        return cmd

    def _container_db(self, db: str, path: Path) -> bool:
        docker_path = f"/tmp/{db}{self._DUMB_FILE_EXT}"
        cmd = self._build_cmd(db, f"{self._FILE_PARAM}{docker_path}")
        result, stdout = self._container.exec_run(cmd)

        if result != 0:
            logger.error("%s Database %s backup was not successful!", self._dbname, db)
            logger.error(stdout.decode())
            raise

        logger.info("Copy Backup from %s to host ...", self._container.name)
        data, stat = self._container.get_archive(docker_path)
        with open(path, 'wb') as f:
            for d in data:
                f.write(d)

        logger.info("%s Database %s backup was successful", self._dbname, db)
        return stat

    def _local_db(self, db: str, path: Path) -> bool:
        pass


class Database(_Database, metaclass=_MetaDatabase):

    @staticmethod
    def get_dbname() -> str:
        return None
