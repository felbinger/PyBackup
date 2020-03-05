class Config:
    local_location: str = ""
    server_location: str = ""
    ssh_hostname: str = ""
    ssh_port: int = 0
    ssh_username: str = ""
    ssh_key_file: str = ""
    ssh_passphrase: str = ""

    def __init__(self, json: dict):
        self.local_location = json.get("local_location")
        self.server_location = json.get("server_location")
        ssh_values: dict = json.get("server")
        if not isinstance(ssh_values, dict):
            print("Error: SSH values are not properly initialized! Exiting.")
            exit(1)
        self.ssh_hostname = ssh_values.get("hostname") or None
        self.ssh_port = ssh_values.get("port") or None
        self.ssh_username = ssh_values.get("username") or None
        self.ssh_key_file = ssh_values.get("keyfile") or None
        self.ssh_passphrase = ssh_values.get("passphrase") or None

    def verify_settings(self):
        if not self.ssh_hostname:
            print("Error: SSH host is not properly initialized! Exiting...")
            exit(2)
        if not self.local_location:
            print(f"Warning: Path to local backup folder is not properly initialized! Using default value: "
                  f'"/var/backups/{self.ssh_hostname}"')
            self.local_location = f'/var/backups/{self.ssh_hostname}'
        if not self.server_location:
            print("Warning: Path to remote backup folder is not properly initialized! Using default value: "
                  '"/var/backups/"')
            self.server_location = "/var/backups/"
        if not self.ssh_username:
            print('Warning: SSH username is not properly initialized! Using default value: "backup"')
            self.ssh_username = "backup"
        if not self.ssh_port:
            print('Warning: SSH port is not properly initialized! Using default value: 22')
            self.ssh_port = 22
        try:
            self.ssh_port = int(self.ssh_port)
        except ValueError:
            print("Error: Unable to convert ssh port to int! Exiting.")
            exit(1)
        if not self.ssh_key_file:
            print('Warning: SSH Keyfile is not properly initialized! Trying password authentication...')
            # TODO implement password auth.
            print("not implemented!")
            exit(1)


def create_from_json(json: dict) -> Config:
    return Config(json)
