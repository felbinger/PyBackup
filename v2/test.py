from docker import from_env as docker_env
from mariadb import MariaDB
from mongodb import MongoDB
from postgresql import PostgreSQL
from files import File
from checksums import Checksums

from utils import Printer, DatabaseResult, FileResult

Printer.verbose = True

"""
# Docker Databases
mariadb = MariaDB(
    username="root", password="root", path='/home/user/Downloads', databases=['mysql', 'spring'],
    container=list(filter(lambda c: c.name == "user_mariadb_1", docker_env().containers.list()))[0]
)
mariadb.backup()

mariadb_insecure = MariaDB(
    path='/home/user/Downloads', databases=["mysql", "teamspeak", "nextcloud"],
    container=list(filter(lambda c: c.name == "user_mariadb_insecure_1", docker_env().containers.list()))[0]
)
mariadb_insecure.backup()

mongodb = MongoDB(
    username="root", password="root", path='/home/user/Downloads', databases=['admin'],
    container=list(filter(lambda c: c.name == "user_mongodb_1", docker_env().containers.list()))[0]
)
mongodb.backup()

mongodb_insecure = MongoDB(
    path='/home/user/Downloads', databases=['admin'],
    container=list(filter(lambda c: c.name == "user_mongodb_insecure_1", docker_env().containers.list()))[0]
)
mongodb_insecure.backup()

# Due to postgres trust system, password is not required on localhost.
# The username (in this setup only postgres) on the other hand have to be existing.
postgres = PostgreSQL(
    path='/home/user/Downloads', databases=['postgres', 'teamspeak', 'nextcloud'],
    container=list(filter(lambda c: c.name == "user_postgres_1", docker_env().containers.list()))[0]
)
postgres.backup()

# Local Databases
mariadb = MariaDB(username="root", password="root", path='/home/user/Downloads', databases=['mysql', 'spring'])
mariadb.backup()

mongodb = MongoDB(path='/home/user/Downloads', databases=['admin'])
mongodb.backup()

postgres = PostgreSQL(path='/home/user/Downloads', databases=['postgres', 'teamspeak', 'nextcloud'])
postgres.backup()

# File Backups
File(src='/home/user/Pictures/blackscreen.jpg', path='/home/user/Downloads/').backup()
File(src='/home/user/Music', path='/home/user/Downloads/').backup()

# Generate Checksums
checksums = Checksums(path='/home/user/Downloads/')
checksums.generate_all()

# Reporting
dr = DatabaseResult()
dr.sortby = 'Container'
dr.print()
fr = FileResult()
fr.print()
"""

# TODO
# write config validator
