from loguru import logger

logger.add(
    "logs/app_twitter_log.log",
    rotation="100 KB",
    level="INFO",
    # format="{time} {level} {message}",
    backtrace=True,
    diagnose=True,
)
