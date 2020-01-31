# PyBackup

PyBackup is a backup script for docker environments.
The script support's:
* simple file backups
* docker mysql database backups 
* gitlab repository backups.


### Arguments
You can execute the script `backup.py` with the following arguments:

|    Argument    |                  Description                  | Default      |
|:--------------:|:---------------------------------------------:|--------------|
| -v, --verbose  | Enable verbose output                         | False        |
| -c, --config   | Set config file                               | .config.json |
| -a, --all      | Create all possible backups                   | False        |
| -d, --database | Create a backup of the MySQL/MariaDB database | False        |
| -f, --files    | Create a file backup of the configured paths  | False        |
| --gitlab       | Create a backup of the GitLab repositories    | False        |
|                |                                               |              ||

### Configuration
The configuration file (by default it's `.config.json` does contain the following parameters:

| Parameter               | Description                                                   | Default              |
|-------------------------|---------------------------------------------------------------|----------------------|
| backup_dir              | Location where backups get stored.                            | /var/backups/system/ |
| database/container_name | Container name of the MySQL/MariaDB container                 | root_db_1            |
| database/username       | Username for backup mysql user                                | backup               |
| database/password       | Password for backup mysql user                                | default_password     |
| database/list           | Databases that should get backed up                           | [mysql]              |
| gitlab/container_name   | Container name of the GitLab container                        | root_gitlab_1        |
| files/paths             | Paths that should be backed up                                |                      |
| files/checksums         | Checksums that should be created for the file backup archives |                      ||

Example:
```
{
    "backup_dir": "",
    "database": {
        "container_name": "",
        "username": "",
        "password": "",
        "list": [
        ]
    },
    "gitlab": {
        "container_name": ""
    },
    "files": {
        "paths": [
        ],
        "checksums": [
          "md5",
          "sha1",
          "sha224",
          "sha256",
          "sha384",
          "sha512"
        ]
    }
}
```

#### Checksums
You can use the following values in the checksums list, other options will be ignored:
* md5
* sha1
* sha224
* sha256
* sha384
* sha512


## Backup Check
The file check.py contains a simple check if the backup was successful. You can use it for example in [monit](https://mmonit.com/monit/).
Just add the following lines to you config (`/etc/monit/monitrc`):
```
check program backup with path check.py
  if status != 0 then alert
```

## Offside Backup
The last feature can be found in the directory `OffsideBackup`. 
It's a simple script which will connect to the server and download the latest version 
of the Backup using the secure file transfer protocol.
The script currently offers the two most used authentication methods (password, private key (with and without passphrase)).

### Arguments
|    Argument    |                  Description                  | Default      |
|:--------------:|:---------------------------------------------:|--------------|
| -v, --verbose  | Enable verbose output                         | False        |
| -c, --config   | Set config file                               | .config.json ||

### Configuration
The configuration file (by default it's `.config.json` does contain the following parameters:

| Parameter               | Description                                                   | Default                 |
|-------------------------|---------------------------------------------------------------|-------------------------|
| local_location          | Location where local copy of the backup should be stored.     | /var/backups/{hostname} |
| server_location         | Location of the backup on the server                          | /var/backups/           |
| server/hostname         | Hostname/IP address of the server                             |                         |
| server/username         | Username for the User Account to copy the backup using scp.   | backup                  |
| server/keyfile          | Private SSH key that should be used to authenticate           |                         |
| server/passphrase       | Password for the private key                                  |                         |
| server/password         | if you want to authenticate without ssh keys, add the password|                         ||

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

## TODO / Roadmap
* OffsideBackup: check how to store the passphrase for the private key in the config file - so that the user doesn't need to type it all the time.
* OffsideBackup: check and fix DeprecationWarnings.
  * CryptographyDeprecationWarning: Support for unsafe construction of public numbers from encoded data will be removed in a future version. 
    Please use EllipticCurvePublicKey.from_encoded_point
  self.curve, Q_S_bytes
  * CryptographyDeprecationWarning: encode_point has been deprecated on EllipticCurvePublicNumbers and will be removed in a future version. 
    Please use EllipticCurvePublicKey.public_bytes to obtain both compressed and uncompressed point encoding.
