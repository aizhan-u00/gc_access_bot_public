"""
Module for configuring logging for the Telegram bot.

Initializes the 'access-bot' logger with output to 'access-bot.log' file and console.
Supports DEBUG (file) and INFO (console) logging levels with formatted output.
"""

import logging

# Создаем логгер
logger = logging.getLogger("access-bot")  # Задаем имя логгера
logger.setLevel(logging.DEBUG)  # Уровень логирования

# Формат логов
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Логирование в файл
file_handler = logging.FileHandler("access-bot.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Логирование в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Добавляем обработчики
logger.addHandler(file_handler)
logger.addHandler(console_handler)
