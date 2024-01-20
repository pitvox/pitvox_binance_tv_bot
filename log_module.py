import logging
from config import *

class CustomLogger:
    def __init__(self, log_file_name):
        # Configure logging to log to a file
        logging.basicConfig(
            level=LOG_LEVEL,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format='%(asctime)s [%(levelname)s]: %(message)s',  # Define the log message format
            datefmt='%Y-%m-%d %H:%M:%S',  # Define the date/time format
            filename=log_file_name,  # Specify the file to which logs should be written
            filemode='a'  # Use 'w' to overwrite the file or 'a' to append to an existing file
        )

        # Create a logger instance
        self.logger = logging.getLogger()

    def log(self, level, message):
        print(message)
        # Log the message at the specified level
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'critical':
            self.logger.critical(message)