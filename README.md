# PyBackup

PyBackup is a backup script for docker environments. The latest version with a few more features **requires Python 3.8**!
The script support's:
* simple file backups
* mariadb/mysql, mongodb and postgres database backups
* gitlab repository backups.


### Arguments
You can execute the script `backup.py` with the following arguments:

|    Argument    |                  Description                  | Default      |
|----------------|-----------------------------------------------|--------------|
| -v, --verbose  | Enable verbose output                         | False        |
| -q, --quiet    | Enable quiet mode                             | False        |
| -c, --config   | Set config file                               | .config.json |
| -a, --all      | Create all possible backups                   | False        |
| -d, --database | Create a backup of the MySQL/MariaDB database | False        |
| -f, --files    | Create a file backup of the configured paths  | False        |
| --gitlab       | Create a backup of the GitLab repositories    | False        |
|                |                                               |              ||

### Configuration
The configuration file (by default it's `.config.json` does contain the following:
```json5
{
    // directory where the backup should get stored
    "backup_dir": "",
    // MariaDB / MySQL database backup configuration
    "mariadb": [
        {
            "container_name": "",
            "host": "",
            "port":"",
            "username": "",
            "password": "",
            "databases": [
            ],
            "skip_existing": true                 // skip backups if they already exist
        }
    ],
    // MongoDB database backup configuration
    "mongodb": [
        {
            "container_name": "",
            "host": "",
            "port":"",
            "username": "",
            "password": "",
            "authentication_database": "",        // default is admin, should work if you haven't changed to much.
            "authentication_mechanism": "",       // default is SCRAM-SHA-1, should also work
            "databases": [
            ],
            "skip_existing": true                 // skip backups if they already exist
        }
    ],
    // PostgreSQL database backup configuration
    "postgres": [
        {
            "container_name": "",
            "host": "",
            "port":"",
            "username": "",
            "password": "",
            "databases": [
            ],
            "skip_existing": true                 // skip backups if they already exist
        }
    ],
    // GitLab repository backups
    "gitlab": {
        "container_name": ""
    },
    // simple file backups
    "files": {
        "paths": [
        ]
    },
    // checksum files that should be created
    "checksums": [
        "md5",
        "sha1",
        "sha224",
        "sha256",
        "sha384",
        "sha512"
    ]
}
```

## Offside Backup
The last feature can be found in the directory `OffsideBackup`. 
It's a simple script which will connect to the server and download the latest version 
of the Backup using the secure file transfer protocol.
The script currently offers the two most used authentication methods (password, private key (with and without passphrase)).

### Arguments
|    Argument    |                  Description                  | Default      |
|:--------------:|:---------------------------------------------:|--------------|
| -q, --quiet    | Disable verbose output / quiet mode           | False        |
| -c, --config   | Set config file                               | .config.json ||

### Configuration
The configuration file (by default it's `.config.json` does contain the following parameters:

| Parameter               | Description                                                   | Default                 |
|-------------------------|---------------------------------------------------------------|-------------------------|
| local_location          | Location where local copy of the backup should be stored.     | /var/backups/{hostname} |
| server_location         | Location of the backup on the server                          | /var/backups/           |
| server/hostname         | Hostname/IP address of the server                             |                         |
| server/username         | Port of the ssh server.                                       | 22                      |
| server/username         | Username for the User Account to copy the backup using scp.   | backup                  |
| server/keyfile          | Private SSH key that should be used to authenticate           |                         |
| server/passphrase       | Password for the private key                                  |                         |
| server/password         | Fallback option, if you want to authenticate without ssh keys |                         ||

You can eighter use the Keyfile (and if the keyfile is secured using a passphrase) to authenticate, or the password for the user account. Make sure that the keyfile is added to the authorized hosts or that PasswordAuthentication is still enabled on your ssh server. 

Example:
```
{
    "local_location": "",
    "server_location": "",
    "server": {
        "hostname": "",
        "port": "",
        "username": "",
        "keyfile": "",
        "passphrase": "",
        "password": ""
    }
}
```

## TODO
* write config validator