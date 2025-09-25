import json
import re
import logger

logger = logger.setup_logger("app")

class UserManager:
    def __init__(self):
        logger.debug(f"Initializing UserManagement module.")
        self.users = self.load_json_to_dict()

    def load_json_to_dict(self):
        logger.debug(f"Loading users.json file.")
        try:
            users = {}
            with open("./userdata/users.json", "r") as f:
                users_json = json.load(f)
            for user_details in users_json:
                username = user_details["username"]
                password = user_details["password"]
                users[username] = password
            logger.debug(f"users.json file loaded successfully.")
            return users
        except Exception as e:
            logger.error(f"users.json could not be loaded! {e}")
            return {}

    def register_page_add_user(self, username, password, password_confirmation):
        logger.debug(f"Proccessing new user's details.")
        try:
            logger.debug(f"Checking username validity.")
            usr_valid = self.username_validity(self.users, username)
            if usr_valid == "FAILED" or not usr_valid[0]:
                logger.debug(f"username invalid.")
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
            
            logger.debug(f"creating ./UserData/{username}_domains.json file.")
            with open(f"./UsersData/{username}_domains.json", "w") as f:
                json.dump({}, f, indent=4)
            
            logger.debug(f"{username} registered successfully.")
            return {"message" : "Registered Successfully"}
        
        except Exception as e:
            logger.error(f"Unable to register user.")
            return {"error": "Unable to register user.", 'exception': e}

    def register_page_password_validity(self, password, password_confirmation):
        logger.debug(f"Checking the validity of the password.")
        try:
            if password != password_confirmation:
                return False, "Password and Password Confirmation are not the same."
            password_str = f"{password}"
            if len(password_str) < 8 or len(password_str) > 12:
                return False, "Password is not between 8 to 12 characters."
            if not re.fullmatch("[A-Z]+", password_str):
                return False, "Password does not include at least one uppercase character."
            if not re.fullmatch("[a-z]+", password_str):
                return False, "Password does not include at least one lowercase character."
            if not re.fullmatch("[0-9]+", password_str):
                return False, "Password does not include at least one digit."
            if not password_str.isalnum():
                return False, "Password should include only uppercase \
                    characters, lowercase characters and digits!"
            return True, "SUCCESS"
        except Exception as e:
            logger.error(f"Unable to validate user's password.")
            return "FAILED", "Error: Unable to validate password.", e

    def username_validity(self, username):
        logger.debug(f"Checking the validity of the username.")
        try:
            if username == "":
                return False,  "Username invalid."
            if f"{username}" in self.users:
                return False, "Username already taken."
            return True, "Username is valid."
        except Exception as e:
            logger.debug(f"Unable to check the validity of the password.")
            return "FAILED","Error: Unable to validate username.", e 
    
    def write_user_to_json(self, username, password):
        logger.debug(f"Writing user's details to users.json.")
        try:
            with open("./userData/users.json", "r") as f:
                users_list = json.load(f)
            
            user_to_write = {
                "username" : f"{username}", 
                "password" : f"{password}"
            }

            users_list.append(user_to_write)
            with open("./userData/users.json", "w") as f:
               json.dump(users_list, f, indent=4, ensure_ascii=False)

            return "SUCCESS", "Username and password was written successfully."
        
        except Exception as e:
            logger.error(f"Failed to write user's details to users.json.")
            return "FAILED", "Error: Unable to write user to file.", e 

    def validate_login(self, username, password):
        try:
            if username in self.users and self.users[username] == password:
                logger.info(f"Login successful: username={username}")
                return True
            logger.warning(f"Login failed: username={username}")
            return False
        except Exception as e:
            logger.error(f"Could not validate users credentials. {e}")
            return False
