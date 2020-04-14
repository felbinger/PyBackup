from datetime import datetime
from prettytable import PrettyTable
import re
import os


class Printer:
    """
    verbose does overwrite quiet parameter!
    date can be used to add the date (generated with date_format) as prefix to the content
    """
    verbose = False
    quiet = False
    date = False
    date_format = "[%Y-%m-%d %H:%M:%S] "

    @staticmethod
    def print(content, importance=1):
        """
        importance 0: only on verbose
        importance 1: normal (not verbose, not quiet)
        importance 2: high, content will be shown even if quiet flag is set
        """
        prefix = datetime.now().strftime(Printer.date_format) if Printer.date else ''
        if Printer.verbose:
            print(prefix + content)
        elif importance == 1 and not Printer.quiet:
            print(prefix + content)
        elif importance == 2:
            print(prefix + content)


class Result:
    header: list = []
    data: list = list()
    table: PrettyTable = PrettyTable()
    title: str = ''
    alignments: list = []

    def print(self):
        if self.data:
            self.table.title = self.title
            self.table.field_names = self.header
            for row in self.data:
                self.table.add_row(row)
            for alignment in self.alignments:
                self.table.align[alignment[0]] = alignment[1]
            print(self.table)


class FileResult(Result):
    header: list = ["Path", "Source Size", "Destination Size", "Status"]
    data: list = list()
    table: PrettyTable = PrettyTable()
    title: str = "File Backup Status"
    alignments: list = [('Path', 'l'), ('Source Size', 'r'), ('Destination Size', 'r')]


class DatabaseResult(Result):
    header: list = ["Type", "Container", "Database", "Size", "Status"]
    data: list = list()
    table: PrettyTable = PrettyTable()
    title: str = "Database Backup Status"
    alignments: list = [('Type', 'l'), ('Container', 'l'), ('Database', 'l'), ('Size', 'r')]


def secure(content):
    """
    :param content which should be secured
    :return: content without password
    """
    return re.compile(r"--password=.*? ").sub(r"--password=REDACTED ", content)


def remove_timestamp(content):
    """
    :param content which the timestamp should be removed from (mostly mongodb error messages)
    :return: content without timestamp
    """
    return content.split("\t")[1]


# convert bytes to next unit
def convert_size(num):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'):
        if abs(num) < 1000.0:
            # return "%3.2f %s" % (num, unit)
            return '{:3.2f} {}'.format(num, unit)
        num /= 1000.0
    # return "%.2f YiB" % (num)
    return '{:3.2f} YiB'.format(num)


# convert seconds to next unit
def convert_time(seconds):
    # humanfriendly.format_timespan(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ret = 'elapsed time: '

    if days:
        ret += f'{days} days' if days > 1 else '1 day'
        if hours:
            ret += f', {hours} hours' if hours > 1 else ', 1 hour'
            if minutes:
                ret += f', {minutes} minutes' if minutes > 1 else ', 1 minute'
                if seconds:
                    ret += f' and {seconds} seconds' if seconds > 1 else ' and 1 second'
    elif hours:
        ret += f'{hours} hours' if hours > 1 else '1 hour'
        if minutes:
            ret += f', {minutes} minutes' if minutes > 1 else ', 1 minute'
            if seconds:
                ret += f' and {seconds} seconds' if seconds > 1 else ' and 1 second'
    elif minutes:
        ret += f'{minutes} minutes' if minutes > 1 else '1 minute'
        if seconds:
            ret += f' and {seconds} seconds' if seconds > 1 else ' and 1 second'
    else:
        ret += f'{seconds} seconds' if seconds > 1 else '1 second'

    return ret


# size of a specific path including all subdirectories
def sizeof(start):
    if os.path.isfile(start):
        return convert_size(os.path.getsize(start))
    size = 0
    for path, folder, files in os.walk(start):
        for file in files:
            file = os.path.join(path, file)
            if not os.path.islink(file):
                size += os.path.getsize(file)
    return convert_size(size) if size else 'empty'
