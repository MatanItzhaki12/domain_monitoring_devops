import re
import logger as log
import DomainManagementEngine as DME
import psycopg2
import IP_Library
logger = log.setup_logger("UserManagementModule")
DB_PARAMS = {
    'dbname': IP_Library.DATABASE_NAME,
    'user': IP_Library.DATABASE_USER,
    'password': IP_Library.DATABASE_PASSWORD,
    'host': IP_Library.DATABASE_IP,
    'port': IP_Library.DATABASE_PORT
}

def connect_db():
    return psycopg2.connect(**DB_PARAMS)

class UserManager:
    """
    This class handles everything in relation to users.
    """
    def __init__(self):
        pass

# OZ
    def register_page_add_user(self, username, password, password_confirmation, dme: DME.DomainManagementEngine):
        """
        registering user to the system, after checking the validity of the credentials.
        """
        logger.info("Processing new user's details.")
        try:
            # username validity 
            logger.debug("Checking username validity.")
            usr_valid = self.username_validity(username)
            if usr_valid[0] == "FAILED" or not usr_valid[0]:
                logger.debug(f'The "{username}" is an invalid username.')
                return {"error": usr_valid[1]}

            # password validity
            logger.debug("Checking password validity.")
            password_validity = self.register_page_password_validity(password, password_confirmation)
            if password_validity[0] == "FAILED" or not password_validity[0]:
                logger.debug("Password invalid.")
                return {"error": password_validity[1]}

            # Write user to DB (use Matan's function as a method)
            logger.debug("Adding user to database.")
            write_status = self.write_user_to_DB(username, password)
            if write_status[0] == "FAILED":
                return {"error": write_status[1]}

            # 4) Load/create user domains file/structure
            dme.load_user_domains(username)

            logger.info(f"{username} registered successfully.")
            return {"message": "Registered Successfully."}

        except Exception as e:
            logger.error(f"Unable to register user; Exception: {str(e)}")
            return {"error": "Unable to register user."}

# OZ
    def register_page_password_validity(self, password, password_confirmation):
        """
        This method checks the validity of the password.
        The password needs to be between 8 to 12 characters.
        It should also contain uppercase and lowercase characters and digits.
        It should also match the password_confirmation.
        This method should return True if the password valid and False otherwise, with
        an matching message for the user.
        """
        logger.info("Checking password validity.")
        try:
            if password is None or password_confirmation is None:
                return False, "Password invalid."

            password = str(password)
            password_confirmation = str(password_confirmation)

            if password != password_confirmation:
                return False, "Passwords do not match."

            if not (8 <= len(password) <= 12):
                return False, "Password must be between 8 and 12 characters."

            if not re.search(r"[A-Z]", password):
                return False, "Password must contain at least one uppercase letter."

            if not re.search(r"[a-z]", password):
                return False, "Password must contain at least one lowercase letter."

            if not re.search(r"\d", password):
                return False, "Password must contain at least one digit."

            return True, "SUCCESS"

        except Exception as e:
            logger.error(f"Unable to validate password; Exception: {str(e)}")
            return "FAILED", "Error: Unable to validate password.", e
# OZ
    def username_validity(self, username):
        """
        # This method checks username validity, mainly it checks if the 
        username is not empty and not already exist.
        
        # add select from where querry to check if user is not exist
        """
        logger.info("Checking the validity of the username.")
        try:
            if username is None or str(username).strip() == "":
                return False, "Username invalid."

            username = str(username).strip()

            with connect_db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM users WHERE username = %s LIMIT 1", (username,))
                    exists = cursor.fetchone()

            if exists:
                return False, "Username already exists."

            return True, "Username is valid."

        except (Exception, psycopg2.Error) as e:
            logger.error(f"Unable to validate username; Exception: {str(e)}")
            return "FAILED", "Error: Unable to validate username.", e

