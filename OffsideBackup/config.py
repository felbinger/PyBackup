class Config:
    local_location: str = ""
    server_location: str = ""
    ssh_hostname: str = ""
    ssh_port: int = 0
    ssh_username: str = ""
    ssh_keyfile: str = ""
    ssh_passphrase: str = ""
    time_hour: int = 0
    time_minute: int = 0

    def __init__(self, json: dict):
        self.local_location = json.get("local_location")
        self.server_location = json.get("server_location")
        ssh_values: dict = json.get("server")
        if not ssh_values:
            print("Error: SSH values are not properly initialized! Exiting.")
            exit(1)
        self.ssh_hostname = ssh_values.get("hostname")
        self.ssh_port = ssh_values.get("port")
        self.ssh_username = ssh_values.get("username")
        self.ssh_keyfile = ssh_values.get("keyfile")
        self.ssh_passphrase = ssh_values.get("passphrase")
        time_values: dict = json.get("time")
        if not time_values:
            print("Warning: Time values are not properly initialized! Using default value: 00:00")
            self.time_hour = 0
            self.time_minute = 0
        else:
            self.time_hour = time_values.get("hour")
            self.time_minute = time_values.get("minute")

    def verify_settings(self):
        if None in [self.ssh_hostname, self.ssh_keyfile, self.ssh_port, self.ssh_passphrase]:
            print("Error: SSH values are not properly initialized! Exiting.")
            exit(2)
        if self.local_location is None:
            print(f"Warning: Path to local backup folder is not properly initialized! Using default value: "
                  f"\"/var/backups/{self.ssh_hostname}\"")
            self.server_location = self.ssh_hostname
        if self.server_location is None:
            print("Warning: Path to remote backup folder is not properly initialized! Using default value: "
                  "\"/var/backups/\"")
            self.server_location = "/var/backups/"
        if self.ssh_username is None:
            print("Warning: SSH username is not properly initialized! Using default: \"backup\"")
            self.ssh_username = "backup"
        if self.ssh_port is None:
            print("Warning: SSH port is not properly initialized! Using default: \"22\"")
            self.ssh_port = 22
        try:
            self.ssh_port = int(self.ssh_port)
        except ValueError:
            print("Error: Unable to convert ssh port to int! Exiting.")
            exit(1)
        try:
            self.time_hour = int(self.time_hour)
        except ValueError:
            print("Error: Unable to convert minute part of time to int! Exiting.")
            exit(1)
        try:
            self.time_minute = int(self.time_minute)
        except ValueError:
            print("Error: Unable to convert hour part of time to int! Exiting.")
            exit(1)

def create_from_json(json: dict) -> Config:
    return Config(json)
