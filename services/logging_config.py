import logging, sys

def setup_logging(log_level):
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = setup_logging("DEBUG")  # Falls keine ENV gesetzt ist

# Create Logger
logger = logging.getLogger(__name__)

if LOG_LEVEL:
    if LOG_LEVEL == "ERROR":
        logger.setLevel(logging.ERROR)
    elif LOG_LEVEL == "WARNING":
        logger.setLevel(logging.WARNING)
    elif LOG_LEVEL == "INFO":
        logger.setLevel(logging.INFO)
    elif LOG_LEVEL == "DEBUG":
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.error("Log Level not set correctly. Please choose from ERROR, WARNING, INFO or DEBUG")
        stopServer()
else:
    if(DEBUG and DEBUG==True):
        logger.setLevel(logging.DEBUG)
        LOG_LEVEL = "DEBUG"
    else:
        logger.setLevel(logging.INFO)
        LOG_LEVEL = "INFO"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info(f"LogLevel is set to {LOG_LEVEL}")