from datetime import timedelta
import json
import logging
from settings import Settings
from filelock import FileLock, Timeout
from azure.communication.identity import CommunicationIdentityClient, CommunicationUserIdentifier, CommunicationTokenScope

class UserStore:
    _instance = None
    _lock = FileLock("users.json.lock", timeout = 5)
    _filepath = "users.json"
    _all_users = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings):
        self._settings = settings
        self._identity_client = CommunicationIdentityClient.from_connection_string(settings.acs_connection_string)
        self.__load_users()

    def get_all(self):
        return self._all_users
    
    def delete(self, user_upn):
        user = self.get(user_upn)
        if user is not None:
            user_communication_identifier = CommunicationUserIdentifier(user['communication_id'])
            logging.info(f"Deleting user {user_upn}, id: {user_communication_identifier}")
            self._identity_client.delete_user(
                user_communication_identifier
            )
            self._all_users.remove(user)
            self.__dump_users()
            logging.info(f"User {user_upn} deleted")
        else:
            raise Exception(f"User {user_upn} not found")

    def get(self, user_upn):
        user = None
        users_matching = [u for u in self._all_users if u['upn'] == user_upn]
        if (len(users_matching) > 0):
            user = users_matching[0]
        logging.info(f"User {user_upn} found: {user}")

        return user

    def create(self, user_upn):
        user = self.get(user_upn)
        if (user is not None):
            raise Exception(f"User {user_upn} already exists")
        
        # Create user and token
        token_expires_in = timedelta(hours=24)
        identity_user, tokenresponse = self._identity_client.create_user_and_token(scopes=[CommunicationTokenScope.VOIP], token_expires_in=token_expires_in)
        logging.info("User created with id: " + identity_user.properties['id'])
        logging.info("Token issued with value: " + tokenresponse.token)
            
        user = [{
            "upn": user_upn,
            "communication_id": identity_user.properties['id'],
            "last_token": tokenresponse.token,
            "last_token_expires": tokenresponse.expires_on
        }]
        
        self.__add(user)
        return user

    def __load_users(self):
        try:
            with open(self._filepath) as f:
                self._all_users = json.load(f)
        except Exception as e:
            logging.error(f'Error: {e}')
            raise e
    
    def __add(self, new_user):
        logging.info(f"Adding user {new_user} to user store")
        self._all_users += new_user
        self.__dump_users()
        return new_user
    
    def __dump_users(self):
        try:
            self._lock.acquire()
            with open(self._filepath, "w") as f:
                json.dump(self._all_users, f)
        finally:
            self._lock.release()
        
        self.__load_users()