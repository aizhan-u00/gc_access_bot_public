"""
Configuration module for the Telegram bot.

Contains settings such as bot token, API keys, messages, chat IDs, groups, and administrators.
Used for centralized management of bot parameters.
"""

# Basic URL for GetCourse API
BASE_GC_API = ""

# API key for GetCourse
GC_API_KEY = ""

# Setting wait time for GetCourse API
GC_WAIT_SECONDS = {'groups': 60, 'users': 10}

# Maximum number of retries for API requests
GC_MAX_RETRIES = 3

# Delay between retries (in seconds)
GC_RETRY_DELAY = 5

# Paths in responses from API GetCourse
FIELDS_PATH = "info.fields"
ITEMS_PATH = "info.items"
EXPORT_ID_PATH = "info.export_id"

# Fields in exports from GetCourse
FIELD_EMAIL = "Email"
FIELD_GROUP_ID = "id групп пользователя"


# Telegram bot token
BOT_TOKEN = ""

# Time of access check and message send
CHECK_TIME_HOUR = 4
CHECK_TIME_MIN = 0
SEND_TIME = "09:00"

# Messages to users
# Used in bot.py for sending responses to users.
# Keya (e.g., "hello") are used in code, values are message texts to be sent to users.
# Formatting: Markdown (*bold*, _italic_) to improve readability.
# Instructions for configurators:
# 1. Edit the message text while preserving the keys (e.g., "hello", "try2").
# 2. Do not delete or rename keys, otherwise the bot will not find the message.
# 3. After making changes, save the file and restart the bot or use the /update_config command.
# 4. Test changes by sending a test chat join request.
MESSAGES = {
    "hello": (
        "👋 Please send your email registered with GetCourse so we can verify your access."
    ),
    "try2": (
        "😔 It seems the entered email does not grant access to this chat. "
        "Try again with a different email."
    ),
    "is_access": (
        "🎉 Access confirmed! You have been added to the chat. Welcome!"
    ),
    "is_not_access": (
        "❌ Unfortunately, your email does not provide access to this chat. "
        "Check the email accuracy or contact support."
    ),
    "is_duplicate": (
        "⚠️ This email is already registered in one of our chats. "
        "Each email can only be used once."
    ),
    "is_end_access": (
        "⏰ Your access to the chat has expired. If you did not request a freeze and "
        "purchased the course less than a year ago, contact support for clarification."
    )
}

# Matching course groups with Telegram chats and GetCourse groups
# Format: {"group_name": {"chat_ids": [chat_id, ...], "gc_group_ids": [group_id, ...]}}
# - group_name: Group name - for configurator.
# - chat_ids: List of Telegram chat IDs associated with the group, mandatory with -100 at the beginning.
# - gc_group_ids: List of GetCourse group IDs granting access.
# Instructions for configurators:
# 1. Add new groups while preserving the structure.
# 2. Ensure that chat_ids and gc_group_ids are lists, even if they contain one element.
# 3. After making changes, use the /update_config command or restart the bot.
CHAT_IDS_GROUPS = {}

# IDs of administrators who can use the /update_config command
ADMIN_IDS = []
