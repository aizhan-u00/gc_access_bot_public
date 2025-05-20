"""
Module for configuring logging for the Telegram bot.

Initializes the 'access-bot' logger with output to 'access-bot.log' file and console.
Supports DEBUG (file) and INFO (console) logging levels with formatted output.
"""

import logging

# Create the logger
logger = logging.getLogger("access-bot")  # Set the logger name
logger.setLevel(logging.DEBUG)  # Logging level

# Log format
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Logging to file
file_handler = logging.FileHandler("access-bot.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Logging to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)
