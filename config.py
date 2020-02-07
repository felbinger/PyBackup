class Config:
    backup_dir: str = ""
    database_conatainer_name: str = ""
    database_list: list = []
    database_username: str = ""
    database_password: str = ""
    gitlab_container_name: str = ""
    file_path_list: list = []
    checksums: list = []

    def __init__(self, json: dict):
        self.backup_dir = json.get("backup_dir")
        database_values: dict = json.get("database")
        if not database_values:
            print("Error: Database values are not properly initialized! Exiting.")
            exit(1)
        self.database_conatainer_name = database_values.get("onatainer_name")
        self.database_password = database_values.get("password")
        self.database_username = database_values.get("username")
        self.database_list = database_values.get("list")
        self.gitlab_container_name = json.get("gitlab").get("container_name")
        self.file_path_list = json.get("files").get("paths")
        self.checksums = json.get("files").get("checksums")

    def verify_settings(self):
        if self.backup_dir in [None, ""]:
            print(f"Warning: Path to local backup folder is not properly initialized! Using default value: "
                  f"\"/var/backups/system/\"")
            self.backup_dir = '/var/backups/system/'
        if self.database_conatainer_name in [None, ""]:
            print("Warning: Name of database container is not properly initialized! Using default value: "
                  "\"root_db_1\"")
            self.database_conatainer_name = "root_db_1"
        if self.database_username in [None, ""]:
            print("Warning: Database username is not properly initialized! Using default: \"backup\"")
            self.database_username = "backup"
        if self.database_password in [None, ""]:
            print("Warning: Database password is not properly initialized! Using default: \"default_password\"")
            self.database_password = "default_password"
        if self.database_list in [None, ""]:
            print("Warning: Database list is not properly initialized! Using default: only \"mysql\"")
            self.database_list = ['mysql']
        if self.file_path_list in [None, ""]:
            print("Warning: List of file paths is not properly initialized!")
            self.file_path_list = list()
        if self.checksums in [None, ""]:
            print("Warning: List of checksums is not properly initialized!")
            self.checksums = list()
        if self.gitlab_container_name in [None, ""]:
            print("Warning: Name of gitlab container is not properly initialized! Using default value: "
                  "\"'root_gitlab_1'\"")
            self.gitlab_container_name = "'root_gitlab_1'"


def create_from_json(json: dict) -> Config:
    return Config(json)
