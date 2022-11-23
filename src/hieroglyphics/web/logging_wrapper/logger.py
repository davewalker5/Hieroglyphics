import logging
import os.path
import socket
from platform import system
from tempfile import gettempdir
from os.path import dirname, join
from logging.handlers import RotatingFileHandler

LOGGER_NAME = "werkzeug"
HOSTNAME = socket.gethostname()
IP_ADDRESS = socket.gethostbyname(HOSTNAME)


def get_log_file_path(log_file_name):
    """
    Return the full path to the log file

    :param log_file_name: Name of the log file without the path
    :return: Full path to the log file
    """
    # Get the path to the log folder within the project
    project_folder = dirname(dirname(dirname(dirname(dirname(__file__)))))
    log_file_folder = join(project_folder, "logs")

    # If the above doesn't exist, use either "/tmp" (MacOS) or the temporary file
    # folder - the reason for this is that, on MacOS, gettempdir() returns a very
    # non-user-friendly path of the form /var/folders/4x/3xd5wtl93pggh7cltbd4nshm0000gn/T
    if not os.path.exists(log_file_folder):
        log_file_folder = "/tmp" if system().casefold() == "darwin" else gettempdir()

    return join(log_file_folder, log_file_name)


def configure_logger(log_file_name, log_file_max_size):
    """
    Reconfigure the Werkzeug logger to log to both file and the console and also to
    provide a consistent logging format from Werkzeug, Flask and the application to
    a single destination

    :param log_file_name: Name of the log file without the path
    :param log_file_max_size: Maximum size of the log file before it rolls
    """
    logger = logging.getLogger(LOGGER_NAME)

    # Remove the existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Create a common logging format for all handlers
    log_format = f"%(asctime)s {HOSTNAME} {IP_ADDRESS} %(process)s %(levelname)s - %(message)s"

    # Create a console handler and formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create a rotating log file handler
    log_file_path = get_log_file_path(log_file_name)
    file_handler = RotatingFileHandler(log_file_path, maxBytes=log_file_max_size, backupCount=0)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def get_logger():
    """
    Return the configured logger

    :return: Instance of the logger configured by the configuration method
    """
    return logging.getLogger(LOGGER_NAME)


def log_message(caller, message):
    """
    Log a message

    :param caller: Calling method name/endpoint name tag
    :param message: Message to log
    """
    get_logger().info(f"{caller} - {message}")
