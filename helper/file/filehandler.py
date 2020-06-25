import logging

from pathlib import Path, WindowsPath, PosixPath
from typing import Union, Generator


logger = logging.getLogger(__name__)


def validate_path(func):
    def wrapper(cls, path: Union[str, Path] = "", *args, **kwargs):
        if not path:
            return None
        if isinstance(path, str):
            path = Path(path)
        if not isinstance(path, (PosixPath, WindowsPath)):
            logger.warning("The given path is not an Path object but from type %s", type(path))
            return None
        if not path.exists():
            logger.warning("The specified path doesn't exists")
            return None

        return func(cls, path, *args, **kwargs)
    return wrapper


class FileHandler:
    _DEFAULT_CHUNK_SIZE = 2048

    def __init__(self, chunk_size: int = 0):
        self._chunk_size = chunk_size if chunk_size else self._DEFAULT_CHUNK_SIZE

    @validate_path
    def iter_read_file(self, path: Path) -> Generator[bytes, None, None]:
        if not path.is_file():
            logger.warning("The specified path is not a file")
            return None

        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(self._chunk_size), b''):
                yield chunk

    @validate_path
    def iter_read_dir(self, path: Path, pattern: str = '*') -> Generator[bytes, None, None]:
        if not path.is_dir():
            logger.warning("The specified path is not a folder")
            return None

        for file in path.rglob(pattern):
            if not file.is_file():
                continue
            yield from self.iter_read_file(file)
