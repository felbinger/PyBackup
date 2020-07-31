from docker.models.containers import Container
from colorama import Fore

from . import Printer


class GitLab:
    def __init__(self, container: Container = None):
        self.container = container

    def backup(self):
        Printer.print(f'{Fore.YELLOW}GitLab repository backup has been started!{Fore.RESET}')
        result, stdout = self.container.exec_run('gitlab-rake gitlab:backup:create')

        if result.exit_code != 0:
            Printer.print(f'{Fore.YELLOW}GitLab repository backup failed ({res.status_code})!{Fore.RESET}')
            Printer.print(stdout.decode(), 0)
        else:
            Printer.print(f'{Fore.YELLOW}GitLab repository backup completed!{Fore.RESET}')