# MATAN
    def write_user_to_DB(self, username, password):
        """
        This method writes the username and password to the PostgreSQL database.
        """
        # FIX: Updated log message
        logger.info(f"Writing user's details to database.") 
        
        try:
            # Ensure DB_PARAMS is accessible here (either global or self.DB_PARAMS)
            with connect_db() as connection:
                with connection.cursor() as cursor:
                    insert_query = """ 
                    INSERT INTO users (username, password, created_at) 
                    VALUES (%s, %s, NOW())
                    """
                    cursor.execute(insert_query, (username, password))
                    
            # FIX: Matched the old string exactly if you want 100% compatibility
            return "SUCCESS", "Username and password was written successfully."

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Failed to write user's details to database; Exception: {str(error)}")
            
            # FIX: Structure matches old return (Status, Message, ErrorObj)
            return "FAILED", "Error: Unable to write user to database.", error
# MATAN
    def validate_login(self, username, password):
        """
        This method validates the username and password for login by checking 
        if the username and password pair exists in the PostgreSQL database.
        """
        try:
            # Connect to the database
            with connect_db() as connection:
                with connection.cursor() as cursor:
                    
                    # SQL Query: Look for a row where BOTH username and password match.
                    # We select '1' because we don't need the actual data, just to know it exists.
                    query = "SELECT 1 FROM users WHERE username = %s AND password = %s"
                    
                    # Execute query and check if at least one matching record exists
                    cursor.execute(query, (username, password))
                    return cursor.fetchone() is not None

        except (Exception, psycopg2.Error) as e:
            logger.error(f"Could not validate users credentials. {str(e)}")
            return False
# MATAN
    def remove_user(self, username):
        """
        Removes a user from the PostgreSQL database.
        
        Logic:
        1. Find user_id by username.
        2. Identify domains linked to this user.
        3. Delete the link in 'aux_users_domains'.
        4. Check if those domains are used by anyone else.
        5. If not used by anyone else, delete the domain from 'domains'.
        6. Delete the user from 'users'.
        """
        # Updated log message for DB context
        logger.info(f"Deleting {username} and associated orphaned data from database.")

        try:
            with connect_db() as connection:
                with connection.cursor() as cursor:
                    
                    # --- STEP 1: Find user id ---
                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    user_row = cursor.fetchone()
                    
                    if not user_row:
                        # User not found, behave like the old function (do nothing/return None)
                        logger.warning(f"User {username} not found in database.")
                        return

                    user_id = user_row[0]

                    # --- STEP 2 & 3: Find domains and Delete links ---
                    # We delete the links for this user, but we use 'RETURNING domain_id'
                    # so we know which domains we just unlinked (to check them in step 4).
                    cursor.execute("""
                        DELETE FROM aux_users_domains 
                        WHERE user_id = %s 
                        RETURNING domain_id
                    """, (user_id,))
                    
                    # Get a list of domain_ids that this user had
                    # fetchall returns tuples like [(1,), (5,)], so we flatten it to [1, 5]
                    user_domain_ids = [row[0] for row in cursor.fetchall()]

                    # --- STEP 4 & 5: Check for other users and Delete orphaned domains ---
                    for domain_id in user_domain_ids:
                        # Check if ANY other user is still linked to this domain
                        cursor.execute("""
                            SELECT 1 FROM aux_users_domains 
                            WHERE domain_id = %s LIMIT 1
                        """, (domain_id,))
                        
                        is_still_used = cursor.fetchone()

                        # If is_still_used is None, no one else is using this domain.
                        # We can safely delete it.
                        if not is_still_used:
                            cursor.execute("DELETE FROM domains WHERE id = %s", (domain_id,))

                    # --- STEP 6: Delete the user record ---
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    
                    # The transaction commits automatically here if no errors occurred

        except (Exception, psycopg2.Error) as e:
            # Matches the old error logging structure
            logger.error(f"Error deleting {username} and files from system: {str(e)}")
