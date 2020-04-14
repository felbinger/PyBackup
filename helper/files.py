from datetime import datetime
from shutil import copyfile
from colorama import Fore
from tarfile import is_tarfile, open as tar_open
import os

from . import Printer, FileResult, sizeof, convert_size


class File:
    def __init__(self, src: str = '', path: str = '/home/backups'):
        self.src = src

        # path where the backup should be stored
        date = datetime.now().strftime("%Y-%m-%d")
        if path.endswith("/"):
            path = path[:-1]
        self.path: str = f'{path}/{date}/'
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def backup(self):
        if os.path.isdir(self.src):
            self.dir_backup()
        if os.path.isfile(self.src):
            self.file_backup()

    # create tar.gz file of src
    def dir_backup(self):
        src_basename = os.path.basename(self.src)
        dest = f'{self.path}{src_basename}.tar.gz'
        if os.path.isfile(dest) and is_tarfile(dest):
            Printer.print(f'{Fore.YELLOW}{dest} already exist. Skipping!{Fore.RESET}')
            return FileResult.data.append([
                self.src,
                " ",
                " ",
                f'{Fore.YELLOW}Skipped{Fore.RESET}'
            ])
        Printer.print(f'{Fore.YELLOW}Archiving {self.src} to {dest}.{Fore.RESET}')
        with tar_open(dest, "w:gz") as target_fd:
            target_fd.add(self.src, arcname=src_basename)
        return FileResult.data.append([
            self.src,
            sizeof(self.src),
            convert_size(os.path.getsize(dest)) + ' (compressed)',
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])

    # copy src to dest
    def file_backup(self):
        src_basename = os.path.basename(self.src)
        dest = f'{self.path}{src_basename}'
        if os.path.isfile(dest):
            if os.path.getsize(self.src) == os.path.getsize(dest):
                Printer.print(f'{Fore.YELLOW}{dest} already exist. Skipping!{Fore.RESET}')
                return FileResult.data.append([
                    self.src,
                    " ",
                    " ",
                    f'{Fore.YELLOW}Skipped{Fore.RESET}'
                ])
            else:
                Printer.print(f'{Fore.YELLOW}{dest} already exist, but size differs!{Fore.RESET}')
                os.remove(dest)
        Printer.print(f'{Fore.YELLOW}Copying {self.src} to {dest}.{Fore.RESET}')
        copyfile(self.src, dest)
        return FileResult.data.append([
            self.src,
            sizeof(self.src),
            convert_size(os.path.getsize(dest)),
            f'{Fore.GREEN}OK{Fore.RESET}'
        ])
