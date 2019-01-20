# PyBackup

PyBackup is a backup script for docker environments

### Arguments
|    Argument    |                  Description                  | Default      |
|:--------------:|:---------------------------------------------:|--------------|
| -v, --verbose  | Enable verbose output                         | False        |
| -c, --config   | Set config file                               | .config.json |
| -a, --all      | Create all possible backups                   | False        |
| -d, --database | Create a backup of the MySQL/MariaDB database | False        |
| -f, --files    | Create a file backup of the configured paths  | False        |
| --gitlab       | Create a backup of the GitLab repositories    | False        |
|                |                                               |              |

### Configuration

| Parameter               | Description                                                   | Default              |
|-------------------------|---------------------------------------------------------------|----------------------|
| backup_dir              | Location where backups get stored.                            | /var/backups/system/ |
| database/container_name | Container name of the MySQL/MariaDB container                 | root_db_1            |
| database/username       | Username for backup mysql user                                | backup               |
| database/password       | Password for backup mysql user                                | default_password     |
| database/list           | Databases that should get backed up                           | [mysql]              |
| gitlab/container_name   | Container name of the GitLab container                        | root_gitlab_1        |
| files/paths             | Paths that should be backed up                                |                      |
| files/checksums         | Checksums that should be created for the file backup archives |                      |

#### Checksums
* md5
* sha1
* sha224
* sha256
* sha384
* sha512
