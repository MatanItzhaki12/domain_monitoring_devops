import json
import re
from pathlib import Path
from . import logger
from . import DomainManagementEngine as DME

logger = logger.setup_logger("backend.UserManagementModule")
USERS_CRED_PATH = "./UsersData/users.json"
DATA_PATH = "./UsersData/"

class UserManager:
    """
    This class handles everything in relation to users.
    """
    def __init__(self):
        logger.info(f"Initializing UserManagement module.")
        self.users = self._load_json_to_dict()

    def load_users_json_to_memory(self):
        logger.info(f"Reloading users.json file.")
        self.users = self._load_json_to_dict()

    def _load_json_to_dict(self):
        logger.debug(f"Loading users.json file.")
        try:
            users = {}
            with open(USERS_CRED_PATH, "r") as f:
                users_json = json.load(f)
            for user_details in users_json:
                username = user_details["username"]
                password = user_details["password"]
                users[username] = password
            logger.debug(f"users.json file loaded successfully.")
            return users
        except Exception as e:
            logger.error(f"users.json could not be loaded! {str(e)}")
            return {}

    def register_page_add_user(self, username, password, password_confirmation, dme: DME.DomainManagementEngine):
        logger.info(f"Proccessing new user's details.")
        try:
            logger.debug(f"Checking username validity.")
            usr_valid = self.username_validity(username)
            if usr_valid == "FAILED" or not usr_valid[0]:
                logger.debug(f"The \"{username}\" is an invalid username.")
                return {"error" : usr_valid[1]}
            logger.debug(f"Checking password validity.")
            password_validity = self.register_page_password_validity(password, password_confirmation)
            if password_validity[0] == "FAILED" or not password_validity[0]:
                logger.debug(f"Password invalid.")
                return {"error": password_validity[1]}
            logger.debug(f"Adding user to database.")
            self.users[username] = password
            write_user_status = self.write_user_to_json (username, password)
            if write_user_status[0] == "FAILED":
                logger.debug(f"Writing user to json failed.")
                return {"error": write_user_status[1]}
            logger.debug(f"creating {DATA_PATH}{username}_domains.json file.")
            dme.load_user_domains(username)
            logger.info(f"{username} registered successfully.")
            return {"message" : "Registered Successfully."}
        except Exception as e:
            logger.error(f"Unable to register user; Exception: {str(e)}")
            return {"error": "Unable to register user."}

    def register_page_password_validity(self, password, password_confirmation):
        logger.info(f"Checking the validity of the password.")
        try:
            if password != password_confirmation:
                return False, "Password and Password Confirmation are not the same."
            password_str = f"{password}"
            if len(password_str) < 8 or len(password_str) > 12:
                return False, "Password is not between 8 to 12 characters."
            if not re.search("[A-Z]", password_str):
                return False, "Password does not include at least one uppercase character."
            if not re.search("[a-z]", password_str):
                return False, "Password does not include at least one lowercase character."
            if not re.search("[0-9]", password_str):
                return False, "Password does not include at least one digit."
            if not password_str.isalnum():
                return False, "Password should include only uppercase characters, lowercase characters and digits!"
            return True, "SUCCESS"
        except Exception as e:
            logger.error(f"Unable to validate user's password; Exception: {str(e)}")
            return "FAILED", "Error: Unable to validate password.", e

    def username_validity(self, username):
        logger.info(f"Checking the validity of the username.")
        try:
            if username == "":
                return False,  "Username invalid."
            if f"{username}" in self.users:
                return False, "Username already taken."
            return True, "Username is valid."
        except Exception as e:
            logger.debug(f"Unable to check the validity of the password; Exception: {str(e)}")
            return "FAILED","Error: Unable to validate username.", e
    
    def save_users_from_memory_to_json(self):
        logger.info(f"writing users from memory to users.json file.")
        try:
            users_list = []
            for user in self.users:
                user_temp = {
                    "username": user,
                    "password": self.users[user]
                }
                users_list.append(user_temp)
            with open(USERS_CRED_PATH, "w") as f:
                json.dump(users_list, f, indent=4, ensure_ascii=False)
            return "SUCCESS", "Users was written from memory to users.json file successfully."
        except Exception as e:
            logger.error(f"Failed to write self.users from memory to users.json; Exception: {str(e)}")
            return "FAILED", "Unabled to write self.users to users.json.", e
    
    def write_user_to_json(self, username, password):
        logger.info(f"Writing user's details to users.json.")
        try:
            with open(USERS_CRED_PATH, "r") as f:
                users_list = json.load(f)
            user_to_write = {
                "username" : f"{username}", 
                "password" : f"{password}"
            }
            users_list.append(user_to_write)
            with open(USERS_CRED_PATH, "w") as f:
               json.dump(users_list, f, indent=4, ensure_ascii=False)
            return "SUCCESS", "Username and password was written successfully."
        except Exception as e:
            logger.error(f"Failed to write user's details to users.json; Exception: {str(e)}")
            return "FAILED", "Error: Unable to write user to file.", e 
    
    def validate_login(self, username, password):
        try:
            if username in self.users and self.users[username] == password:
                logger.info(f"Login successful: username={username}")
                return True
            logger.warning(f"Login failed: username={username}")
            return False
        except Exception as e:
            logger.error(f"Could not validate users credentials. {str(e)}")
            return False
    
    def remove_user(self, username):
        logger.info(f"deleting {username}'s details from users.json, and deletes its domains file if exists.")
        try:
            if username in self.users:
                password = self.users[username]
                del self.users[username]
                result = self.save_users_from_memory_to_json()
                if result[0] == "FAILED":
                    self.users[username] = password
                    logger.error(f"Unable to remove user {username} from json file.")
            Path(f"{DATA_PATH}{username}_domains.json").unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error deleting {username} and files from system: {str(e)}")
