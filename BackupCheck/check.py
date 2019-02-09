#!/usr/bin/python3.6

import json
import os
from sys import exit
from datetime import date, time, datetime, timedelta

BACKUP_CONFIG = "/home/admin/tools/.config.json"

# The cronjob will start the backup at 3 o'clock (am). The average backup duration is 20 minutes.
# Start the check at 3:20 am
START_CHECK = (3, 20)


def get_backup_path(path):
    if not path.endswith('/'):
        path += "/"

    # get the current date
    current_date = date.today()

    # check if the script has been executed before the backup job has
    # been started / before it can be completed (defined as START_CHECK)
    if datetime.now().time() < time(*START_CHECK):
        # check the backup of yesterday
        current_date -= timedelta(1)

    path += str(current_date)
    return path


def main():
    config = json.loads(open(BACKUP_CONFIG, 'r').read())

    backup_location = get_backup_path(config.get("backup_dir"))

    if os.path.isdir(backup_location):
        files = [file for file in os.listdir(backup_location) if os.path.isfile(os.path.join(backup_location, file))]

        for database in config.get("database").get("list"):
            if f'{database}.sql' not in files:
                print(f"Missing backup of {database}")
                exit(1)

        for path in config.get("files").get("paths"):
            if path.endswith('/'):
                path = path[:-1]
            path = os.path.basename(path)
            if f'{os.path.basename(path)}.tar.gz' not in files:
                print(f"Missing backup of {path}")
                exit(1)

        if config.get("files").get("paths"):
            for sum in config.get("files").get("checksums"):
                if f'{sum}sum.txt' not in files:
                    print(f"Warning: Missing {sum} check sums for the file backup!")
                    exit(1)

        print('Ok!')
        exit(0)
    else:
        print('Backup not found!')
        exit(1)


if __name__ == '__main__':
    main()
