import logging

from datetime import datetime
from pathlib import Path

from .file.checksum import ChecksumLib


logger = logging.getLogger(__name__)


class Checksums:

    def __init__(self, path: str = '/home/backups', methods: list = ['sha256']):
        self.methods = Checksums._check_methods(methods)

        # path where the backup should be stored
        date = datetime.now().strftime("%Y-%m-%d")
        self.path: Path = Path(path) / date
        if not self.path.exists():
            logger.info("Create backup folder")
            self.path.mkdir()

    def generate_all(self):
        cl = ChecksumLib()

        for file in self.path.rglob("*"):
            if not file.is_file():
                continue
            for method in self.methods:
                cf = self.path / f'{method}sum.txt'
                if cf.exists():
                    logger.info("File '%s' already exists but will be removed", cf)
                    cf.unlink()
                with (self.path / f'{method}sum.txt').open('a') as f:
                    c = cl.get_checksum_file(file, method)
                    f.write(f'{c}\t{file}\n')

    # check if the check sums from the config file are all valid method names from the hashlib module
    @staticmethod
    def _check_methods(methods: list) -> set:
        valid = ChecksumLib.algorithms_available() & set(methods)
        if len(valid) < len(methods):
            logger.warning("Invalid checksum method(s): %s", ",".join(set(methods) - valid))
        return valid
