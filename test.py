from docker import from_env as docker_env
from helper import Printer, DatabaseResult, FileResult, MariaDB, MongoDB, PostgreSQL, File, Checksums

Printer.verbose = True


# Docker Databases
MariaDB(
    username="root", password="root", path='/home/user/Downloads', databases=['mysql', 'spring'],
    container=list(filter(lambda c: c.name == "user_mariadb_1", docker_env().containers.list()))[0]
).backup()

MariaDB(
    path='/home/user/Downloads', databases=["mysql", "teamspeak", "nextcloud"],
    container=list(filter(lambda c: c.name == "user_mariadb_insecure_1", docker_env().containers.list()))[0]
).backup()

MongoDB(
    username="root", password="root", path='/home/user/Downloads', databases=['admin'],
    container=list(filter(lambda c: c.name == "user_mongodb_1", docker_env().containers.list()))[0]
).backup()

MongoDB(
    path='/home/user/Downloads', databases=['admin'],
    container=list(filter(lambda c: c.name == "user_mongodb_insecure_1", docker_env().containers.list()))[0]
).backup()

# Due to postgres trust system, password is not required on localhost.
# The username (in this setup only postgres) on the other hand have to be existing.
PostgreSQL(
    path='/home/user/Downloads', databases=['postgres', 'teamspeak', 'nextcloud'],
    container=list(filter(lambda c: c.name == "user_postgres_1", docker_env().containers.list()))[0]
).backup()

# Local Databases
MariaDB(username="root", password="root", path='/home/user/Downloads', databases=['mysql', 'spring']).backup()
MongoDB(path='/home/user/Downloads', databases=['admin']).backup()
PostgreSQL(path='/home/user/Downloads', databases=['postgres', 'teamspeak', 'nextcloud']).backup()

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
