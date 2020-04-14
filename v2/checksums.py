from datetime import datetime
import os
import hashlib

from . import Printer


class Checksums:
    def __init__(self, path: str = '/home/backups', methods: list = ['sha256']):
        self.methods = methods
        Checksums._check_methods(self.methods)

        # path where the backup should be stored
        date = datetime.now().strftime("%Y-%m-%d")
        if path.endswith("/"):
            path = path[:-1]
        self.path: str = f'{path}/{date}/'
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def generate_all(self):
        for method in self.methods:
            filename = f'{self.path[:-1]}/{method}sum.txt'
            if os.path.isfile(filename):
                os.remove(filename)
        for subdir, dirs, files in os.walk(self.path[:-1]):
            for filename in files:
                self.generate(f'{subdir}/{filename}')

    def generate(self, path):
        if Checksums._check_methods(self.methods):
            for method in self.methods:
                with open(f'{self.path[:-1]}/{method}sum.txt', 'a') as f:
                    generated_hash = getattr(hashlib, method)(open(path, 'rb').read()).hexdigest()
                    f.write(f'{generated_hash}\t{path}\n')

    # check if the check sums from the config file are all valid method names from the hashlib module
    @staticmethod
    def _check_methods(lst):
        allow = ("md5", "sha1", "sha224", "sha384", "sha256", "sha512")
        ret = not any(method not in allow for method in lst)
        if not ret:
            Printer.print(f"Invalid checksum method(s): {', '.join(set(lst).difference(set(allow)))}")
        return ret
