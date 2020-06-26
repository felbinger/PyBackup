from __future__ import annotations

import logging
import hashlib
import hmac

from pathlib import Path
from typing import Union, Generator

from .filehandler import FileHandler, validate_path


logger = logging.getLogger(__name__)


class ChecksumLib:
    _DEFAULT_SHAKE_LENGTH = 32

    def __init__(self, length: int = 0):
        self._shake_length = length if length else self._DEFAULT_SHAKE_LENGTH
        self._file = FileHandler(chunk_size=2048)

    @validate_path
    def get_checksum_file(self, path: Path, algorithm: str) -> Checksum:
        gen = self._file.iter_read_file
        if algorithm not in Checksum.algorithms_available():
            logger.warning("Invalid checksum algorithm")
            return None
        return self._get_checksum(gen, algorithm, path)

    @validate_path
    def get_checksum_dir(self, path: Path, algorithm: str) -> Checksum:
        gen = self._file.iter_read_dir
        if algorithm not in Checksum.algorithms_available():
            logger.warning("Invalid checksum algorithm")
            return None
        return self._get_checksum(gen, algorithm, path)

    def _get_checksum(self, gen: Generator[bytes], algorithm: str, path: Path):
        c = Checksum(algorithm, self._shake_length)
        for b in gen(path):
            c.update(b)
        return c

    @staticmethod
    def algorithms_available() -> set:
        return Checksum.algorithms_available()


class Checksum:
    _DEFAULT_ALGORITHMS = 'sha1'
    _SHAKE = {'shake_128', 'shake_256'}
    _DEFAULT_SHAKE_LENGTH = 32

    def __init__(self, algorithm: str = '', length: int = 0):
        self._algorithm = algorithm if algorithm in Checksum.algorithms_available() else self._DEFAULT_ALGORITHMS
        self._shake_length = length if length else self._DEFAULT_SHAKE_LENGTH
        self._hash = hashlib.new(self._algorithm)

    @staticmethod
    def algorithms_available() -> set:
        return hashlib.algorithms_available

    def update(self, data: bytes):
        self._hash.update(data)

    def to_bytes(self) -> bytes:
        return self._hash.digest(*self._get_args())

    def to_int(self) -> int:
        return int.from_bytes(self.to_bytes(), 'big')

    def to_str(self) -> str:
        return self._hash.hexdigest(*self._get_args())

    def __eq__(self, checksum: Union[Checksum, str, bytes, int]) -> bool:
        if isinstance(checksum, bytes):
            return hmac.compare_digest(bytes(self), checksum)
        if isinstance(checksum, int):
            return int(self) == checksum
        if isinstance(checksum, str):
            return str(self) == checksum
        if isinstance(checksum, self.__class__):
            if self.get_algorithm() is not checksum.get_algorithm():
                logger.warning("The compared checksum have different algorithms")
                return False
            return hmac.compare_digest(bytes(self), bytes(checksum))
        return False

    def __bytes__(self) -> bytes:
        return self.to_bytes()

    def __int__(self) -> int:
        return self.to_int()

    def __str__(self) -> str:
        return self.to_str()

    def _get_args(self) -> list:
        return [self._shake_length] if self._algorithm in self._SHAKE else []
