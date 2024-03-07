import logging
import os
from dapr.clients import DaprClient
from retry import retry

class Settings:
    def __init__(self, dapr_client : DaprClient):
        self.dapr_client = dapr_client

        # Dapr settings
        self.secret_store_name = self.__get_environment_variable("SECRET_STORE_NAME")
        self.acs_connection_string = self.__get_secret("COMMUNICATION_SERVICES_CONNECTION_STRING")
        self.callback_events_uri= self.__get_environment_variable("CALLBACK_EVENTS_URI")
        logging.info(f"""
<settings>
    secret_store_name:{self.secret_store_name}
    acs_connection_string:{self.acs_connection_string}
    callback_events_uri:{self.callback_events_uri}
</settings>""")
       
    def __get_environment_variable(self, variable_name, mandatory=True):
        variable = os.environ.get(variable_name)
        if not variable and mandatory:
            raise Exception(f"Environment variable {variable_name} is not set")
        return variable
    
    @retry(delay=1, backoff=2, max_delay=30)
    def __show_secrets(self):
        try:
            secret = self.dapr_client.get_bulk_secret(store_name=self.secret_store_name)
            logging.info('Result for bulk secret: ')
            logging.info(sorted(secret.secrets.items()))
        except Exception as e:
            raise e

    @retry(delay=1, backoff=2, max_delay=30)
    def __get_secret(self, secret_name):
        try:
            logging.log(logging.INFO, f"Getting secret {secret_name} from secret store {self.secret_store_name} ...")
            secret = self.dapr_client.get_secret(
                store_name=self.secret_store_name,
                key=secret_name
            )
            return secret.secret[secret_name]
        except Exception as e:
            raise e